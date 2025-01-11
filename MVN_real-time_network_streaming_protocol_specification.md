## MVN real-time network streaming Protocol Specification




Xsens Technologies B.V.

phone: +31 (0)88 9736700

fax: +31 (0)88 9736701

e-mail:info@xsens.com

www.xsens.com

Xsens North America, Inc.




## Revisions

| Revision | Date | By | Changes |
| :---: | :---: | :---: | :---: |
| E | February 2012 | DOS | Updated for release MVN Analyze/Animate 3.3 |
| F | June 2013 | AOD | Updated for release MVN Analyze/Animate 3.5 |
| G | December 2013 | CMO | Updated for release MVN Analyze/Animate 3.5.2 |
| H | October 2014 | JMU | Updated for release MVN Analyze/Animate 4.0 (new HW + support for TCP protocol) |
| I | November 2014 | PVR | Indicate more clearly which data types are used by MotionBuilder, Maya and Unity3D |
| J | February 2015 | JMU | Updated for MVN Analyze/Animate 4.1: <br> Additional datagrams for expanded network streaming defined |
| K | November 2017 | HBE | Updated naming for MVN 2018 |
| L | April 2018 | EJO | Updated documentation for scale information |
| M | June 2018 | JKO | Updated Motion Tracker Kinematics |
| N | September 2018 | JMU | Added finger tracking and updated header |

© 2005-2018, Xsens Technologies B.V. All rights reserved. Information in this document is subject to change without notice. Xsens, MVN, MotionGrid, MTi, MTi-G, MTx, MTw and Awinda are registered trademarks or trademarks of Xsens Technologies B.V. and/or its parent, subsidiaries and/or affiliates in The Netherlands, the USA and/or other countries. All other trademarks are the property of their respective owners.



## Table of Contents

1 INTRODUCTION ..... 1
1.1 Perceived Usage ..... 1
1.1.1 Usage in real-time previsualization and simulation VR setups ..... 1
1.1.2 Network Streamer and Network monitor ..... 1
1.1.3 Usage in multi-person or other complex motion capture setups ..... 2
2 TRANSPORT MEDIUM ..... 3
2.1 Network Environment ..... 3
2.2 Network Protocol ..... 3
2.3 Default Port ..... 3
2.4 Datagram ..... 3
2.4.1 Header ..... 4
2.5 POSE DATA ..... 7
2.5.1 Data order ..... 7
2.5.2 Segment data Euler (type 01) ..... 7
2.5.3 Segment data quaternion (type 02) ..... 7
2.5.4 Point position data (type 03) ..... 8
2.5.5 Segment data Unity3D (type 05) ..... 8
2.5.6 Position ..... 9
2.5.7 Rotation (Euler) ..... 9
2.5.8 Rotation (Quaternion). ..... 9
2.5.9 Segment ID ..... 9
2.5.10 Point ID ..... 9
2.5.11 Float and integer values over the network ..... 9
2.5.12 String values over the network ..... 9
2.6 Character information ..... 10
2.6.1 Meta data (type 12) ..... 10
2.6.2 Scale information (type 13) ..... 10
2.7 AdDITIONAL Information ..... 11
2.7.1 Joint Angles (type 20) ..... 11
2.7.2 Linear Segment Kinematics (type 21) ..... 11
2.7.3 Angular Segment Kinematics (type 22) ..... 11
2.7.4 Motion Tracker Kinematics (type 23) ..... 12
2.7.5 Center of Mass (type 24) ..... 12
2.7.6 Time Code (type 25) ..... 12
3 DATA TYPES ..... 13
3.1 Segments ..... 13



## 1 Introduction

MVN Analyze/Animate, developed by Xsens, is a tool to capture and compute the 6DOF motion data of an inertial sensor-driven system. It allows the export of the data to third party applications such as Motion Builder, making the data available to drive rigged characters in e.g. animations. The data transfer to other applications is primarily file based when using MVN Analyze/Animate. With the XME API (SDK) there are many other options.

In many situations it is attractive to keep the ease of use of MVN Analyze/Animate, while receiving the motion capture data in real-time in another application, even on another PC possibly physically remote from the MVN system.

This document defines a network protocol specification for this purpose. It describes the transport medium, the given data and the datagrams to be sent and received over the network, as well as the control sequences the server and clients will use to communicate states and requests during the sessions. The network communication is mainly required to be fast/real-time, other quality criteria are secondary.

This document describes MVN Analyze/Animate Real-time Network Streaming. The streaming feature enables computers that run MVN Analyze/Animate to stream the captured data over a network to other client computers.

### 1.1 Perceived Usage

### 1.1.1 Usage in real-time previsualization and simulation VR setups

Many software packages (e.g. MotionBuilder) and experimental VR rigs use single computers to do specific processing and hardware interfacing tasks, such as driving motion platforms, real-time rendering to a screen, or interfacing with a motion capture device. In this scenario, a PC set up with MVN Analyze/Animate could service one (or more) motion captured persons. This requires immediate, regularly timed delivery of state (pose) packets. The UDP protocol is most suitable for this task because it delivers packets without congestion control and dropped packet checking. MVN Analyze/Animate realtime network streaming protocol is based on UDP and is specified in this document.

To support scenarios like this for usage with $3^{\text {rd }}$ party tools as a client application, Xsens has developed several plug-ins. MVN Analyze/Animate plug-ins are available for Autodesk Motion Builder, Autodesk Maya and Unity3D. These tools use protocols specified in this document to receive motion capture data in real-time.

The client side plug-ins for MotionBuilder and Maya can be requested and purchased separately at Xsens.
The Unity3D plug-in is available for free at: https://www.assetstore.unity3d.com/en/\#!/content/11338 (Version: 1.0 (Apr 25, 2014), Size: 1.6 MB, this requires Unity 4.0.1 or higher)

### 1.1.2 Network Streamer and Network monitor

To send motions from MVN Analyze/Animate, go to Options > Preferences > Miscellaneous > Network Streamer and choose the desired protocol. The motion can also be received by MVN Analyze/Animate go to File > open Network Monitor. The Network Monitor will also show the local axis for each segment. Also note that the red triangle in the origin is representing the x -axis.

### 1.1.3 Usage in multi-person or other complex motion capture setups

In roll-your-own motion capture setups, often additional data is captured. An example could be medical data, or data gloves. Another setup might capture multiple subjects at once. The TCP protocol would be most suitable for this task as this protocol guarantees that the data stream is completely sent, potentially at the expense of near real-time delivery. However UDP also suffices in a well-designed network setup as there will be nearly no, or very little, packet loss.

Advantages for motion capture setup builders include:

- Not necessary to interface with XME API (SDK).
- Processing CPU time required for inertial motion capture is done on a separate PC, freeing up resources for other processing;
- Calibration and real-time pre-viewing (e.g. for assessment of motion capture quality) can be done on the processing PC using MVN Analyze/Animate itself.




## 2 Transport Medium

### 2.1 Network Environment

The network environment will be assumed to be a local 100 Mbit Ethernet network, larger network topologies are not considered and can be covered by file transfer of the already given file export functionality or later extensions to the network protocol. Thus, few packet loss or data corruption during transfer is to be expected, as well as constant connectivity.

### 2.2 Network Protocol

Network communication uses a protocol stack, thus the streaming protocol will be implemented on top of a given set of protocols already available for the network clients. In this case, the layers to build upon are IP and UDP (or TCP, which is also supported). IP (Internet Protocol, RFC 791) is the network layer protocol used in Ethernet networks and defines the source and destination of the packets within the network. Upon this, UDP (User Datagram Protocol, RFC 768) is used to encapsulate the data. The UDP Protocol is unidirectional, and contrary to TCP (Transmission Control Protocol, RFC 793) it is stateless and does not require the receiver to answer incoming packets. This allows greater speed.

### 2.3 Default Port

The default Port to be used on the network is 9763 . This Port is derived from the XME API $(9=X, M=6$, $\mathrm{E}=3$ ). MVN Analyze/Animate server will default to this Port.

It is of course possible to define an arbitrary Port if needed.

### 2.4 Datagram

The motion capture data is sampled and sent at regular time intervals for which the length depends upon the configuration of MVN Analyze/Animate. Common sampling rates lie between 60 and 240 Hertz. The update rate of the real-time network stream can be modified separately. The data content in the datagram is defined by the specific protocol set, but basically, the positions and rotation of all segments of the body at a sampling instance are sent away as one or more UDP datagrams.

Each datagram starts with a 24-byte header followed by a variable number of bytes for each body segment, depending on the selected data protocol. All data is sent in 'network byte order', which corresponds to big-endian notation.

Framed text indicates items that are sent as part of the datagram.



### 2.4.1 Header

The header contains the type of the data and some identification information, so the receiving end can apply it to the right target.

## Datagram header

```
6 bytes ID String
4 bytes sample counter
1 byte datagram counter
1 byte number of items
4 bytes time code
1 byte character ID
1 byte number of body segments - from MVN 2019
1 byte number of props - from MVN 2019
1 byte number of finger tracking data segments - from MVN }201
2 bytes reserved for future use
2 bytes size of payload
```


### 2.4.1.1 ID String

The ID String is an ASCII string which consists of 6 characters (not terminated by a null character). It serves to unambiguously identify the UDP datagram as containing motion data of the format according to this specification. Since the values in the string are characters, this string is not converted to a bigendian notation, but the first byte is simply the first character, etc.

These are the ASCII and hexadecimal byte values of the ID String:

| ASCII | M | X | T | P | 0 | 1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Hex | 4 D | 58 | 54 | 50 | 30 | 31 |

[^0]\#\#: Message type. The first digit determines what kind of packet this is and the second digit determines the format of the data in the packet

| Message type | Description |
|--------------|-------------|
| 01 | Pose data (Euler) ← MotionBuilder +Maya |
|    | • Absolute position and orientation (Euler) of segments |
|    | • Y-Up, right-handed |
|    | • This type is used by the Motion Builder + Maya plug-in |
|    | • *Supported by MVN Analyze/Animate network monitor* |
| 02 | Pose data (Quaternion) ← MVN Analyze/Animate Network Monitor |
|    | • Absolute position and orientation (Quaternion) of segments |
|    | • Default mode Z-Up, right-handed or Y-Up |
|    | • *Supported by MVN Analyze/Animate network monitor* |
| 03 | Pose data (Positions only, MVN Optical marker set 1) |
|    | • Positions of selected defined points (simulating optical markers), typically 38-46 points. Multiple data sets are available. |
|    | • This datagram is used by the Motion Builder plug-in v1.0. |
|    | • *Partially supported by MVN Analyze/Animate network monitor.* |
|    |   MVN Analyze/Animate has a limited ability to re-integrate these marker positions into a character. The segment orientations will not be updated. Therefore, when only this datagram is received, the resulting character can appear incorrect. |
| 04 | Deprecated: MotionGrid Tag data |
| 05 | Pose data (Unity3D) |
|    | • Relative position and orientation (Quaternion) of segments |
|    | • Uses alternative segment order |
|    | • Left-handed for Unity3D protocol |
|    | • *Supported by MVN Analyze/Animate network monitor* |
| 10 | Deprecated, use 13: Character information → scale information |
| 11 | Deprecated, use 13: Character information → prop information |
| 12 | Character information → meta data |
|    | • Name of the character |
|    | • MVN character ID (BodyPack or Awinda Station ID) |
|    | • << more can be added later >> |
|    | • *Supported by MVN Analyze/Animate network monitor* |
| 13 | Character information → scaling information, including prop and null-pose |
|    | *Supported by MVN Analyze/Animate network monitor* |
| 20 | Joint Angle data |
|    | • Joint definition and angles |
|    | • *NOT supported by MVN Analyze/Animate network monitor* |
| 21 | Linear Segment Kinematics |
|    | • Absolute segment position, velocity and acceleration |
|    | • *Partially supported by MVN Analyze/Animate network monitor.* |
|    |   MVN Analyze/Animate has a limited ability to re-integrate this data into a character. The segment orientations will not be updated. Therefore, when only this datagram is received, the resulting character can appear incorrect. |
| 22 | Angular Segment Kinematics |
|    | • Absolute segment orientation, angular velocity and angular acceleration |
|    | • *Partially supported by MVN Analyze/Animate network monitor.* |
|    |   MVN Analyze/Animate has a limited ability to re-integrate this data into a character. The segment positions will not be updated. Therefore, when only this datagram is received, the resulting character can appear incorrect. |
| 23 | Motion Tracker Kinematics |
|    | • Absolute sensor orientation and free acceleration |
|    | • Sensor-local acceleration, angular velocity and magnetic field |
|    | • *NOT supported by MVN Analyze/Animate network monitor* |
| 24 | Center of Mass |
|    | • Absolute position of center of mass |
|    | • *NOT supported by MVN Analyze/Animate network monitor* |
| 25 | Time Code |
|    | • Time code string |
|    | • *NOT supported by MVN Analyze/Animate network monitor* |

Please note that the message type is sent as a string, not as a number, so message type " 03 " is sent as hex code `0x30 0x33`, not as `0x00 0x03`.

### 2.4.1.2 Sample Counter

The sample counter is a 32-bit unsigned integer value which is incremented by one, each time a new set of motion tracker data is sampled and sent away. Note that the sample counter is not to be interpreted as a time code, since the sender may skip frames.

### 2.4.1.3 Datagram Counter

The size of a UDP datagram is usually limited by the MTU (maximum transmission unit, approx. 1500 bytes) of the underlying Ethernet network. In nearly all cases the entire motion data that was collected at one sampling instance will fit into a single UDP datagram. However, if the amount of motion data becomes too large then the data is split up into several datagrams.

If motion data is split up into several datagrams then the datagrams receive index numbers starting at zero. The datagram counter is a 7 -bit unsigned integer value which stores this index number. The most significant bit of the datagram counter byte is used to signal that this datagram is the last one belonging to that sampling instance. For example, if motion data is split up into three datagrams then their datagram counters will have the values 0,1 and $0 x 82$ (hexadecimal). If all data fits into one UDP datagram (the usual case) then the datagram counter will be equal to 0x80 (hexadecimal).
The sample counter mentioned above can be used to identify which datagrams belong to the same sampling instance because they must all carry the same sample counter value but different datagram counters. This also means that the combination of sample counter and datagram counter values is unique for each UDP datagram containing (part of the) motion data.

NOTE: For practical purposes this will not be an issue with the MVN streaming protocol. If problems are encountered, check your MTU settings.

### 2.4.1.4 Number of items

The number of items is stored as an 8-bit unsigned integer value. This number indicates the number of segments or points that are contained in the packet. Note that this number is not necessarily equal to the total number of motion trackers that were captured at the sampling instance if the motion capture data was split up into several datagrams. This number may instead be used to verify that the entire UDP datagram has been fully received by calculating the expected size of the datagram and comparing it to the actual size of the datagram.

### 2.4.1.5 Time code

MVN Analyze/Animate contains a clock which starts running at the start of a recording. The clock measures the elapsed time in milliseconds. Whenever new captured data is sampled the current value of the clock is sampled as well and is stored inside the datagram(s) as a 32-bit unsigned integer value representing a time code.

### 2.4.1.6 Character ID

MVN Analyze/Animate supports multiple characters in one viewport. This byte specifies to which character the data belongs. In a single-character setup this value will always be 0 . In multi-character cases, they will usually be incremental. However, especially during live streaming, one of the characters may disconnect and stop sending data while others will continue, so the receiver should be able to handle this.
Each character will send its own full packet.

### 2.4.1.7 Number of body segments

This value contains the number of regular body segments of the character. In practice this value is always 23 . Note that when streaming something other than segment data, this value will still contain the number of body segments (23).

### 2.4.1.8 Number of props

This value contains the number of prop segments streamed with the character (0-4). Note that when streaming something other than segment data, this value will still contain the number of prop segments.

### 2.4.1.9 Number of finger tracking data segments

This value contains the number of finger tracking data segments streamed with the character, either 0 or 40 . The value is for both hands combined. Note that when streaming something other than segment data, this value will still contain the number of finger tracking data segments.

### 2.4.1.10 Reserved bytes for future use

The left-over bytes near the end of the datagram header are reserved for future versions of this protocol.

### 2.4.1.11 Payload size

The last 2 bytes contain the size of the payload, meaning the size of the datagram without the header. This value can be used when an unknown datagram is received to skip its contents in a reliable way.

### 2.5 Pose data

### 2.5.1 Data order

When receiving data, items are sent in this order, non-existent items are skipped:

- Normal body segments
- Props
- Left hand finger tracking data
- Right hand finger tracking data


### 2.5.2 Segment data Euler (type 01)

This protocol was originally developed and optimized for the MotionBuilder and Maya plug-in.
Information about each segment is sent as follows.
4 bytes segment ID See 2.5.9
4 bytes $x$-coordinate of segment position
4 bytes $y$-coordinate of segment position
4 bytes $z$-coordinate of segment position
4 bytes x rotation-coordinate of segment rotation
4 bytes y rotation-coordinate of segment rotation
4 bytes $z$ rotation -coordinate of segment rotation
Total: 28 bytes per segment
The coordinates use a Y-Up, right-handed coordinate system for Euler protocol.
See also 2.5.1 Data order.

### 2.5.3 Segment data quaternion (type 02)

This protocol reflects the internal format of MVN Analyze/Animate.

Information about each segment is sent as follows.

```
4 bytes segment ID See 2.5.9
4 bytes x-coordinate of segment position
4 bytes y-coordinate of segment position
4 bytes z-coordinate of segment position
4 bytes q1 rotation - segment rotation quaternion component 1 (re)
4 bytes q2 rotation - segment rotation quaternion component 1 (i)
4 bytes q3 rotation - segment rotation quaternion component 1 (j)
4 bytes q4 rotation - segment rotation quaternion component 1 (k)
```

Total: 32 bytes per segment
The coordinates use a Z-Up, right-handed coordinate system.

## See also 2.5.1 Data order.

### 2.5.4 Point position data (type 03)

Information about each point is sent as follows.
This data type is intended to emulate a Virtual (optical) Marker Set.

```
4 bytes point ID
this is 100x the segment ID + the point ID for a marker
this is the tagld for a tag
4 bytes x-coordinate of point position
4 bytes y-coordinate of point position
4 bytes z-coordinate of point position
Total: 16 bytes per point
The coordinates use a Y-Up, right-handed coordinate system.
```


### 2.5.5 Segment data Unity3D (type 05)

Information about each segment is sent as follows.

```
4 bytes segment ID See 2.5.9
4 bytes x-coordinate of segment position
4 bytes y-coordinate of segment position
4 bytes z-coordinate of segment position
4 bytes q1 rotation - segment rotation quaternion component 1 (re)
4 bytes q2 rotation - segment rotation quaternion component 1 (i)
4 bytes q3 rotation - segment rotation quaternion component 1 (j)
4 bytes q4 rotation - segment rotation quaternion component 1 (k)
```

Total: 32 bytes per segment.
The pelvis and prop segments use global positions and rotation, while the other segments only use local rotation and relative positions. Segments follow pelvis position based on the character model hierarchy within Unity3D.

Unity3D mode uses quaternion data, where the coordinates use a Y-Up, left-handed coordinate system.
A total of 23 segments will be sent. Props and finger tracking data are not supported.

### 2.5.6 Position

The position of a captured segment is always stored as a 3D vector composed of three 32-bit float values. The unit is cm .

### 2.5.7 Rotation (Euler)

The rotation of a captured segment in the Euler representation is always stored as a 3D vector composed of three 32-bit float values. The unit is degrees.

### 2.5.8 Rotation (Quaternion)

The rotation of a captured segment in the Quaternion representation is always stored as a 4D vector composed of four 32-bit float values. The quaternion is always normalized, but not necessarily positivedefinite.

### 2.5.9 Segment ID

The IDs of the segments are listed in paragraph 3.1. The segment ID is sent as a normal 4-byte integer.

### 2.5.10 Point ID

The ID of a point depends on the ID of the segment it is attached to and the local ID it has in the segment. These local IDs are documented in the MVN User Manual. The ID is sent as a 4-byte integer, defined as 256 * segment ID + local point ID.

## Example:

The Sacrum point on the Pelvis segment has local ID 13, and the Pelvis has ID 1, so the ID of the point is sent as $256 * 1+13=269$.

### 2.5.11 Float and integer values over the network

All integer values mentioned above are stored in big-endian byte order inside the UDP datagrams with the function htonl() into the network by MVN Analyze/Animate and ntohl() out in the client. In other words: the most significant byte (MSB) is stored first. This is the same byte order that is used for other Internet protocols, so standard conversion functions should be available on all computer systems.

### 2.5.12 String values over the network

Strings are utf-8 encoded. They are preceded by the size of the string as a 32-bit signed integer and NOT 0-terminated.



### 2.6 Character information

### 2.6.1 Meta data (type 12)

This packet contains some meta-data about the character. This is in a tagged format, each tag is formatted as "tagname:" and each tagline is terminated by a newline. Each value is a string that can be interpreted in its own way.
Defined tags are:
name: contains the name as displayed in MVN Analyze/Animate
xmid: contains the BodyPack/Awinda-station ID as shown in MVN Analyze/Animate
color: contains the color of the character as used in MVN Analyze/Animate, the format is hex RRGGBB
More tags may be added later, so any implementation should be able to skip unknown and unused tags. This packet may contain different tags each time to reduce network load. The order of the tags can vary from packet to packet.

### 2.6.2 Scale information (type 13)

This packet contains scaling information about the character.
The scaling information is provided as known key points of the character standing in a perfect/ideal Tpose, where all segment orientations are set to identity.

The data sent per item for each packet is:

```
4 bytes: segment count (S)
S times:
- string: name of segment
    - 3x4 bytes: x,y,z coordinates of the origin of the segment in global space
4 bytes: point count (P)
P times:
    - 2 bytes: segment ID of the point
    - 2 bytes: point ID of the point in this segment
    - string: name of the point
    -4 bytes: unsigned integer containing flags describing the point's characteristics
    - 3x4 bytes: x,y,z coordinates of the point relative to the segment origin in the null pose
```

Total: unknown

Typically multiple packets of this type are sent to provide the full scaling information.
The separation is done to allow successful communication on networks with typical packet size limitations.
The first packet in a sequence will contain just the segments and will set the point count to 0 .
Following this will be packets with the segment count set to 0 and the point count set to a non- 0 value. These packets will define a subset of the available points. At the time of writing there are about 123 points defined. Combining the information in the 'point' packets will give the full set of available points.

The coordinates use a Z-Up, right-handed coordinate system.

### 2.7 Additional Information

These datagrams provide additional data, but do not by themselves define a full pose.

### 2.7.1 Joint Angles (type 20)

Information about each joint is sent as follows.
4 bytes point ID of parent segment connection. See 2.5.10
4 bytes point ID of child segment connection. See 2.5.10
4 bytes floating point rotation around segment $x$-axis
4 bytes floating point rotation around segment $y$-axis
4 bytes floating point rotation around segment $z$-axis
Total: 20 bytes per segment
The coordinates use a Z-Up, right-handed coordinate system.

### 2.7.2 Linear Segment Kinematics (type 21)

Information about each segment is sent as follows.
4 bytes segment ID See 2.5.9
4 bytes $x$-coordinate of segment position
4 bytes $y$-coordinate of segment position
4 bytes z-coordinate of segment position
4 bytes x component of segment global velocity
4 bytes y component of segment global velocity
4 bytes z component of segment global velocity
4 bytes $x$ component of segment global acceleration
4 bytes y component of segment global acceleration
4 bytes z component of segment global acceleration
Total: 40 bytes per segment
The coordinates use a Z-Up, right-handed coordinate system.
See also 2.5.1 Data order.

### 2.7.3 Angular Segment Kinematics (type 22)

Information about each segment is sent as follows.

```
4 bytes segment ID See 2.5.9
4 bytes q1 rotation - segment rotation quaternion component 1 (re)
4 bytes q2 rotation - segment rotation quaternion component 1 (i)
4 bytes q3 rotation - segment rotation quaternion component 1 (j)
4 bytes q4 rotation - segment rotation quaternion component 1 (k)
4 bytes $x$ component of segment global angular velocity
4 bytes y component of segment global angular velocity
4 bytes $z$ component of segment global angular velocity
4 bytes x component of segment global angular acceleration
4 bytes y component of segment global angular acceleration
4 bytes z component of segment global angular acceleration
```


## Total: 44 bytes per segment

The coordinates use a Z-Up, right-handed coordinate system.
See also 2.5.1 Data order.

### 2.7.4 Motion Tracker Kinematics (type 23)

Information about each motion tracker is sent as follows.
4 bytes segment ID to which the tracker is attached See 2.5.9
4 bytes q1 rotation - segment rotation quaternion component 1 (re)
4 bytes q2 rotation - segment rotation quaternion component 1 (i)
4 bytes q3 rotation - segment rotation quaternion component 1 (j)
4 bytes q4 rotation - segment rotation quaternion component $1(k)$
4 bytes $x$-coordinate of tracker global free acceleration
4 bytes $y$-coordinate of tracker global free acceleration
4 bytes z-coordinate of tracker global free acceleration
4 bytes x component of segment local magnetic field
4 bytes y component of segment local magnetic field
4 bytes z component of segment local magnetic field
Total: 44 bytes per segment.
Only data for segments with a tracker is sent. So it's important to check the segment ID for this datagram.
The coordinates use a Z-Up, right-handed coordinate system.

### 2.7.5 Center of Mass (type 24)

Information about the center of mass is sent as follows.

```
4 \text { bytes x-coordinate of center of mass position}
4 bytes y-coordinate of center of mass position
4 bytes z-coordinate of center of mass position
```

Total: 12 bytes
The coordinates use a Z-Up, right-handed coordinate system.

### 2.7.6 Time Code (type 25)

Information about time code is sent as follows.
12 byte string formatted as such HH:MM:SS.mmm
Total: 12 bytes

## 3 Data Types

### 3.1 Segments

Segments are internally addressed by a 0-based index. In some cases they are referred to by ID, which by definition is the index +1 .

Table 1: Euler and Quaternion protocols

| Segment Name | Segment Index |
| :--- | :---: |
| Pelvis | $\mathbf{0}$ |
| L5 | $\mathbf{1}$ |
| L3 | $\mathbf{2}$ |
| T12 | $\mathbf{3}$ |
| T8 | $\mathbf{4}$ |
| Neck | $\mathbf{5}$ |
| Head | $\mathbf{6}$ |
| Right Shoulder | $\mathbf{7}$ |
| Right Upper Arm | $\mathbf{8}$ |
| Right Forearm | $\mathbf{9}$ |
| Right Hand | 10 |
| Left Shoulder | 11 |
| Left Upper Arm | 12 |
| Left Forearm | 13 |
| Left Hand | 14 |
| Right Upper Leg | $\mathbf{1 5}$ |
| Right Lower Leg | $\mathbf{1 6}$ |
| Right Foot | $\mathbf{1 7}$ |
| Right Toe | 18 |
| Left Upper Leg | 19 |
| Left Lower Leg | 20 |
| Left Foot | 21 |
| Left Toe | 22 |
| Prop1 | $\mathbf{2 4}$ |
| Prop2 | $\mathbf{2 5}$ |
| Prop3 | $\mathbf{2 6}$ |
| Prop4 | $\mathbf{2 7}$ |
|  |  |



Table 2: Euler and Quaternion protocols finger tracking data additional segments

| Finger Tracking Segment Name | Left Hand Index | Right Hand Index |
| :---: | :---: | :---: |
| Carpus | 23 + Prop Count | 43 + Prop Count |
| First Metacarpal | Carpus + 1 | Carpus + 1 |
| First Proximal Phalange | Carpus + 2 | Carpus + 2 |
| First Distal Phalange | Carpus + 3 | Carpus + 3 |
| Second Metacarpal | Carpus + 4 | Carpus + 4 |
| Second Proximal Phalange | Carpus + 5 | Carpus + 5 |
| Second Middle Phalange | Carpus + 6 | Carpus + 6 |
| Second Distal Phalange | Carpus + 7 | Carpus + 7 |
| Third Metacarpal | Carpus + 8 | Carpus + 8 |
| Third Proximal Phalange | Carpus + 9 | Carpus + 9 |
| Third Middle Phalange | Carpus + 10 | Carpus + 10 |
| Third Distal Phalange | Carpus + 11 | Carpus + 11 |
| Fourth Metacarpal | Carpus + 12 | Carpus + 12 |
| Fourth Proximal Phalange | Carpus + 13 | Carpus + 13 |
| Fourth Middle Phalange | Carpus + 14 | Carpus + 14 |
| Fourth Distal Phalange | Carpus + 15 | Carpus + 15 |
| Fifth Metacarpal | Carpus + 16 | Carpus + 16 |
| Fifth Proximal Phalange | Carpus + 17 | Carpus + 17 |
| Fifth Middle Phalange | Carpus + 18 | Carpus + 18 |
| Fifth Distal Phalange | Carpus + 19 | Carpus + 19 |

Table 3: Unity3D protocol

| Segment Name | Segment Index |
| :--- | :---: |
| Pelvis | $\mathbf{0}$ |
| Right Upper Leg | $\mathbf{1}$ |
| Right Lower Leg | 2 |
| Right Foot | 3 |
| Right Toe | 4 |
| Left Upper Leg | 5 |
| Left Lower Leg | 6 |
| Left Foot | 7 |
| Left Toe | 8 |
| L5 | 9 |
| L3 | 10 |
| T12 | 11 |
| T8 | 12 |
| Left Shoulder | 13 |
| Left Upper Arm | 14 |
| Left Forearm | 15 |
| Left Hand | 16 |
| Right Shoulder | 17 |
| Right Upper Arm | 18 |
| Right Forearm | 19 |
| Right Hand | 20 |
| Neck | 21 |
| Head | 22 |
| Prop1-4 | $24-27$ |


[^0]:    M: M for MVN
    X: X for Xsens
    T: T for Transfer
    P: P for Protocol

