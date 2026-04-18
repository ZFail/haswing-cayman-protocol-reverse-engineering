# Haswing Cayman 55 GPS — Packet CRC Analysis Results

## 🎯 Conclusion: It's MAVLink v1 Protocol

Your Haswing Cayman 55 GPS trolling motor uses the **MAVLink v1** protocol over RS232.

The CRC is **CRC-16/X.25 (MCRF4XX)** with a **per-message-type CRC_EXTRA seed**, stored in **little-endian** byte order. **All 72 packets matched 100%.**

---

## Packet Structure (MAVLink v1)

```
Byte 0:     0xFE          — Start marker (MAVLink v1 magic)
Byte 1:     LEN           — Payload length (total packet = LEN + 8)
Byte 2:     SEQ           — Sequence number (0–255, wrapping)
Byte 3:     SYS_ID        — System ID (always 0x6E = 110 in your motor)
Byte 4:     COMP_ID       — Component ID (always 0x00)
Byte 5:     MSG_ID        — Message type ID
Bytes 6…:   PAYLOAD       — LEN bytes of message data
Last 2:     CRC_LO CRC_HI — CRC-16, little-endian
```

## CRC Algorithm

| Parameter | Value |
|-----------|-------|
| **Algorithm** | CRC-16/MCRF4XX (X.25) |
| **Polynomial** | 0x1021 |
| **Init Value** | 0xFFFF |
| **Reflect In** | Yes |
| **Reflect Out** | Yes |
| **XOR Out** | 0x0000 |
| **Byte Order** | Little-endian (low byte first) |
| **Data Range** | Bytes 1 through N-2 (LEN, SEQ, SYS, COMP, MSG, PAYLOAD) |
| **CRC_EXTRA** | Per-message seed byte appended to CRC input (see table below) |

### How to Calculate

```python
def crc_x25(data):
    crc = 0xFFFF
    for b in data:
        tmp = b ^ (crc & 0xFF)
        tmp ^= (tmp << 4) & 0xFF
        crc = (crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)
        crc &= 0xFFFF
    return crc

def compute_packet_crc(packet_bytes):
    """Compute CRC for a full MAVLink v1 packet."""
    msg_id = packet_bytes[5]
    crc_extra_map = {
        0x00: 50, 0x07: 119, 0x1A: 170,
        0x1B: 144, 0x1E: 39, 0x21: 104, 0x34: 141
    }
    data = packet_bytes[1:-2]              # LEN through end of payload
    crc = crc_x25(data)
    # Append CRC_EXTRA as additional byte
    extra = crc_extra_map[msg_id]
    tmp = extra ^ (crc & 0xFF)
    tmp ^= (tmp << 4) & 0xFF
    crc = (crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)
    crc &= 0xFFFF
    return crc  # Store as little-endian: low byte first, high byte second
```

## Message Types Decoded

| MSG ID | Name (MAVLink standard) | Payload Size | CRC_EXTRA | Packets | Match |
|--------|------------------------|-------------|-----------|---------|-------|
| `0x00` (0) | **HEARTBEAT** | 9 bytes | **50** | 10 | ✅ 100% |
| `0x07` (7) | *Custom / Haswing-specific* | 32 bytes | **119** | 10 | ✅ 100% |
| `0x1A` (26) | **SCALED_IMU** | 22 bytes | **170** | 10 | ✅ 100% |
| `0x1B` (27) | **RAW_IMU** | 26 bytes | **144** | 10 | ✅ 100% |
| `0x1E` (30) | **ATTITUDE** | 28 bytes | **39** | 11 | ✅ 100% |
| `0x21` (33) | **GLOBAL_POSITION_INT** | 28 bytes | **104** | 11 | ✅ 100% |
| `0x34` (52) | *Custom / Haswing-specific* | 15 bytes | **141** | 10 | ✅ 100% |

> [!NOTE]
> 5 of 7 message IDs match **standard MAVLink** message definitions exactly (including CRC_EXTRA and payload size). MSG IDs `0x07` and `0x34` appear to be **Haswing-proprietary** messages.

## Example Verification

Packet 1 (line 1 of packets.txt):
```
FE 1C AE 6E 00 21 0B 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 FC E4

CRC input:  1C AE 6E 00 21 0B 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00
            + CRC_EXTRA byte 0x68 (104, for MSG 0x21)
CRC result: 0xE4FC → stored as FC E4 (little-endian) ✅
```

## Additional Details

- **System ID `0x6E` (110)**: This is the motor's MAVLink system identifier
- **Component ID `0x00`**: Default component
- **Sequence counter**: Increments each packet (wraps at 255→0), visible in byte 2
- The **HSW_m4Cgo** string in MSG `0x07` packets is likely a device identifier
- MSG `0x21` (GLOBAL_POSITION_INT) likely carries **GPS position data**
- MSG `0x1E` (ATTITUDE) contains **orientation/heading** (roll, pitch, yaw)
- MSG `0x1A` (SCALED_IMU) contains **accelerometer/gyro/magnetometer** readings

## What You Can Do With This

1. **Parse all messages** using any MAVLink v1 library (pymavlink, etc.)
2. **Construct valid packets** to send commands to the motor
3. **Monitor GPS position, heading, and IMU data** in real-time
4. For custom MSG IDs (0x07, 0x34), you'll need to reverse-engineer the payload fields by correlating values with motor state changes
