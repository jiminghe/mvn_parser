class MVNError(Exception):
    """Base exception for all MVN-related errors"""
    def __init__(self, message: str, *args, **kwargs):
        self.message = message
        super().__init__(self.message, *args, **kwargs)

class MVNParseError(MVNError):
    """
    Exception raised for parsing errors in MVN data.
    
    This includes:
    - Invalid header format
    - Invalid message type
    - Incorrect data length
    - Data format mismatches
    - Invalid segment IDs
    - Invalid quaternion values
    - Scale information parsing errors
    """
    def __init__(self, message: str, data_type: str = None, position: int = None, *args, **kwargs):
        self.data_type = data_type
        self.position = position
        detailed_message = f"Parse error"
        if data_type:
            detailed_message += f" in {data_type}"
        if position is not None:
            detailed_message += f" at position {position}"
        detailed_message += f": {message}"
        super().__init__(detailed_message, *args, **kwargs)

class MVNNetworkError(MVNError):
    """
    Exception raised for network-related errors.
    
    This includes:
    - Connection failures
    - Socket binding errors
    - Datagram reception errors
    - Timeout errors
    - Multiple character conflicts
    - Packet sequence errors
    """
    def __init__(self, message: str, address: str = None, port: int = None, *args, **kwargs):
        self.address = address
        self.port = port
        detailed_message = f"Network error"
        if address and port:
            detailed_message += f" for {address}:{port}"
        detailed_message += f": {message}"
        super().__init__(detailed_message, *args, **kwargs)

class MVNDatagramError(MVNError):
    """
    Exception raised for datagram-specific errors.
    
    This includes:
    - Invalid datagram counter
    - Missing datagrams in sequence
    - Datagram size errors
    - Invalid payload size
    """
    def __init__(self, message: str, datagram_counter: int = None, 
                 sample_counter: int = None, *args, **kwargs):
        self.datagram_counter = datagram_counter
        self.sample_counter = sample_counter
        detailed_message = f"Datagram error"
        if datagram_counter is not None:
            detailed_message += f" (datagram {datagram_counter}"
            if sample_counter is not None:
                detailed_message += f", sample {sample_counter}"
            detailed_message += ")"
        detailed_message += f": {message}"
        super().__init__(detailed_message, *args, **kwargs)

class MVNProtocolError(MVNError):
    """
    Exception raised for protocol-specific errors.
    
    This includes:
    - Invalid message types
    - Unsupported protocols
    - Protocol version mismatches
    - Invalid coordinate system specifications
    """
    def __init__(self, message: str, protocol_type: str = None, *args, **kwargs):
        self.protocol_type = protocol_type
        detailed_message = f"Protocol error"
        if protocol_type:
            detailed_message += f" for {protocol_type}"
        detailed_message += f": {message}"
        super().__init__(detailed_message, *args, **kwargs)

class MVNSegmentError(MVNError):
    """
    Exception raised for segment-related errors.
    
    This includes:
    - Invalid segment IDs
    - Missing required segments
    - Invalid segment data
    - Finger tracking segment errors
    """
    def __init__(self, message: str, segment_id: int = None, 
                 segment_name: str = None, *args, **kwargs):
        self.segment_id = segment_id
        self.segment_name = segment_name
        detailed_message = f"Segment error"
        if segment_id is not None and segment_name:
            detailed_message += f" for segment {segment_name} (ID: {segment_id})"
        elif segment_id is not None:
            detailed_message += f" for segment ID {segment_id}"
        elif segment_name:
            detailed_message += f" for segment {segment_name}"
        detailed_message += f": {message}"
        super().__init__(detailed_message, *args, **kwargs)

