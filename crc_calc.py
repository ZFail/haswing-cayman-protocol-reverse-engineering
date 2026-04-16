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