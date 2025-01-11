# MVN Network Parser

A Python library for parsing and processing Xsens MVN motion capture real-time network streaming data. This library provides a robust implementation for receiving and parsing MVN network protocol messages, supporting various data formats including Euler angles, quaternions, joint angles, and more.

## Introduction

The MVN Network Parser is designed to handle real-time motion capture data streamed from Xsens MVN systems. It supports:

- Multiple data formats (Euler, Quaternion, Unity3D)
- Full body segment tracking
- Finger tracking
- Joint angles
- Center of mass
- Time code data
- Meta data and scaling information
- Split datagram handling
- Both synchronous and asynchronous operation

## Installation

### Requirements

- Python 3.8+
- No external dependencies required (uses standard library only)

### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/jiminghe/mvn_parser.git
cd mvn_parser
```

2. Install using pip (optional):
```bash
pip install .
```

## Usage

### Basic Usage

```python
from mvn_receiver import MVNReceiver

# Create a receiver instance
receiver = MVNReceiver(
    ip="127.0.0.1",
    port=9763,  # Default MVN streaming port
)

# Start receiving data
receiver.start()

# Get data synchronously
while True:
    data = receiver.get_data(timeout=1.0)
    if data:
        msg_type, parsed_data = data
        print(f"Received {msg_type} data")

# Stop receiving
receiver.stop()
```

### Using Callbacks

```python
def handle_data(msg_type, data):
    print(f"Received {msg_type} data:")
    print(data)

# Create receiver with callback
receiver = MVNReceiver(
    ip="127.0.0.1",
    port=9763,
    callback=handle_data
)

receiver.start()
```

### Using the Application Class

```python
from main import MVNApplication

# Create application instance
app = MVNApplication(
    ip="127.0.0.1",
    port=9763,
    output_dir="data",
    save_data=True,
    log_level="INFO"
)

# Start the application
app.start()
```

### Command Line Usage

```bash
python main.py --ip 127.0.0.1 --port 9763 --output-dir ./data --save-data --log-level INFO
```

## Configuration

### Network Settings

- `DEFAULT_PORT`: Default MVN streaming port (9763)
- `PROTOCOL_IDENTIFIER`: Protocol identifier bytes ('MXTP')

### Data Types

Configurable in `mvn_types.py`:
- Coordinate systems
- Units of measurement
- Segment definitions
- Protocol details
- Data validation ranges

### Receiver Settings

Configurable in `MVNReceiver`:
- Buffer size
- Queue size
- Socket timeout
- Datagram handling parameters

### Application Settings

Configurable in `MVNApplication`:
- Output directory
- Data saving options
- Logging levels
- Session file format

## Supported Message Types

- `POSE_DATA_EULER` (01): MotionBuilder + Maya format
- `POSE_DATA_QUATERNION` (02): MVN Analyze/Animate format
- `POSE_DATA_POINTS` (03): Position data only
- `POSE_DATA_UNITY3D` (05): Unity3D specific format
- `META_DATA` (12): Character meta data
- `SCALE_INFO` (13): Character scaling information
- `JOINT_ANGLES` (20): Joint angle data
- `LINEAR_SEGMENT_KIN` (21): Linear segment kinematics
- `ANGULAR_SEGMENT_KIN` (22): Angular segment kinematics
- `TRACKER_KIN` (23): Motion tracker kinematics
- `CENTER_OF_MASS` (24): Center of mass data
- `TIME_CODE` (25): Time code data

## Error Handling

The library provides specific exception classes for different types of errors:
- `MVNError`: Base exception class
- `MVNParseError`: Parsing-related errors
- `MVNNetworkError`: Network-related errors
- `MVNDatagramError`: Datagram-specific errors
- `MVNProtocolError`: Protocol-related errors
- `MVNSegmentError`: Segment-related errors

## Data Storage

When enabled, data is stored in JSONL format with:
- Session metadata
- Frame-by-frame data
- Character information
- Session statistics

## Reference Manual

For detailed information about the MVN network protocol and data formats, refer to:
- [Xsens MVN User Manual](https://www.movella.com/hubfs/MVN_User_Manual.pdf)
- [MVN real-time network streaming Protocol Specification](https://www.xsens.com/hubfs/Downloads/Manuals/MVN_real-time_network_streaming_protocol_specification.pdf)