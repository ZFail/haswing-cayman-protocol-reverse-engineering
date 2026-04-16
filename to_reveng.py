#!/usr/bin/env python3
"""Convert packets.txt hex dumps to reveng-compatible format (continuous hex, no spaces)."""

import re
import sys

INPUT = "packets.txt"

with open(INPUT) as f:
    lines = f.readlines()

packets = []
for line in lines:
    # Extract hex bytes between timestamp "->" and "["
    m = re.search(r"->\s+([0-9A-F ]+)\s+\[", line)
    if m:
        hex_bytes = m.group(1).split()
        packets.append("".join(hex_bytes).lower())

# Full packets
with open("reveng_packets.txt", "w") as f:
    for pkt in packets:
        f.write(pkt + "\n")

# Without first byte
with open("reveng_packets_no_first1.txt", "w") as f:
    for pkt in packets:
        f.write(pkt[2:] + "\n")

# Without first 2 bytes
with open("reveng_packets_no_first2.txt", "w") as f:
    for pkt in packets:
        f.write(pkt[4:] + "\n")

print(f"Wrote {len(packets)} packets to each output file")
