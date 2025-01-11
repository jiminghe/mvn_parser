import argparse
import signal
import sys
import time
import logging
from typing import Any, Optional, Dict
from pathlib import Path
import json
from datetime import datetime
import os

from mvn_types import *
from mvn_exceptions import *
from mvn_receiver import MVNReceiver

class MVNApplication:
    """Main application for MVN data reception and processing"""
    
    def __init__(self, ip: str, port: int, 
                 output_dir: Optional[Path] = None,
                 save_data: bool = False,
                 log_level: str = "INFO"):
        """
        Initialize MVN application
        
        Args:
            ip: IP address to listen on
            port: Port number to listen on
            output_dir: Directory for saving data (optional)
            save_data: Whether to save received data to files
            log_level: Logging level
        """
        self.ip = ip
        self.port = port
        self.output_dir = output_dir
        self.save_data = save_data
        
        # Setup logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(log_level)
        
        # Initialize receiver with callback
        self.receiver = MVNReceiver(
            ip=ip,
            port=port,
            callback=self.handle_data
        )
        
        # State tracking
        self.running = False
        self.connected_characters: Dict[int, MetaData] = {}
        self.data_counters = {msg_type.value: 0 for msg_type in MessageType}
        
        # Data file handling
        self.current_session_file = None
        self.session_start_time = None
        if self.save_data and output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self._initialize_session_file()

        # Setup signal handling
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def _initialize_session_file(self):
        """Initialize new session file with metadata"""
        self.session_start_time = datetime.now()
        session_filename = f"mvn_session_{self.session_start_time.strftime('%Y%m%d_%H%M%S')}.jsonl"
        self.current_session_file = self.output_dir / session_filename

        # Write session header
        session_header = {
            "type": "session_info",
            "timestamp": self.session_start_time.isoformat(),
            "ip": self.ip,
            "port": self.port,
            "version": Version.STRING
        }
        self._append_to_session_file(session_header)
        
        self.logger.info(f"Initialized new session file: {self.current_session_file}")

    def _append_to_session_file(self, data: Dict):
        """Append data to current session file"""
        if not self.current_session_file:
            return

        try:
            with open(self.current_session_file, 'a') as f:
                json.dump(data, f)
                f.write('\n')
        except Exception as e:
            self.logger.error(f"Error writing to session file: {e}")

    def signal_handler(self, signum: int, frame: Any):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}")
        self.stop()
    
    def _handle_time_code(self, data: TimeCode, header: Optional[MVNHeader]):
        """Handle time code data"""
        if header:
            char_info = self.connected_characters.get(header.character_id, None)
            char_name = char_info.name if char_info else f"Character_{header.character_id}"
            
            self.logger.debug(
                f"Time code for {char_name}: {data.time_str} "
                f"({data.hours:02d}:{data.minutes:02d}:{data.seconds:02d})"
            )

    def handle_data(self, msg_type: str, data: Any, header: Optional[MVNHeader] = None):
        """
        Handle received MVN data
        
        Args:
            msg_type: Message type string
            data: Parsed data
            header: Optional MVN header information
        """
        try:
            # Update counters
            self.data_counters[msg_type] += 1
            
            # Process different message types
            if msg_type == MessageType.META_DATA.value:
                self._handle_meta_data(data, header)
            elif msg_type == MessageType.POSE_DATA_QUATERNION.value:
                self._handle_quaternion_pose(data, header)
            elif msg_type == MessageType.POSE_DATA_EULER.value:
                self._handle_euler_pose(data, header)
            elif msg_type == MessageType.CENTER_OF_MASS.value:
                self._handle_center_of_mass(data, header)
            elif msg_type == MessageType.JOINT_ANGLES.value:
                self._handle_joint_angles(data, header)
            elif msg_type == MessageType.TIME_CODE.value:
                self._handle_time_code(data, header)
            
            # Save data if enabled
            if self.save_data:
                self._save_data(msg_type, data, header)
                
        except Exception as e:
            self.logger.error(f"Error handling data: {e}")

    def _handle_meta_data(self, data: MetaData, header: Optional[MVNHeader]):
        """Handle character meta data"""
        if header:
            self.connected_characters[header.character_id] = data
            self.logger.info(f"Character connected - ID: {header.character_id}, Name: {data.name}")

    def _handle_quaternion_pose(self, data: Dict[str, Segment], header: Optional[MVNHeader]):
        """Handle quaternion pose data"""
        if header:
            char_info = self.connected_characters.get(header.character_id, None)
            char_name = char_info.name if char_info else f"Character_{header.character_id}"
            
            self.logger.debug(f"Quaternion pose data for {char_name}")
            for segment_name, segment in data.items():
                self.logger.debug(
                    f"  {segment_name}: "
                    f"pos({segment.position.x:.2f}, {segment.position.y:.2f}, {segment.position.z:.2f}), "
                    f"rot({segment.orientation.w:.2f}, {segment.orientation.x:.2f}, "
                    f"{segment.orientation.y:.2f}, {segment.orientation.z:.2f})"
                )

    def _handle_euler_pose(self, data: Dict[str, Segment], header: Optional[MVNHeader]):
        """Handle Euler pose data"""
        if header:
            char_info = self.connected_characters.get(header.character_id, None)
            char_name = char_info.name if char_info else f"Character_{header.character_id}"
            
            self.logger.debug(f"Euler pose data for {char_name}")
            for segment_name, segment in data.items():
                self.logger.debug(
                    f"  {segment_name}: "
                    f"pos({segment.position.x:.2f}, {segment.position.y:.2f}, {segment.position.z:.2f}), "
                    f"rot({segment.orientation.x:.2f}, {segment.orientation.y:.2f}, "
                    f"{segment.orientation.z:.2f})"
                )

    def _handle_center_of_mass(self, data: CenterOfMass, header: Optional[MVNHeader]):
        """Handle center of mass data"""
        if header:
            char_info = self.connected_characters.get(header.character_id, None)
            char_name = char_info.name if char_info else f"Character_{header.character_id}"
            
            self.logger.debug(
                f"Center of mass for {char_name}: "
                f"({data.position.x:.2f}, {data.position.y:.2f}, {data.position.z:.2f})"
            )

    def _handle_joint_angles(self, data: List[JointAngle], header: Optional[MVNHeader]):
        """Handle joint angle data"""
        if header:
            char_info = self.connected_characters.get(header.character_id, None)
            char_name = char_info.name if char_info else f"Character_{header.character_id}"
            
            self.logger.debug(f"Joint angles for {char_name}")
            for joint in data:
                self.logger.debug(
                    f"  Joint {joint.parent_point_id}->{joint.child_point_id}: "
                    f"({joint.rotation.x:.2f}, {joint.rotation.y:.2f}, {joint.rotation.z:.2f})"
                )

    def _save_data(self, msg_type: str, data: Any, header: Optional[MVNHeader]):
        """Save data to session file"""
        if not self.save_data or not self.current_session_file:
            return
            
        try:
            # Create frame data structure
            frame_data = {
                "type": "frame",
                "timestamp": datetime.now().isoformat(),
                "message_type": msg_type,
                "header": self._convert_to_dict(header) if header else None,
                "data": self._convert_to_dict(data)
            }
            
            # Append to session file
            self._append_to_session_file(frame_data)
                
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")

    def _convert_to_dict(self, obj: Any) -> Any:
        """Convert object to JSON-serializable dictionary"""
        if hasattr(obj, '__dict__'):
            return {k: self._convert_to_dict(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, dict):
            return {k: self._convert_to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_dict(x) for x in obj]
        elif isinstance(obj, tuple):
            return tuple(self._convert_to_dict(x) for x in obj)
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        else:
            return str(obj)

    def start(self):
        """Start the application"""
        try:
            self.running = True
            self.receiver.start()
            self.logger.info(f"Application started - listening on {self.ip}:{self.port}")
            
            while self.running:
                time.sleep(0.1)  # Prevent CPU overuse
                
        except MVNError as e:
            self.logger.error(f"MVN error: {e}")
            self.stop()
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            self.stop()

    def stop(self):
        """Stop the application"""
        self.running = False
        self.receiver.stop()
        
        # Write session summary before closing
        if self.save_data and self.current_session_file:
            summary = {
                "type": "session_summary",
                "timestamp": datetime.now().isoformat(),
                "session_duration": str(datetime.now() - self.session_start_time),
                "message_counts": self.data_counters,
                "connected_characters": {
                    str(char_id): self._convert_to_dict(meta_data)
                    for char_id, meta_data in self.connected_characters.items()
                }
            }
            self._append_to_session_file(summary)
        
        # Print statistics
        self.logger.info("Application stopped")
        self.logger.info("Data reception statistics:")
        for msg_type, count in self.data_counters.items():
            if count > 0:
                self.logger.info(f"  {msg_type}: {count} messages")
        
        self.logger.info("Connected characters:")
        for char_id, meta_data in self.connected_characters.items():
            self.logger.info(f"  ID {char_id}: {meta_data.name} ({meta_data.xmid})")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='MVN Network Receiver')
    parser.add_argument('--ip', type=str, default='127.0.0.1',
                      help='IP address to listen on (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                      help=f'Port to listen on (default: {DEFAULT_PORT})')
    parser.add_argument('--output-dir', type=str,
                      help='Directory to save received data')
    parser.add_argument('--save-data', action='store_true',
                      help='Save received data to files')
    parser.add_argument('--log-level', type=str, default='INFO',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                      help='Logging level (default: INFO)')
    return parser.parse_args()

def main():
    """Main entry point"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting MVN receiver on {args.ip}:{args.port}")
    
    try:
        # Create and start application
        app = MVNApplication(
            ip=args.ip,
            port=args.port,
            output_dir=args.output_dir if args.save_data else None,
            save_data=args.save_data,
            log_level=args.log_level
        )
        app.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Application error: {e}")
    finally:
        logger.info("Shutting down")
        sys.exit(0)

if __name__ == "__main__":
    main()