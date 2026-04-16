#!/usr/bin/env python3
"""Use CRCBeagle to find CRC parameters from packets.txt."""

import re
import sys
sys.path.insert(0, '/tmp/crcbeagle')
from crcbeagle.crcbeagle import CRCBeagle

# Parse packets
with open('/home/user/crcfind/packets.txt') as f:
    content = f.read()

lines = re.split(r'(?=\d{2}:\d{2}:\d{2}\.\d+ ->)', content)

packets = []
for line in lines:
    line = line.strip()
    if not line:
        continue
    m = re.search(r'->\s+([0-9A-Fa-f ]+)\s+\[', line.replace('\n', ' '))
    if m:
        hex_bytes = m.group(1).split()
        pkt_bytes = [int(b, 16) for b in hex_bytes]
        packets.append(pkt_bytes)

# Group by length
from collections import defaultdict
groups = defaultdict(list)
for pkt in packets:
    groups[len(pkt)].append(pkt)

print(f"Total packets: {len(packets)}")
print(f"Lengths: {sorted(groups.keys())}")

# Try CRCBeagle on each length group
for pktlen in sorted(groups.keys()):
    pkts = groups[pktlen]
    print(f"\n=== Length {pktlen} ({len(pkts)} packets) ===")
    
    # Try assuming last 2 bytes are CRC-16
    if pktlen > 2:
        data_list = [pkt[:-2] for pkt in pkts[:4]]
        crc_list = [pkt[-2:] for pkt in pkts[:4]]
        # CRCBeagle expects CRC as integer list (little-endian or big-endian)
        crc_be = [[c[1], c[0]] for c in crc_list]  # big-endian
        crc_le = [list(c) for c in crc_list]        # little-endian
        
        crcb = CRCBeagle()
        
        # Try big-endian CRC
        try:
            crcb.search(data_list, crc_be)
            print(f"  CRC-16 BE: found matches")
        except Exception as e:
            print(f"  CRC-16 BE: {e}")
        
        # Try little-endian CRC
        crcb2 = CRCBeagle()
        try:
            crcb2.search(data_list, crc_le)
            print(f"  CRC-16 LE: found matches")
        except Exception as e:
            print(f"  CRC-16 LE: {e}")
    
    # Try assuming last 1 byte is CRC-8
    if pktlen > 1:
        data_list = [pkt[:-1] for pkt in pkts[:4]]
        crc_list = [[pkt[-1]] for pkt in pkts[:4]]
        
        crcb3 = CRCBeagle()
        try:
            crcb3.search(data_list, crc_list)
            print(f"  CRC-8: found matches")
        except Exception as e:
            print(f"  CRC-8: {e}")
