from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Dict, Optional, Any
import struct
import logging
import re

# Network constants
DEFAULT_PORT = 9763  # Default port for MVN network streaming
PROTOCOL_IDENTIFIER = b'MXTP'  # Protocol identifier bytes

# Regular expressions
# TIME_CODE_PATTERN = re.compile(r'^\d{2}:\d{2}:\d{2}\.\d{3}$')
TIME_CODE_PATTERN = re.compile(r'^\d{2}:\d{2}:\d{2}(?:\.\d{3})?$')

# Type hints
SegmentIndex = int
PointID = int
SampleCounter = int
CharacterID = int

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IDString:
    """ID String byte values"""
    ASCII = "MXTP01"
    HEX = [0x4D, 0x58, 0x54, 0x50, 0x30, 0x31]  # M X T P 0 1
    
# Data type sizes in bytes
class DataSize:
    """Byte sizes for different data types"""
    HEADER = 24
    FLOAT = 4
    INT = 4
    SHORT = 2
    BYTE = 1
    QUATERNION = 16
    EULER = 12
    POSITION = 12
    SEGMENT_EULER = 28
    SEGMENT_QUATERNION = 32
    POINT = 16
    JOINT_ANGLE = 20
    LINEAR_KINEMATICS = 40
    ANGULAR_KINEMATICS = 44
    TRACKER_KINEMATICS = 44
    CENTER_OF_MASS = 12
    TIME_CODE = 12

@dataclass
class CoordinateSystemAxes:
    """Coordinate system axes definitions"""
    up_axis: str
    forward_axis: str
    handedness: str

COORDINATE_SYSTEMS = {
    "euler": CoordinateSystemAxes("Y", "Z", "right"),
    "quaternion": CoordinateSystemAxes("Z", "Y", "right"),
    "unity3d": CoordinateSystemAxes("Y", "Z", "left")
}

class Units:
    """Units of measurement"""
    POSITION = "centimeters"
    ROTATION = "degrees"  # For Euler angles
    VELOCITY = "meters/second"
    ACCELERATION = "meters/second²"
    ANGULAR_VELOCITY = "degrees/second"
    ANGULAR_ACCELERATION = "degrees/second²"
    MAGNETIC_FIELD = "arbitrary units"
    
class FingerTrackingOffset:
    """Finger segment index offsets"""
    LEFT_HAND_START = 27  # After props
    RIGHT_HAND_START = 47  # After left hand fingers
    FINGERS_PER_HAND = 20
    
class ProtocolDetails:
    """Protocol-specific details"""
    EULER_PROTOCOL = {
        "type": "01",
        "coordinate_system": "Y-Up, right-handed",
        "supported_by": ["MotionBuilder", "Maya"]
    }
    QUATERNION_PROTOCOL = {
        "type": "02",
        "coordinate_system": "Z-Up, right-handed",
        "supported_by": ["MVN Analyze/Animate Network Monitor"]
    }
    UNITY3D_PROTOCOL = {
        "type": "05",
        "coordinate_system": "Y-Up, left-handed",
        "supported_by": ["Unity3D"]
    }
    
class SegmentCounts:
    """Segment count constants"""
    BODY_SEGMENTS = 23
    MAX_PROPS = 4
    FINGERS_PER_HAND = 20
    TOTAL_FINGER_SEGMENTS = 40  # Both hands
    
class PointFlags:
    """Flags for point data"""
    CONTACT = 1 << 0
    FOOT_CONTACT = 1 << 1
    REJECTED = 1 << 2
    INTERPOLATED = 1 << 3
    
class Version:
    """Protocol version information"""
    MAJOR = 1
    MINOR = 0
    PATCH = 0
    STRING = f"{MAJOR}.{MINOR}.{PATCH}"
    
class MessageType(Enum):
    """Message types as defined in the MVN manual"""
    POSE_DATA_EULER = "01"         # MotionBuilder + Maya
    POSE_DATA_QUATERNION = "02"    # MVN Analyze/Animate Network Monitor
    POSE_DATA_POINTS = "03"        # Positions only, MVN Optical marker set
    DEPRECATED_MOTIONGRID = "04"   # Deprecated: MotionGrid Tag data
    POSE_DATA_UNITY3D = "05"       # Unity3D specific format
    DEPRECATED_INFO_10 = "10"      # Deprecated, use 13: Character scale info
    DEPRECATED_INFO_11 = "11"      # Deprecated, use 13: Prop info
    META_DATA = "12"               # Character meta data
    SCALE_INFO = "13"              # Character scaling information
    JOINT_ANGLES = "20"            # Joint angle data
    LINEAR_SEGMENT_KIN = "21"      # Linear segment kinematics
    ANGULAR_SEGMENT_KIN = "22"     # Angular segment kinematics
    TRACKER_KIN = "23"             # Motion tracker kinematics
    CENTER_OF_MASS = "24"          # Center of mass data
    TIME_CODE = "25"               # Time code data

@dataclass
class MVNHeader:
    """MVN datagram header structure"""
    id_string: str                 # 6 bytes ID string
    sample_counter: int            # 4 bytes sample counter
    datagram_counter: int          # 1 byte datagram counter
    num_items: int                 # 1 byte number of items
    time_code: int                 # 4 bytes time code
    character_id: int              # 1 byte character ID
    num_segments: int              # 1 byte number of body segments
    num_props: int                 # 1 byte number of props
    num_fingers: int               # 1 byte number of finger tracking segments
    payload_size: int              # 2 bytes size of payload

@dataclass
class Position:
    """3D position vector"""
    x: float
    y: float
    z: float

@dataclass
class Velocity:
    """3D velocity vector"""
    x: float
    y: float
    z: float

@dataclass
class Acceleration:
    """3D acceleration vector"""
    x: float
    y: float
    z: float

@dataclass
class Quaternion:
    """Quaternion rotation"""
    w: float  # Real component
    x: float  # i component
    y: float  # j component
    z: float  # k component

@dataclass
class Euler:
    """Euler angles rotation"""
    x: float  # Roll
    y: float  # Pitch
    z: float  # Yaw

@dataclass
class AngularVelocity:
    """Angular velocity vector"""
    x: float
    y: float
    z: float

@dataclass
class AngularAcceleration:
    """Angular acceleration vector"""
    x: float
    y: float
    z: float

@dataclass
class Segment:
    """Body segment data"""
    id: int
    position: Position
    orientation: Any  # Can be Euler or Quaternion

@dataclass
class Point:
    """Point position data"""
    id: int
    position: Position
    flags: int = 0  # Optional flags for point status

@dataclass
class JointAngle:
    """Joint angle data"""
    parent_point_id: int
    child_point_id: int
    rotation: Euler

@dataclass
class LinearKinematics:
    """Linear segment kinematics"""
    segment_id: int
    position: Position
    velocity: Velocity
    acceleration: Acceleration

@dataclass
class AngularKinematics:
    """Angular segment kinematics"""
    segment_id: int
    orientation: Quaternion
    angular_velocity: AngularVelocity
    angular_acceleration: AngularAcceleration


@dataclass
class TrackerID:
    """Tracker identification information"""
    id: int
    type: str = "unknown"
    location: str = "unknown"

    @staticmethod
    def from_raw_id(raw_id: int) -> 'TrackerID':
        """Create TrackerID from raw sensor ID"""
        return TrackerID(
            id=raw_id,
            type="MVN",  # You can add logic here to determine tracker type
            location="unknown"  # You can add logic here to determine location
        )

@dataclass
class TrackerKinematics:
    """Motion tracker kinematics"""
    segment_id: int
    tracker_id: Optional[TrackerID] = None
    orientation: Quaternion = field(default_factory=lambda: Quaternion(1.0, 0.0, 0.0, 0.0))
    free_acceleration: Acceleration = field(default_factory=lambda: Acceleration(0.0, 0.0, 0.0))
    magnetic_field: Position = field(default_factory=lambda: Position(0.0, 0.0, 0.0))
         
@dataclass
class CenterOfMass:
    """Center of mass data"""
    position: Position

@dataclass
class TimeCode:
    """
    Time code data
    Format: HH:MM:SS.mmm or HH:MM:SS (12 bytes max length)
    """
    time_str: str  # Format: HH:MM:SS.mmm or HH:MM:SS

    def __post_init__(self):
        """Add milliseconds if not present"""
        if '.' not in self.time_str:
            self.time_str = f"{self.time_str}.000"

    @property
    def hours(self) -> int:
        """Get hours component"""
        return int(self.time_str[0:2])
    
    @property
    def minutes(self) -> int:
        """Get minutes component"""
        return int(self.time_str[3:5])
    
    @property
    def seconds(self) -> int:
        """Get seconds component"""
        return int(self.time_str[6:8])
    
    @property
    def milliseconds(self) -> int:
        """Get milliseconds component"""
        if '.' in self.time_str:
            return int(self.time_str.split('.')[-1])
        return 0
    
    def __str__(self) -> str:
        return self.time_str

    def to_total_seconds(self) -> float:
        """Convert to total seconds including milliseconds"""
        return (self.hours * 3600 + 
                self.minutes * 60 + 
                self.seconds +
                self.milliseconds / 1000.0)

@dataclass
class MetaData:
    """Character meta data"""
    name: Optional[str] = None
    xmid: Optional[str] = None
    color: Optional[str] = None
    additional_tags: Dict[str, str] = field(default_factory=dict)
    
@dataclass
class ScaleInfo:
    """Character scale information"""
    segment_data: List[Tuple[str, Position]]  # (segment_name, origin_position)
    point_data: List[Tuple[int, int, str, int, Position]]  # (segment_id, point_id, name, flags, position)
    null_pose_data: Dict[str, Position] = field(default_factory=dict)  # Segment name -> position

class DataValidation:
    """Data validation ranges and limits"""
    MAX_SEGMENTS = 100
    MAX_POINTS = 1000
    MAX_DATAGRAM_SIZE = 65535
    MAX_PAYLOAD_SIZE = MAX_DATAGRAM_SIZE - DataSize.HEADER
    VALID_SAMPLE_RATE = [60, 100, 120, 240]  # Valid sampling rates in Hz
    MAX_PROPS = 4
    MAX_FINGER_SEGMENTS = 40
    MTU_SIZE = 1500  # Typical MTU size for Ethernet
    
class MetaDataTags:
    """Known metadata tags"""
    NAME = "name"
    XMID = "xmid"
    COLOR = "color"
    FORMAT = "tagname: value\n"  # Format specification
    
# Segment definitions for regular body segments
SEGMENT_NAMES = {
    0: "Pelvis",
    1: "L5",
    2: "L3",
    3: "T12",
    4: "T8",
    5: "Neck",
    6: "Head",
    7: "Right Shoulder",
    8: "Right Upper Arm",
    9: "Right Forearm",
    10: "Right Hand",
    11: "Left Shoulder",
    12: "Left Upper Arm",
    13: "Left Forearm",
    14: "Left Hand",
    15: "Right Upper Leg",
    16: "Right Lower Leg",
    17: "Right Foot",
    18: "Right Toe",
    19: "Left Upper Leg",
    20: "Left Lower Leg",
    21: "Left Foot",
    22: "Left Toe",
    # Props
    23: "Prop1",
    24: "Prop2",
    25: "Prop3",
    26: "Prop4",
    # Left Hand Fingers
    27: "Left Carpus",
    28: "Left First MC",
    29: "Left First PP",
    30: "Left First DP",
    31: "Left Second MC",
    32: "Left Second PP",
    33: "Left Second MP",
    34: "Left Second DP",
    35: "Left Third MC",
    36: "Left Third PP",
    37: "Left Third MP",
    38: "Left Third DP",
    39: "Left Fourth MC",
    40: "Left Fourth PP",
    41: "Left Fourth MP",
    42: "Left Fourth DP",
    43: "Left Fifth MC",
    44: "Left Fifth PP",
    45: "Left Fifth MP",
    46: "Left Fifth DP",
    # Right Hand Fingers
    47: "Right Carpus",
    48: "Right First MC",
    49: "Right First PP",
    50: "Right First DP",
    51: "Right Second MC",
    52: "Right Second PP",
    53: "Right Second MP",
    54: "Right Second DP",
    55: "Right Third MC",
    56: "Right Third PP",
    57: "Right Third MP",
    58: "Right Third DP",
    59: "Right Fourth MC",
    60: "Right Fourth PP",
    61: "Right Fourth MP",
    62: "Right Fourth DP",
    63: "Right Fifth MC",
    64: "Right Fifth PP",
    65: "Right Fifth MP",
    66: "Right Fifth DP"
}

# Unity3D specific segment order
UNITY3D_SEGMENT_NAMES = {
    0: "Pelvis",
    1: "Right Upper Leg",
    2: "Right Lower Leg",
    3: "Right Foot",
    4: "Right Toe",
    5: "Left Upper Leg",
    6: "Left Lower Leg",
    7: "Left Foot",
    8: "Left Toe",
    9: "L5",
    10: "L3",
    11: "T12",
    12: "T8",
    13: "Left Shoulder",
    14: "Left Upper Arm",
    15: "Left Forearm",
    16: "Left Hand",
    17: "Right Shoulder",
    18: "Right Upper Arm",
    19: "Right Forearm",
    20: "Right Hand",
    21: "Neck",
    22: "Head"
}

# Finger segment definitions
LEFT_FINGER_SEGMENTS = {
    0: "Left Carpus",
    1: "Left First Metacarpal",
    2: "Left First Proximal Phalange",
    3: "Left First Distal Phalange",
    4: "Left Second Metacarpal",
    5: "Left Second Proximal Phalange",
    6: "Left Second Middle Phalange",
    7: "Left Second Distal Phalange",
    8: "Left Third Metacarpal",
    9: "Left Third Proximal Phalange",
    10: "Left Third Middle Phalange",
    11: "Left Third Distal Phalange",
    12: "Left Fourth Metacarpal",
    13: "Left Fourth Proximal Phalange",
    14: "Left Fourth Middle Phalange",
    15: "Left Fourth Distal Phalange",
    16: "Left Fifth Metacarpal",
    17: "Left Fifth Proximal Phalange",
    18: "Left Fifth Middle Phalange",
    19: "Left Fifth Distal Phalange"
}

RIGHT_FINGER_SEGMENTS = {
    0: "Right Carpus",
    1: "Right First Metacarpal",
    2: "Right First Proximal Phalange",
    3: "Right First Distal Phalange",
    4: "Right Second Metacarpal",
    5: "Right Second Proximal Phalange",
    6: "Right Second Middle Phalange",
    7: "Right Second Distal Phalange",
    8: "Right Third Metacarpal",
    9: "Right Third Proximal Phalange",
    10: "Right Third Middle Phalange",
    11: "Right Third Distal Phalange",
    12: "Right Fourth Metacarpal",
    13: "Right Fourth Proximal Phalange",
    14: "Right Fourth Middle Phalange",
    15: "Right Fourth Distal Phalange",
    16: "Right Fifth Metacarpal",
    17: "Right Fifth Proximal Phalange",
    18: "Right Fifth Middle Phalange",
    19: "Right Fifth Distal Phalange"
}

# Constants for coordinate systems
class CoordinateSystem:
    """Coordinate system definitions"""
    EULER_Y_UP = "Y-Up, right-handed"      # For Euler protocol (type 01)
    QUATERNION_Z_UP = "Z-Up, right-handed"  # For Quaternion protocol (type 02)
    UNITY3D_Y_UP = "Y-Up, left-handed"     # For Unity3D protocol (type 05)

# Point ID calculation helper
def calculate_point_id(segment_id: int, local_point_id: int) -> int:
    """Calculate global point ID from segment ID and local point ID"""
    return 256 * segment_id + local_point_id

# Datagram counter helpers
def is_last_datagram(datagram_counter: int) -> bool:
    """Check if datagram is the last in sequence"""
    return bool(datagram_counter & 0x80)  # Check if most significant bit is set

def get_datagram_index(datagram_counter: int) -> int:
    """Get index of datagram in sequence"""
    return datagram_counter & 0x7F  # Get lower 7 bits

def validate_time_code(time_str: str) -> bool:
    """Validate time code string format"""
    # Check basic format
    if not TIME_CODE_PATTERN.match(time_str):
        return False
        
    try:
        # Parse components
        hours = int(time_str[0:2])
        minutes = int(time_str[3:5])
        seconds = int(time_str[6:8])
        
        # Validate ranges
        if not (0 <= hours <= 23 and 0 <= minutes <= 59 and 0 <= seconds <= 59):
            return False
            
        # If milliseconds present, validate them
        if '.' in time_str:
            milliseconds = int(time_str.split('.')[-1])
            if not (0 <= milliseconds <= 999):
                return False
                
        return True
        
    except (ValueError, IndexError):
        return False