# Haswing Cayman 55 Protocol Analysis

**📘 Protocol Documentation: [Haswing-Motor-Control.md](./Haswing-Motor-Control.md)**

Packet dumps and scripts for reverse-engineering the communication protocol of the Haswing Cayman 55 outboard motor.

## Directory Structure

```
dumps/
├── rs232_mavlink_v1/    # Communication via USR-WIFI232-S module (MAVLink v1)
│   ├── to_motor/         # Packets from remote to motor
│   └── to_remote/        # Packets from motor to remote
├── rs485/                # RS-485 dumps (head ↔ bottom control board, 9600 baud)
└── usr_wifi232_s_config.txt  # USR-WIFI232-S module configuration session dump
```

## Hardware Notes

The USR-WIFI232-S module is located in the motor head. It handles wireless communication between the motor and the remote control (and phones — Android connects via the remote, iPhone likely works directly with the module).

From the config dump:

- Protocol: **UDP**, server mode
- Port: **14550**
- Motor sends data to IP **192.168.1.150** (DHCP-assigned when connecting to the motor's WiFi)
- WiFi SSID: varies per motor, e.g. **HSW_m4Cgo** (can view via wifi search)
- WiFi key: varies per motor, configurable via official app

The RS-232 bus runs at **115200 baud** between the USR-WIFI232-S module and motor head central processor.
The RS-485 bus runs at **9600 baud** between the motor head and the lower control board.

## Scripts

- `scripts/parse_pymavlink.py` — parse MAVLink v1 packets from a text dump using pymavlink, can be used to parse files from dumps/rs232_mavlink_v1 folder

## Setup

```bash
py -3 -m venv venv
./venv/Scripts/python.exe -m pip install -r requirements.txt
```

Usage:

```bash
./venv/Scripts/python.exe parse_pymavlink.py <packets.txt>
```
