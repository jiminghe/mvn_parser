import struct
import logging
from typing import Tuple, Dict, List, Any
from mvn_types import *
from mvn_exceptions import *
import re

class MVNParser:
    """Parser for MVN network protocol messages"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.segment_names = SEGMENT_NAMES
        self.unity3d_segment_names = UNITY3D_SEGMENT_NAMES
        self.left_finger_segments = LEFT_FINGER_SEGMENTS
        self.right_finger_segments = RIGHT_FINGER_SEGMENTS

    def _validate_data_length(self, data: bytes, required_length: int, 
                            data_type: str, offset: int = 0) -> None:
        """Validate that enough data is available"""
        if len(data) - offset < required_length:
            raise MVNParseError(
                f"Insufficient data length. Required: {required_length}, "
                f"Available: {len(data) - offset}",
                data_type=data_type,
                position=offset
            )

    def _unpack_string(self, data: bytes, offset: int) -> Tuple[str, int]:
        """Unpack a string preceded by its length"""
        try:
            str_size = struct.unpack('>I', data[offset:offset+4])[0]
            offset += 4
            string = data[offset:offset+str_size].decode('utf-8')
            offset += str_size
            return string, offset
        except struct.error as e:
            raise MVNParseError(
                f"Failed to unpack string size: {str(e)}",
                data_type="string",
                position=offset
            )
        except UnicodeDecodeError as e:
            raise MVNParseError(
                f"Failed to decode string: {str(e)}",
                data_type="string",
                position=offset
            )

    def parse_header(self, data: bytes) -> Tuple[MVNHeader, int]:
        """Parse MVN message header and return header object and bytes consumed"""
        try:
            self._validate_data_length(data, 24, "header")

            # Parse ID string
            id_string = data[0:6].decode('ascii')
            # print(f"ID string: {id_string}")
            if not id_string.startswith('MXTP'):
                raise MVNProtocolError(
                    f"Invalid header ID: {id_string}",
                    protocol_type="MVN"
                )

            # Parse remaining header fields
            sample_counter = struct.unpack('>I', data[6:10])[0]
            datagram_counter = data[10]
            num_items = data[11]
            time_code = struct.unpack('>I', data[12:16])[0]
            character_id = data[16]
            num_segments = data[17]
            num_props = data[18]
            num_fingers = data[19]
            payload_size = struct.unpack('>H', data[22:24])[0]

            # Create header object
            header = MVNHeader(
                id_string=id_string,
                sample_counter=sample_counter,
                datagram_counter=datagram_counter,
                num_items=num_items,
                time_code=time_code,
                character_id=character_id,
                num_segments=num_segments,
                num_props=num_props,
                num_fingers=num_fingers,
                payload_size=payload_size
            )

            # Basic validation
            if payload_size == 0:
                self.logger.debug(f"Zero payload size in header (type: {id_string[-2:]})")
            
            if num_items == 0:
                self.logger.debug(f"Zero items in header (type: {id_string[-2:]})")
            
            return header, 24

        except struct.error as e:
            raise MVNParseError(
                f"Failed to unpack header data: {str(e)}",
                data_type="header"
            )
        except UnicodeDecodeError as e:
            raise MVNParseError(
                f"Failed to decode header string: {str(e)}",
                data_type="header"
            )

    def _parse_position(self, data: bytes, offset: int) -> Tuple[Position, int]:
        """Parse position vector"""
        try:
            x, y, z = struct.unpack('>fff', data[offset:offset+12])
            return Position(x, y, z), offset + 12
        except struct.error as e:
            raise MVNParseError(
                f"Failed to unpack position data: {str(e)}",
                data_type="position",
                position=offset
            )

    def _parse_quaternion(self, data: bytes, offset: int) -> Tuple[Quaternion, int]:
        """Parse quaternion rotation"""
        try:
            w, x, y, z = struct.unpack('>ffff', data[offset:offset+16])
            return Quaternion(w, x, y, z), offset + 16
        except struct.error as e:
            raise MVNParseError(
                f"Failed to unpack quaternion data: {str(e)}",
                data_type="quaternion",
                position=offset
            )

    def _parse_euler(self, data: bytes, offset: int) -> Tuple[Euler, int]:
        """Parse Euler angles"""
        try:
            x, y, z = struct.unpack('>fff', data[offset:offset+12])
            return Euler(x, y, z), offset + 12
        except struct.error as e:
            raise MVNParseError(
                f"Failed to unpack Euler angles: {str(e)}",
                data_type="euler",
                position=offset
            )

    def parse_pose_euler(self, data: bytes, num_items: int) -> Dict[str, Segment]:
        """Parse type 01 pose data with Euler angles (Y-Up, right-handed)"""
        result = {}
        offset = 0
        bytes_per_segment = 28

        try:
            for i in range(num_items):
                self._validate_data_length(data, bytes_per_segment, "euler pose", offset)

                # Parse segment ID
                segment_id = struct.unpack('>I', data[offset:offset+4])[0]
                offset += 4

                # Check if it's a valid segment ID
                is_finger_segment = (
                    (segment_id >= 23 and segment_id < 43) or  # Left hand fingers
                    (segment_id >= 43 and segment_id < 63)     # Right hand fingers
                )
                
                if segment_id not in self.segment_names and not is_finger_segment:
                    raise MVNSegmentError(
                        "Invalid segment ID",
                        segment_id=segment_id
                    )

                # Parse position and rotation
                position, offset = self._parse_position(data, offset)
                rotation, offset = self._parse_euler(data, offset)
                
                segment = Segment(
                    id=segment_id,
                    position=position,
                    orientation=rotation
                )
                
                # Get segment name
                if segment_id in self.segment_names:
                    segment_name = self.segment_names[segment_id]
                elif is_finger_segment:
                    if segment_id >= 23 and segment_id < 43:
                        finger_idx = segment_id - 23
                        segment_name = self.left_finger_segments[finger_idx]
                    else:
                        finger_idx = segment_id - 43
                        segment_name = self.right_finger_segments[finger_idx]
                else:
                    segment_name = f"Unknown_Segment_{segment_id}"
                
                result[segment_name] = segment

            return result

        except struct.error as e:
            raise MVNParseError(
                f"Failed to parse Euler pose data: {str(e)}",
                data_type="euler pose",
                position=offset
            )

    def parse_pose_quaternion(self, data: bytes, num_items: int) -> Dict[str, Segment]:
        """Parse type 02 pose data with quaternions (Z-Up, right-handed)"""
        result = {}
        offset = 0
        bytes_per_segment = 32

        try:
            for i in range(num_items):
                self._validate_data_length(data, bytes_per_segment, "quaternion pose", offset)

                # Parse segment ID
                segment_id = struct.unpack('>I', data[offset:offset+4])[0]
                offset += 4

                # Check if it's a valid segment ID
                is_finger_segment = (
                    (segment_id >= 23 and segment_id < 43) or  # Left hand fingers
                    (segment_id >= 43 and segment_id < 63)     # Right hand fingers
                )
                
                if segment_id not in self.segment_names and not is_finger_segment:
                    raise MVNSegmentError(
                        "Invalid segment ID",
                        segment_id=segment_id
                    )

                # Parse position and quaternion
                position, offset = self._parse_position(data, offset)
                quaternion, offset = self._parse_quaternion(data, offset)
                
                segment = Segment(
                    id=segment_id,
                    position=position,
                    orientation=quaternion
                )
                
                # Get segment name
                if segment_id in self.segment_names:
                    segment_name = self.segment_names[segment_id]
                elif is_finger_segment:
                    if segment_id >= 23 and segment_id < 43:
                        finger_idx = segment_id - 23
                        segment_name = self.left_finger_segments[finger_idx]
                    else:
                        finger_idx = segment_id - 43
                        segment_name = self.right_finger_segments[finger_idx]
                else:
                    segment_name = f"Unknown_Segment_{segment_id}"
                
                result[segment_name] = segment

            return result

        except struct.error as e:
            raise MVNParseError(
                f"Failed to parse quaternion pose data: {str(e)}",
                data_type="quaternion pose",
                position=offset
            )


    def parse_point_data(self, data: bytes, num_items: int) -> Dict[int, Point]:
        """Parse type 03 point position data"""
        result = {}
        offset = 0
        bytes_per_point = 16

        try:
            for i in range(num_items):
                self._validate_data_length(data, bytes_per_point, "point data", offset)

                # Parse point ID
                point_id = struct.unpack('>I', data[offset:offset+4])[0]
                offset += 4

                # Parse position
                position, offset = self._parse_position(data, offset)
                
                point = Point(
                    id=point_id,
                    position=position
                )
                
                result[point_id] = point

            return result

        except struct.error as e:
            raise MVNParseError(
                f"Failed to parse point data: {str(e)}",
                data_type="point data",
                position=offset
            )

    def parse_unity3d_data(self, data: bytes, num_items: int) -> Dict[str, Segment]:
        """Parse type 05 Unity3D specific data (Y-Up, left-handed)"""
        result = {}
        offset = 0
        bytes_per_segment = 32

        try:
            for i in range(num_items):
                self._validate_data_length(data, bytes_per_segment, "Unity3D data", offset)

                # Parse segment ID
                segment_id = struct.unpack('>I', data[offset:offset+4])[0]
                if segment_id not in self.unity3d_segment_names:
                    raise MVNSegmentError(
                        "Invalid Unity3D segment ID",
                        segment_id=segment_id
                    )
                offset += 4

                # Parse position and quaternion
                position, offset = self._parse_position(data, offset)
                quaternion, offset = self._parse_quaternion(data, offset)
                
                segment = Segment(
                    id=segment_id,
                    position=position,
                    orientation=quaternion
                )
                
                result[self.unity3d_segment_names[segment_id]] = segment

            return result

        except struct.error as e:
            raise MVNParseError(
                f"Failed to parse Unity3D data: {str(e)}",
                data_type="Unity3D data",
                position=offset
            )

    def parse_meta_data(self, data: bytes) -> MetaData:
        """Parse type 12 meta data"""
        try:
            meta_data = MetaData()
            offset = 0
            
            while offset < len(data):
                # Read and parse each tag-value pair
                line, offset = self._unpack_string(data, offset)
                
                if ':' in line:
                    tag, value = line.strip().split(':', 1)
                    tag = tag.strip()
                    value = value.strip()
                    
                    # Handle known tags
                    if tag == 'name':
                        meta_data.name = value
                    elif tag == 'xmid':
                        meta_data.xmid = value
                    elif tag == 'color':
                        meta_data.color = value
                    else:
                        meta_data.additional_tags[tag] = value
                else:
                    self.logger.warning(f"Skipping invalid meta data line: {line}")
                    
            return meta_data

        except Exception as e:
            raise MVNParseError(
                f"Failed to parse meta data: {str(e)}",
                data_type="meta data"
            )
       
    def parse_scale_info(self, data: bytes) -> ScaleInfo:
        """Parse type 13 scale information"""
        try:
            offset = 0
            
            # Parse segment count
            self._validate_data_length(data, 4, "scale info", offset)
            segment_count = struct.unpack('>I', data[offset:offset+4])[0]
            offset += 4
            
            # Parse segments
            segments = []
            for _ in range(segment_count):
                # Read segment name
                name, offset = self._unpack_string(data, offset)
                
                # Read position
                self._validate_data_length(data, 12, "scale info segment", offset)
                position, offset = self._parse_position(data, offset)
                
                segments.append((name, position))
            
            # Parse point count
            self._validate_data_length(data, 4, "scale info points", offset)
            point_count = struct.unpack('>I', data[offset:offset+4])[0]
            offset += 4
            
            # Parse points
            points = []
            for _ in range(point_count):
                self._validate_data_length(data, 4, "scale info point", offset)
                segment_id = struct.unpack('>H', data[offset:offset+2])[0]
                point_id = struct.unpack('>H', data[offset+2:offset+4])[0]
                offset += 4
                
                # Read point name
                name, offset = self._unpack_string(data, offset)
                
                # Read flags and position
                self._validate_data_length(data, 16, "scale info point data", offset)
                flags = struct.unpack('>I', data[offset:offset+4])[0]
                offset += 4
                position, offset = self._parse_position(data, offset)
                
                points.append((segment_id, point_id, name, flags, position))
            
            return ScaleInfo(
                segment_data=segments,
                point_data=points
            )

        except Exception as e:
            if isinstance(e, MVNError):
                raise
            raise MVNParseError(
                f"Failed to parse scale information: {str(e)}",
                data_type="scale info"
            )

    def parse_joint_angles(self, data: bytes, num_items: int) -> List[JointAngle]:
        """Parse type 20 joint angle data"""
        result = []
        offset = 0
        bytes_per_joint = 20

        try:
            for i in range(num_items):
                self._validate_data_length(data, bytes_per_joint, "joint angles", offset)

                # Parse parent and child point IDs
                parent_id = struct.unpack('>I', data[offset:offset+4])[0]
                child_id = struct.unpack('>I', data[offset+4:offset+8])[0]
                offset += 8

                # Parse rotation
                rotation, offset = self._parse_euler(data, offset)
                
                joint = JointAngle(
                    parent_point_id=parent_id,
                    child_point_id=child_id,
                    rotation=rotation
                )
                
                result.append(joint)

            return result

        except struct.error as e:
            raise MVNParseError(
                f"Failed to parse joint angle data: {str(e)}",
                data_type="joint angles",
                position=offset
            )

    def parse_linear_kinematics(self, data: bytes, num_items: int) -> Dict[str, LinearKinematics]:
        """Parse type 21 linear segment kinematics"""
        result = {}
        offset = 0
        bytes_per_segment = 40

        try:
            for i in range(num_items):
                self._validate_data_length(data, bytes_per_segment, "linear kinematics", offset)

                # Parse segment ID
                segment_id = struct.unpack('>I', data[offset:offset+4])[0]
                if segment_id not in self.segment_names:
                    raise MVNSegmentError(
                        "Invalid segment ID",
                        segment_id=segment_id
                    )
                offset += 4

                # Parse position, velocity, and acceleration
                position, offset = self._parse_position(data, offset)
                velocity = Velocity(*struct.unpack('>fff', data[offset:offset+12]))
                offset += 12
                acceleration = Acceleration(*struct.unpack('>fff', data[offset:offset+12]))
                offset += 12
                
                kinematics = LinearKinematics(
                    segment_id=segment_id,
                    position=position,
                    velocity=velocity,
                    acceleration=acceleration
                )
                
                result[self.segment_names[segment_id]] = kinematics

            return result

        except struct.error as e:
            raise MVNParseError(
                f"Failed to parse linear kinematics data: {str(e)}",
                data_type="linear kinematics",
                position=offset
            )

    def parse_angular_kinematics(self, data: bytes, num_items: int) -> Dict[str, AngularKinematics]:
        """Parse type 22 angular segment kinematics"""
        result = {}
        offset = 0
        bytes_per_segment = 44

        try:
            for i in range(num_items):
                self._validate_data_length(data, bytes_per_segment, "angular kinematics", offset)

                # Parse segment ID
                segment_id = struct.unpack('>I', data[offset:offset+4])[0]
                if segment_id not in self.segment_names:
                    raise MVNSegmentError(
                        "Invalid segment ID",
                        segment_id=segment_id
                    )
                offset += 4

                # Parse orientation, angular velocity, and angular acceleration
                orientation, offset = self._parse_quaternion(data, offset)
                ang_vel = AngularVelocity(*struct.unpack('>fff', data[offset:offset+12]))
                offset += 12
                ang_acc = AngularAcceleration(*struct.unpack('>fff', data[offset:offset+12]))
                offset += 12
                
                kinematics = AngularKinematics(
                    segment_id=segment_id,
                    orientation=orientation,
                    angular_velocity=ang_vel,
                    angular_acceleration=ang_acc
                )
                
                result[self.segment_names[segment_id]] = kinematics

            return result

        except struct.error as e:
            raise MVNParseError(
                f"Failed to parse angular kinematics data: {str(e)}",
                data_type="angular kinematics",
                position=offset
            )

    def parse_tracker_kinematics(self, data: bytes, num_items: int) -> Dict[str, TrackerKinematics]:
        """Parse type 23 motion tracker kinematics"""
        result = {}
        offset = 0
        bytes_per_tracker = 44

        try:
            for i in range(num_items):
                self._validate_data_length(data, bytes_per_tracker, "tracker kinematics", offset)

                # Parse segment ID - for trackers, we accept any valid 32-bit ID
                segment_id = struct.unpack('>I', data[offset:offset+4])[0]
                offset += 4

                # Parse orientation, free acceleration, and magnetic field
                orientation, offset = self._parse_quaternion(data, offset)
                free_acc = Acceleration(*struct.unpack('>fff', data[offset:offset+12]))
                offset += 12
                magnetic = Position(*struct.unpack('>fff', data[offset:offset+12]))
                offset += 12
                
                kinematics = TrackerKinematics(
                    segment_id=segment_id,
                    orientation=orientation,
                    free_acceleration=free_acc,
                    magnetic_field=magnetic
                )
                
                # Use a generic name if segment ID doesn't map to known segment
                if segment_id in self.segment_names:
                    segment_name = self.segment_names[segment_id]
                else:
                    segment_name = f"Tracker_{segment_id}"
                
                result[segment_name] = kinematics
                
                self.logger.debug(
                    f"Parsed tracker kinematics for {segment_name} (ID: {segment_id}): "
                    f"orientation(w={orientation.w:.2f}, x={orientation.x:.2f}, "
                    f"y={orientation.y:.2f}, z={orientation.z:.2f})"
                )

            return result

        except struct.error as e:
            raise MVNParseError(
                f"Failed to parse tracker kinematics data: {str(e)}",
                data_type="tracker kinematics",
                position=offset
            )

    def parse_center_of_mass(self, data: bytes) -> CenterOfMass:
        """Parse type 24 center of mass data"""
        try:
            self._validate_data_length(data, 12, "center of mass")
            position, _ = self._parse_position(data, 0)
            return CenterOfMass(position=position)

        except struct.error as e:
            raise MVNParseError(
                f"Failed to parse center of mass data: {str(e)}",
                data_type="center of mass"
            )

    def parse_time_code(self, data: bytes) -> TimeCode:
        """
        Parse type 25 time code data
        Format: HH:MM:SS.mmm or HH:MM:SS
        """
        try:
            # Debug: print entire payload
            self.logger.debug(f"Time code complete payload: {' '.join(f'{b:02X}' for b in data)}")
            self.logger.debug(f"Payload length: {len(data)} bytes")
            
            # Look for actual time code data by searching for digits and colons
            time_code_bytes = None
            for i in range(len(data) - 7):  # Need at least 8 bytes for HH:MM:SS
                try:
                    segment = data[i:i+8].decode('ascii')
                    if re.match(r'\d{2}:\d{2}:\d{2}', segment):
                        time_code_bytes = data[i:]
                        break
                except:
                    continue
                    
            if time_code_bytes is None:
                raise MVNParseError(
                    "Could not find valid time code pattern in data",
                    data_type="time code"
                )
                
            self.logger.debug(f"Found time code bytes: {' '.join(f'{b:02X}' for b in time_code_bytes)}")
            
            # Try to decode the time string
            try:
                # Try first 12 bytes for full format (HH:MM:SS.mmm)
                if len(time_code_bytes) >= 12:
                    time_str = time_code_bytes[:12].decode('ascii').strip()
                    if validate_time_code(time_str):
                        return TimeCode(time_str=time_str)
                
                # Try 8 bytes for short format (HH:MM:SS)
                time_str = time_code_bytes[:8].decode('ascii').strip()
                if validate_time_code(time_str):
                    return TimeCode(time_str=time_str)
                    
            except UnicodeDecodeError as e:
                self.logger.debug(f"Decode error: {e}")
                
            # If we get here, we couldn't parse the time code
            raise MVNParseError(
                f"Could not parse time code from data: {' '.join(f'{b:02X}' for b in time_code_bytes)}",
                data_type="time code"
            )

        except Exception as e:
            if isinstance(e, MVNError):
                raise
            raise MVNParseError(
                f"Failed to parse time code: {str(e)}",
                data_type="time code"
            )

    def _parse_payload(self, msg_type: str, payload_data: bytes, header: MVNHeader) -> Any:
        """Parse payload based on message type"""
        try:
            if msg_type == MessageType.POSE_DATA_EULER.value:
                return self.parse_pose_euler(payload_data, header.num_items)
                
            elif msg_type == MessageType.POSE_DATA_QUATERNION.value:
                return self.parse_pose_quaternion(payload_data, header.num_items)
                
            elif msg_type == MessageType.POSE_DATA_POINTS.value:
                return self.parse_point_data(payload_data, header.num_items)
                
            elif msg_type == MessageType.POSE_DATA_UNITY3D.value:
                return self.parse_unity3d_data(payload_data, header.num_items)
                
            elif msg_type == MessageType.META_DATA.value:
                return self.parse_meta_data(payload_data)
                
            elif msg_type == MessageType.SCALE_INFO.value:
                return self.parse_scale_info(payload_data)
                
            elif msg_type == MessageType.JOINT_ANGLES.value:
                return self.parse_joint_angles(payload_data, header.num_items)
                
            elif msg_type == MessageType.LINEAR_SEGMENT_KIN.value:
                return self.parse_linear_kinematics(payload_data, header.num_items)
                
            elif msg_type == MessageType.ANGULAR_SEGMENT_KIN.value:
                return self.parse_angular_kinematics(payload_data, header.num_items)
                
            elif msg_type == MessageType.TRACKER_KIN.value:
                return self.parse_tracker_kinematics(payload_data, header.num_items)
                
            elif msg_type == MessageType.CENTER_OF_MASS.value:
                return self.parse_center_of_mass(payload_data)
                
            elif msg_type == MessageType.TIME_CODE.value:
                return self.parse_time_code(payload_data)
                
            else:
                raise MVNParseError(
                    f"Unknown message type: {msg_type}",
                    data_type=f"type_{msg_type}"
                )

        except MVNError:
            raise
        except Exception as e:
            raise MVNParseError(
                f"Failed to parse payload: {str(e)}",
                data_type=f"type_{msg_type}"
            )