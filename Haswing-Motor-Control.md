# Haswing Motor Communication Protocol

## Overview

Haswing motors support remote control via MAVLink v1 commands sent over UDP. This document describes the protocol for developers implementing third-party control software.

## Transport Layer

- **Protocol**: UDP
- **Default IP**: `192.168.1.1`
- **Default Port**: `14550`

## Message Format

All commands use the MAVLink 1.0 `COMMAND_LONG` message type.

### MAVLink COMMAND_LONG (v1)

| Field              | Value              | Description                      |
| ------------------ | ------------------ | -------------------------------- |
| `target_system`    | 0                  | Target system ID (0 = broadcast) |
| `target_component` | 0                  | Target component ID              |
| `command`          | See commands below | The command to execute           |
| `confirmation`     | 0                  | Confirmation flag                |
| `param1`           | 0                  | Not used                         |
| `param2`           | 0                  | Not used                         |
| `param3`           | 0                  | Not used                         |
| `param4`           | 0                  | Not used                         |
| `param5`           | 0                  | Not used                         |
| `param6`           | 0                  | Not used                         |
| `param7`           | 0                  | Not used                         |

## Commands

### Motor Control

| Command Name                        | ID  | Description             |
| ----------------------------------- | --- | ----------------------- |
| `HASWING_COMMAND_ROTATE_LEFT`       | 6   | Rotate motor left       |
| `HASWING_COMMAND_ROTATE_RIGHT`      | 7   | Rotate motor right      |
| `HASWING_COMMAND_THROTTLE_INCREASE` | 8   | Increase throttle speed |
| `HASWING_COMMAND_THROTTLE_DECREASE` | 9   | Decrease throttle speed |
| `HASWING_COMMAND_THROTTLE_ON`       | 10  | Enable throttle         |
| `HASWING_COMMAND_THROTTLE_OFF`      | 11  | Disable throttle        |

### Navigation

| Command Name                    | ID  | Description                     |
| ------------------------------- | --- | ------------------------------- |
| `HASWING_COMMAND_ANCHOR_START`  | 12  | Start anchor mode               |
| `HASWING_COMMAND_JOB_STOP`      | 13  | Stop current job/operation      |
| `HASWING_COMMAND_HEADING_START` | 14  | Drive in one selected direction |
| `HASWING_COMMAND_PATH_START`    | 15  | Start path navigation mode      |

## Example Implementation

### C (using MAVLink library)

```c
#include <mavlink.h>

void send_haswing_command(int sock, struct sockaddr_in *target,
                         uint16_t command) {
    mavlink_message_t msg;
    uint8_t buf[MAVLINK_MAX_PACKET_LEN];

    mavlink_msg_command_long_pack(0, 0, &msg,
                                  0,    // target_system
                                  0,    // target_component
                                  command,
                                  0,    // confirmation
                                  0, 0, 0, 0, 0, 0, 0);

    uint16_t len = mavlink_msg_to_send_buffer(buf, &msg);
    sendto(sock, buf, len, 0, (struct sockaddr *)target, sizeof(*target));
}
```

### Python

```python
import socket
import struct

MAVLINK_COMMAND_LONG = 76  # MAVLink message ID

def send_command(ip, port, command_id):
    """Send COMMAND_LONG to Haswing motor."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Using pymavlink recommended:
    # from pymavlink import mavutil
    # master = mavutil.mavlink_connection('udpin:0.0.0.0:14550')
    # master.mav.command_long_send(
    #     0, 0, mavutil.mavlink.MAV_CMD_..., 0, 0, 0, 0, 0, 0, 0, 0)

    sock.sendto(struct.pack('<BBHHHffffff',
        0, 0, MAVLINK_COMMAND_LONG, 0, 0, command_id,
        0, 0, 0, 0, 0, 0, 0), (ip, port))
    sock.close()
```

## Connection Notes

- Ensure UDP port is open on firewall
- Motor controller must be on the same network subnet
- Commands are sent as broadcast-ready packets
- No acknowledgment is returned for COMMAND_LONG messages
- Commands 12-15 may not be implemented on all firmware versions

## References

- [MAVLink Protocol Documentation](https://mavlink.io/en/)
- [MAVLink COMMAND_LONG Message](https://mavlink.io/en/messages/common.html#COMMAND_LONG)
