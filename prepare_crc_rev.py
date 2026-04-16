#!/usr/bin/env python3
"""Extract packets from packets.txt, group by length, prepare for crc_rev."""

import re
import os

INPUT = "packets.txt"

with open(INPUT) as f:
    content = f.read()

# Split into lines that start with a timestamp
lines = re.split(r'(?=\d{2}:\d{2}:\d{2}\.\d+ ->)', content)

packets = []
for line in lines:
    line = line.strip()
    if not line:
        continue
    m = re.search(r'->\s+([0-9A-Fa-f ]+)\s+\[', line.replace('\n', ' '))
    if m:
        hex_bytes = m.group(1).split()
        pkt_bytes = bytes(int(b, 16) for b in hex_bytes)
        packets.append(pkt_bytes)

from collections import defaultdict
groups = defaultdict(list)
for pkt in packets:
    groups[len(pkt)].append(pkt)

print(f"Total packets: {len(packets)}")
print(f"Unique lengths: {sorted(groups.keys())}")

outdir = "crc_rev_input"
os.makedirs(outdir, exist_ok=True)

for pktlen, pkts in sorted(groups.items()):
    # Assume last 2 bytes are CRC-16, or last 1 byte is CRC-8
    # Write data (without last 2 bytes) and CRC separately
    for i, pkt in enumerate(pkts):
        # Try CRC-16 (last 2 bytes)
        if pktlen > 2:
            data = pkt[:-2]
            crc = pkt[-2] | (pkt[-1] << 8)  # little-endian
            with open(f"{outdir}/len{pktlen}_d{i}.bin", 'wb') as f:
                f.write(data)
            with open(f"{outdir}/len{pktlen}_crcs.txt", 'a') as f:
                f.write(f"{outdir}/len{pktlen}_d{i}.bin 0x{crc:04x}\n")

        # Try CRC-8 (last 1 byte)
        if pktlen > 1:
            data8 = pkt[:-1]
            crc8 = pkt[-1]
            with open(f"{outdir}/len{pktlen}_d8_{i}.bin", 'wb') as f:
                f.write(data8)
            with open(f"{outdir}/len{pktlen}_crcs8.txt", 'a') as f:
                f.write(f"{outdir}/len{pktlen}_d8_{i}.bin 0x{crc8:02x}\n")

    print(f"  len={pktlen}: {len(pkts)} packets prepared")
