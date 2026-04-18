#!/usr/bin/env python3
"""
Brute-force CRC/checksum finder for Haswing Cayman 55 GPS trolling motor packets.

Packet structure observed:
  - Byte 0: FE (start marker)
  - Byte 1: payload length (number of bytes between byte 2 and the last 2 bytes)
  - Byte 2: sequence counter (increments each packet)
  - Byte 3: 6E (constant? system ID?)
  - Byte 4: 00 (constant?)
  - Byte 5: message type/ID
  - Bytes 6..N-2: payload data
  - Last 2 bytes: CRC/checksum (what we want to find)

We'll try many CRC-16 variants and simple checksum approaches.
"""

import re
import struct
import sys

# ---- Parse packets from the file ----
def parse_packets(filename):
    packets = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Extract hex bytes after the "->"
            match = re.search(r'->\s+((?:[0-9A-Fa-f]{2}\s)+)', line)
            if match:
                hex_str = match.group(1).strip()
                raw = bytes.fromhex(hex_str.replace(' ', ''))
                packets.append(raw)
    return packets

# ---- CRC-16 generic implementation ----
def crc16_generic(data, poly, init, ref_in, ref_out, xor_out):
    """Generic CRC-16 calculator."""
    crc = init
    for byte in data:
        if ref_in:
            byte = int('{:08b}'.format(byte)[::-1], 2)
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    if ref_out:
        crc = int('{:016b}'.format(crc)[::-1], 2)
    crc ^= xor_out
    return crc & 0xFFFF

def reflect_bits(value, width):
    result = 0
    for i in range(width):
        if value & (1 << i):
            result |= 1 << (width - 1 - i)
    return result

def crc16_reflected(data, poly, init, xor_out):
    """CRC-16 with reflected (LSB-first) processing."""
    # Reflect the polynomial
    rpoly = reflect_bits(poly, 16)
    crc = init
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ rpoly
            else:
                crc >>= 1
            crc &= 0xFFFF
    crc ^= xor_out
    return crc & 0xFFFF


# ---- Well-known CRC-16 parameterizations ----
CRC16_PARAMS = {
    # name: (poly, init, ref_in, ref_out, xor_out)
    'CRC-16/CCITT-FALSE':  (0x1021, 0xFFFF, False, False, 0x0000),
    'CRC-16/ARC':          (0x8005, 0x0000, True,  True,  0x0000),
    'CRC-16/AUG-CCITT':    (0x1021, 0x1D0F, False, False, 0x0000),
    'CRC-16/BUYPASS':      (0x8005, 0x0000, False, False, 0x0000),
    'CRC-16/CDMA2000':     (0xC867, 0xFFFF, False, False, 0x0000),
    'CRC-16/DDS-110':      (0x8005, 0x800D, False, False, 0x0000),
    'CRC-16/DECT-R':       (0x0589, 0x0000, False, False, 0x0001),
    'CRC-16/DECT-X':       (0x0589, 0x0000, False, False, 0x0000),
    'CRC-16/DNP':          (0x3D65, 0x0000, True,  True,  0xFFFF),
    'CRC-16/EN-13757':     (0x3D65, 0x0000, False, False, 0xFFFF),
    'CRC-16/GENIBUS':      (0x1021, 0xFFFF, False, False, 0xFFFF),
    'CRC-16/MAXIM':        (0x8005, 0x0000, True,  True,  0xFFFF),
    'CRC-16/MCRF4XX':      (0x1021, 0xFFFF, True,  True,  0x0000),
    'CRC-16/RIELLO':       (0x1021, 0xB2AA, True,  True,  0x0000),
    'CRC-16/T10-DIF':      (0x8BB7, 0x0000, False, False, 0x0000),
    'CRC-16/TELEDISK':     (0xA097, 0x0000, False, False, 0x0000),
    'CRC-16/TMS37157':     (0x1021, 0x89EC, True,  True,  0x0000),
    'CRC-16/USB':          (0x8005, 0xFFFF, True,  True,  0xFFFF),
    'CRC-16/A':            (0x1021, 0xC6C6, True,  True,  0x0000),
    'CRC-16/KERMIT':       (0x1021, 0x0000, True,  True,  0x0000),
    'CRC-16/MODBUS':       (0x8005, 0xFFFF, True,  True,  0x0000),
    'CRC-16/X-25':         (0x1021, 0xFFFF, True,  True,  0xFFFF),
    'CRC-16/XMODEM':       (0x1021, 0x0000, False, False, 0x0000),
    'CRC-16/IBM-3740':     (0x1021, 0xFFFF, False, False, 0x0000),  # same as CCITT-FALSE
    'CRC-16/OPENSAFETY-A': (0x5935, 0x0000, False, False, 0x0000),
    'CRC-16/OPENSAFETY-B': (0x755B, 0x0000, False, False, 0x0000),
    'CRC-16/PROFIBUS':     (0x1DCF, 0xFFFF, False, False, 0xFFFF),
    'CRC-16/LJ1200':       (0x6F63, 0x0000, False, False, 0x0000),
    'CRC-16/CMS':          (0x8005, 0xFFFF, False, False, 0x0000),
}

# ---- Simple checksum approaches ----
def checksum_sum8(data):
    """Simple 8-bit sum, return 16-bit."""
    return sum(data) & 0xFFFF

def checksum_sum16_be(data):
    """Sum of 16-bit big-endian words."""
    s = 0
    for i in range(0, len(data) - 1, 2):
        s += (data[i] << 8) | data[i+1]
    if len(data) % 2:
        s += data[-1] << 8
    return s & 0xFFFF

def checksum_sum16_le(data):
    """Sum of 16-bit little-endian words."""
    s = 0
    for i in range(0, len(data) - 1, 2):
        s += data[i] | (data[i+1] << 8)
    if len(data) % 2:
        s += data[-1]
    return s & 0xFFFF

def checksum_xor8(data):
    """XOR all bytes."""
    x = 0
    for b in data:
        x ^= b
    return x

def checksum_xor16_be(data):
    """XOR 16-bit big-endian words."""
    x = 0
    for i in range(0, len(data) - 1, 2):
        x ^= (data[i] << 8) | data[i+1]
    if len(data) % 2:
        x ^= data[-1] << 8
    return x

def checksum_xor16_le(data):
    """XOR 16-bit little-endian words."""
    x = 0
    for i in range(0, len(data) - 1, 2):
        x ^= data[i] | (data[i+1] << 8)
    if len(data) % 2:
        x ^= data[-1]
    return x

def checksum_fletcher16(data):
    """Fletcher-16 checksum."""
    s1 = 0
    s2 = 0
    for b in data:
        s1 = (s1 + b) % 255
        s2 = (s2 + s1) % 255
    return (s2 << 8) | s1

def checksum_neg_sum8(data):
    """Negative (two's complement) of 8-bit sum."""
    return (-sum(data)) & 0xFFFF

def checksum_neg_sum16_be(data):
    s = 0
    for i in range(0, len(data) - 1, 2):
        s += (data[i] << 8) | data[i+1]
    if len(data) % 2:
        s += data[-1] << 8
    return (-s) & 0xFFFF


# ---- MAVLink CRC (since packet looks MAVLink-like with FE header) ----
def crc_mavlink(data, crc_extra=None):
    """
    MAVLink v1 uses CRC-16/MCRF4XX (X.25) with an extra CRC_EXTRA byte
    appended based on message ID.
    """
    crc = 0xFFFF
    for b in data:
        tmp = b ^ (crc & 0xFF)
        tmp ^= (tmp << 4) & 0xFF
        crc = (crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)
        crc &= 0xFFFF
    if crc_extra is not None:
        tmp = crc_extra ^ (crc & 0xFF)
        tmp ^= (tmp << 4) & 0xFF
        crc = (crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)
        crc &= 0xFFFF
    return crc


def main():
    packets = parse_packets('packets.txt')
    print(f"Loaded {len(packets)} packets\n")

    # Show packet structure analysis
    print("=" * 70)
    print("PACKET STRUCTURE ANALYSIS")
    print("=" * 70)
    for i, pkt in enumerate(packets[:5]):
        print(f"\nPacket {i}: len={len(pkt)}")
        print(f"  Raw: {pkt.hex(' ')}")
        print(f"  Byte 0 (start):    0x{pkt[0]:02X}")
        print(f"  Byte 1 (length?):  0x{pkt[1]:02X} = {pkt[1]}")
        print(f"  Byte 2 (seq?):     0x{pkt[2]:02X} = {pkt[2]}")
        print(f"  Byte 3 (sysid?):   0x{pkt[3]:02X}")
        print(f"  Byte 4 (compid?):  0x{pkt[4]:02X}")
        print(f"  Byte 5 (msgid?):   0x{pkt[5]:02X}")
        print(f"  Payload ({pkt[1]} bytes): {pkt[6:-2].hex(' ')}")
        print(f"  Last 2 (CRC?):     {pkt[-2]:02X} {pkt[-1]:02X}  (BE: 0x{pkt[-2]:02X}{pkt[-1]:02X} = {(pkt[-2]<<8)|pkt[-1]}, LE: 0x{pkt[-1]:02X}{pkt[-2]:02X} = {pkt[-1]<<8|pkt[-2]})")
        expected_len = pkt[1] + 2 + 4  # payload_len + header(incl len byte itself?) + crc
        print(f"  Expected total (len+6): {pkt[1]+6}, actual: {len(pkt)}")

    # Verify length field interpretation
    print("\n" + "=" * 70)
    print("LENGTH FIELD VERIFICATION")
    print("=" * 70)
    for i, pkt in enumerate(packets[:10]):
        declared = pkt[1]
        actual = len(pkt)
        # MAVLink: total = 1(STX) + 1(LEN) + 1(SEQ) + 1(SYS) + 1(COMP) + 1(MSG) + LEN(payload) + 2(CRC) = LEN + 8
        interpretations = {
            'total = len + 8 (MAVLink v1)': declared + 8,
            'total = len + 6': declared + 6,
            'total = len + 4': declared + 4,
            'total = len + 2': declared + 2,
            'total = len': declared,
        }
        matches = [name for name, val in interpretations.items() if val == actual]
        print(f"  Pkt {i:2d}: declared_len=0x{declared:02X}={declared:3d}, actual_total={actual:3d}, match: {matches}")


    # ---- Try all CRC variants on different data ranges ----
    print("\n" + "=" * 70)
    print("CRC / CHECKSUM SEARCH")
    print("=" * 70)

    # Define different ranges of bytes to compute CRC over
    def get_data_ranges(pkt):
        """Return dict of range_name -> bytes to CRC."""
        ranges = {}
        ranges['bytes[1:-2] (len+seq+sys+comp+msg+payload)'] = pkt[1:-2]
        ranges['bytes[0:-2] (stx+len+seq+sys+comp+msg+payload)'] = pkt[0:-2]
        ranges['bytes[2:-2] (seq+sys+comp+msg+payload)'] = pkt[2:-2]
        ranges['bytes[3:-2] (sys+comp+msg+payload)'] = pkt[3:-2]
        ranges['bytes[5:-2] (msg+payload only)'] = pkt[5:-2]
        ranges['bytes[6:-2] (payload only)'] = pkt[6:-2]
        ranges['bytes[1:-2] excl stx (MAVLink style)'] = pkt[1:-2]  # same as first
        return ranges

    # Expected CRC value from packet (we'll check both byte orders)
    def get_expected(pkt):
        crc_be = (pkt[-2] << 8) | pkt[-1]
        crc_le = pkt[-2] | (pkt[-1] << 8)
        return crc_be, crc_le

    results = {}  # (algo, range, endian) -> match_count

    for pkt in packets:
        crc_be, crc_le = get_expected(pkt)

        for range_name, data in get_data_ranges(pkt).items():
            # Standard CRC-16 variants
            for crc_name, (poly, init, ref_in, ref_out, xor_out) in CRC16_PARAMS.items():
                computed = crc16_generic(data, poly, init, ref_in, ref_out, xor_out)
                for endian, expected in [('BE', crc_be), ('LE', crc_le)]:
                    key = (crc_name, range_name, endian)
                    if computed == expected:
                        results[key] = results.get(key, 0) + 1

            # Simple checksums
            for ck_name, ck_func in [
                ('SUM8', checksum_sum8),
                ('SUM16-BE', checksum_sum16_be),
                ('SUM16-LE', checksum_sum16_le),
                ('XOR8', checksum_xor8),
                ('XOR16-BE', checksum_xor16_be),
                ('XOR16-LE', checksum_xor16_le),
                ('FLETCHER16', checksum_fletcher16),
                ('NEG-SUM8', checksum_neg_sum8),
                ('NEG-SUM16-BE', checksum_neg_sum16_be),
            ]:
                computed = ck_func(data)
                for endian, expected in [('BE', crc_be), ('LE', crc_le)]:
                    key = (ck_name, range_name, endian)
                    if computed == expected:
                        results[key] = results.get(key, 0) + 1

    # Print results sorted by match count
    print("\nResults (showing algorithms that matched at least 1 packet):")
    print("-" * 70)
    sorted_results = sorted(results.items(), key=lambda x: -x[1])
    for (algo, rng, endian), count in sorted_results:
        pct = count / len(packets) * 100
        print(f"  {count:3d}/{len(packets)} ({pct:5.1f}%) | {algo:30s} | {rng:45s} | {endian}")

    # ---- MAVLink-specific test ----
    print("\n" + "=" * 70)
    print("MAVLINK CRC TEST (CRC EXTRA brute-force)")
    print("=" * 70)
    print("Testing MAVLink CRC (X.25) with CRC_EXTRA values 0-255...")
    print("Data range: bytes[1:-2] (standard MAVLink v1: LEN, SEQ, SYS, COMP, MSG, PAYLOAD)")

    # Group packets by message ID (byte 5)
    msg_groups = {}
    for pkt in packets:
        msg_id = pkt[5]
        if msg_id not in msg_groups:
            msg_groups[msg_id] = []
        msg_groups[msg_id].append(pkt)

    print(f"\nMessage IDs found: {[f'0x{mid:02X} ({len(pkts)} pkts)' for mid, pkts in sorted(msg_groups.items())]}")

    for msg_id, pkts in sorted(msg_groups.items()):
        print(f"\n  MSG ID 0x{msg_id:02X} ({len(pkts)} packets):")
        for crc_extra in range(256):
            match_count = 0
            for pkt in pkts:
                data = pkt[1:-2]  # MAVLink v1 CRC covers LEN, SEQ, SYS, COMP, MSG, PAYLOAD
                expected_le = pkt[-2] | (pkt[-1] << 8)  # MAVLink uses LE
                expected_be = (pkt[-2] << 8) | pkt[-1]
                computed = crc_mavlink(data, crc_extra)
                if computed == expected_le or computed == expected_be:
                    match_count += 1
            if match_count == len(pkts):
                endian = "LE" if (crc_mavlink(pkts[0][1:-2], crc_extra) == (pkts[0][-2] | (pkts[0][-1] << 8))) else "BE"
                print(f"    *** MATCH: CRC_EXTRA=0x{crc_extra:02X} ({crc_extra}) - ALL {len(pkts)} packets match ({endian})! ***")
            elif match_count > 0:
                print(f"    Partial: CRC_EXTRA=0x{crc_extra:02X} ({crc_extra}) - {match_count}/{len(pkts)} packets match")

    # ---- Also try without CRC_EXTRA ----
    print("\n" + "=" * 70)
    print("MAVLINK CRC WITHOUT CRC_EXTRA")
    print("=" * 70)
    for range_name_short, slicer in [
        ('bytes[1:-2]', lambda p: p[1:-2]),
        ('bytes[0:-2]', lambda p: p[0:-2]),
        ('bytes[2:-2]', lambda p: p[2:-2]),
    ]:
        match_count_le = 0
        match_count_be = 0
        for pkt in packets:
            data = slicer(pkt)
            computed = crc_mavlink(data, crc_extra=None)
            if computed == (pkt[-2] | (pkt[-1] << 8)):
                match_count_le += 1
            if computed == ((pkt[-2] << 8) | pkt[-1]):
                match_count_be += 1
        print(f"  {range_name_short}: LE matches={match_count_le}/{len(packets)}, BE matches={match_count_be}/{len(packets)}")

    print("\nDone!")


if __name__ == '__main__':
    main()
