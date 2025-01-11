import socket
import threading
import queue
import time
from typing import Optional, Callable, Any, Dict, Tuple
import logging
from mvn_types import *
from mvn_exceptions import *
from mvn_parser import MVNParser

class MVNReceiver:
    """
    MVN network receiver for handling real-time motion capture data.
    Supports both synchronous (queue-based) and asynchronous (callback-based) operation.
    """
    
    def __init__(self, ip: str, port: int, 
                 callback: Optional[Callable[[str, Any], None]] = None,
                 buffer_size: int = 65535,
                 queue_size: int = 1000,
                 socket_timeout: float = 1.0):
        """
        Initialize MVN receiver
        
        Args:
            ip: IP address to listen on
            port: Port number to listen on
            callback: Optional callback function to handle parsed data
            buffer_size: UDP receive buffer size (default: 65535)
            queue_size: Size of the data queue for non-callback operation
            socket_timeout: Socket timeout in seconds
        """
        self.ip = ip
        self.port = port
        self.callback = callback
        self.buffer_size = buffer_size
        self.socket_timeout = socket_timeout
        
        self.parser = MVNParser()
        self.running = False
        self.socket = None
        self.receive_thread = None
        self.data_queue = queue.Queue(maxsize=queue_size)
        
        # State tracking
        self.last_sample_counter = None
        self.partial_datagrams: Dict[int, list] = {}  # For handling split datagrams
        self.connected_characters: set = set()  # Track active characters
        self.partial_datagram_times = {}  # For tracking partial datagram timeouts
              
        self._setup_logging()
        


    def _setup_logging(self):
        """Configure logger for this instance"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.setLevel(logging.INFO)

    def start(self):
        """Start listening for MVN messages"""
        try:
            # Create and configure socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.buffer_size)
            self.socket.bind((self.ip, self.port))
            self.socket.settimeout(self.socket_timeout)
            
            # Start receive thread
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            self.logger.info(f"Started listening on {self.ip}:{self.port}")
            
        except socket.error as e:
            raise MVNNetworkError(
                f"Failed to initialize socket: {str(e)}",
                address=self.ip,
                port=self.port
            )
        except Exception as e:
            raise MVNNetworkError(
                f"Failed to start receiver: {str(e)}",
                address=self.ip,
                port=self.port
            )

    def stop(self):
        """Stop listening for messages and clean up resources"""
        self.running = False
        
        if self.socket:
            try:
                self.socket.close()
            except socket.error as e:
                self.logger.error(f"Error closing socket: {e}")
        
        if self.receive_thread:
            self.receive_thread.join(timeout=2.0)
            if self.receive_thread.is_alive():
                self.logger.warning("Receive thread did not terminate properly")
        
        self.clear_queue()
        self.partial_datagrams.clear()
        self.connected_characters.clear()
        self.logger.info("Stopped receiving")

    def _receive_loop(self):
        """Main receive loop"""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(self.buffer_size)
                self.logger.debug(f"Received {len(data)} bytes from {addr}")
                
                try:
                    # Parse header
                    header, bytes_consumed = self.parser.parse_header(data)
                    
                    # Track connected characters
                    self.connected_characters.add(header.character_id)
                    
                    # Check sample counter sequence
                    if self.last_sample_counter is not None:
                        if header.sample_counter < self.last_sample_counter:
                            # This might be normal when starting a new recording
                            self.logger.debug(f"New recording started: sample counter reset from {self.last_sample_counter} to {header.sample_counter}")
                        elif header.sample_counter > self.last_sample_counter + 1:
                            skipped = header.sample_counter - self.last_sample_counter - 1
                            self.logger.debug(f"Missed {skipped} samples")
                    self.last_sample_counter = header.sample_counter
                    
                    # Handle split datagrams
                    if not is_last_datagram(header.datagram_counter):
                        self._handle_partial_datagram(header, data[bytes_consumed:])
                        continue
                    
                    # Get complete payload
                    payload_data = self._get_complete_payload(header, data[bytes_consumed:])
                    
                    # Parse payload based on message type
                    msg_type = header.id_string[-2:]
                    parsed_data = self._parse_payload(msg_type, payload_data, header)
                    
                    # Handle the parsed data
                    if parsed_data is not None:
                        self._handle_parsed_data(msg_type, parsed_data, header)
                            
                except MVNError as e:
                    self.logger.error(f"MVN error processing datagram: {e}")
                    continue
                    
            except socket.timeout:
                continue
            except socket.error as e:
                self.logger.error(f"Socket error in receive loop: {e}")
                if not self.running:
                    break
                time.sleep(0.1)  # Prevent tight loop on persistent errors
            except Exception as e:
                self.logger.error(f"Unexpected error in receive loop: {e}")
                if not self.running:
                    break
                time.sleep(0.1)

    def _handle_partial_datagram(self, header: MVNHeader, payload: bytes):
        """Handle datagram that is part of a split message"""
        key = (header.sample_counter, header.character_id)
        datagram_index = get_datagram_index(header.datagram_counter)
        
        # Initialize storage for partial datagrams if needed
        if key not in self.partial_datagrams:
            # For new sequences, create a dynamic list
            self.partial_datagrams[key] = []
        
        # Extend list if needed
        while len(self.partial_datagrams[key]) <= datagram_index:
            self.partial_datagrams[key].append(None)
        
        # Store the payload
        self.partial_datagrams[key][datagram_index] = payload
        
        self.logger.debug(
            f"Stored partial datagram {datagram_index} for sample {header.sample_counter}, "
            f"character {header.character_id}"
        )

    def _get_complete_payload(self, header: MVNHeader, payload: bytes) -> bytes:
        """Get complete payload, combining split datagrams if necessary"""
        # Handle single datagram case
        if is_last_datagram(header.datagram_counter) and get_datagram_index(header.datagram_counter) == 0:
            if len(payload) < header.payload_size:
                raise MVNDatagramError(
                    f"Payload size mismatch. Expected: {header.payload_size}, Got: {len(payload)}",
                    datagram_counter=header.datagram_counter,
                    sample_counter=header.sample_counter
                )
            return payload
                
        key = (header.sample_counter, header.character_id)
        if key not in self.partial_datagrams:
            raise MVNDatagramError(
                "Missing partial datagrams",
                datagram_counter=header.datagram_counter,
                sample_counter=header.sample_counter
            )
                
        # Add final payload
        datagram_index = get_datagram_index(header.datagram_counter)
        while len(self.partial_datagrams[key]) <= datagram_index:
            self.partial_datagrams[key].append(None)
        self.partial_datagrams[key][datagram_index] = payload
        
        # Check if we have all parts up to this index
        if None in self.partial_datagrams[key][:datagram_index + 1]:
            raise MVNDatagramError(
                "Incomplete datagram sequence",
                datagram_counter=header.datagram_counter,
                sample_counter=header.sample_counter
            )
                
        # Combine payloads and cleanup
        complete_payload = b''.join(self.partial_datagrams[key])
        del self.partial_datagrams[key]
        
        # Validate complete payload size
        if len(complete_payload) < header.payload_size:
            raise MVNDatagramError(
                f"Combined payload size mismatch. Expected: {header.payload_size}, Got: {len(complete_payload)}",
                datagram_counter=header.datagram_counter,
                sample_counter=header.sample_counter
            )
        
        return complete_payload

    def _parse_payload(self, msg_type: str, payload_data: bytes, header: MVNHeader) -> Any:
        """Parse payload using appropriate parser method"""
        try:
            if len(payload_data) < header.payload_size:
                raise MVNParseError(
                    f"Payload size mismatch. Expected: {header.payload_size}, Got: {len(payload_data)}",
                    data_type=f"type_{msg_type}"
                )
            
            return self.parser._parse_payload(msg_type, payload_data, header)
            
        except MVNError:
            raise
        except Exception as e:
            raise MVNParseError(
                f"Failed to parse payload: {str(e)}",
                data_type=f"type_{msg_type}"
            )

    def _handle_parsed_data(self, msg_type: str, data: Any, header: MVNHeader):
        """Handle parsed data through callback or queue"""
        try:
            # Special handling for tracker kinematics
            if msg_type == MessageType.TRACKER_KIN.value:
                self.logger.debug(f"Received tracker kinematics data for {len(data)} trackers")
                for tracker_name, kinematics in data.items():
                    self.logger.debug(
                        f"Tracker {tracker_name}: "
                        f"orientation(w={kinematics.orientation.w:.2f}, "
                        f"x={kinematics.orientation.x:.2f}, "
                        f"y={kinematics.orientation.y:.2f}, "
                        f"z={kinematics.orientation.z:.2f})"
                    )

            if self.callback:
                self.callback(msg_type, data)
            else:
                if self.data_queue.full():
                    self.logger.warning("Data queue full, dropping oldest item")
                    try:
                        self.data_queue.get_nowait()
                    except queue.Empty:
                        pass
                self.data_queue.put((msg_type, data))
                
        except Exception as e:
            self.logger.error(f"Error handling parsed data: {e}")

    def get_data(self, timeout: float = 0.1) -> Optional[Tuple[str, Any]]:
        """
        Get parsed data from the queue
        
        Args:
            timeout: How long to wait for data (seconds)
            
        Returns:
            Tuple of (message_type, parsed_data) or None if queue is empty
        """
        try:
            return self.data_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def clear_queue(self):
        """Clear the data queue"""
        while not self.data_queue.empty():
            try:
                self.data_queue.get_nowait()
            except queue.Empty:
                break

    def get_connected_characters(self) -> set:
        """Get set of currently connected character IDs"""
        return self.connected_characters.copy()

    def get_queue_size(self) -> int:
        """Get current number of items in the data queue"""
        return self.data_queue.qsize()

    def is_running(self) -> bool:
        """Check if receiver is currently running"""
        return self.running and (self.receive_thread is not None and self.receive_thread.is_alive())
    
    def _cleanup_old_partial_datagrams(self):
        """Clean up old partial datagrams that were never completed"""
        current_time = time.time()
        keys_to_remove = []
        
        for key in self.partial_datagrams:
            if current_time - self.partial_datagram_times.get(key, 0) > 1.0:  # 1 second timeout
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.partial_datagrams[key]
            if key in self.partial_datagram_times:
                del self.partial_datagram_times[key]