import sys
import re
from pymavlink.dialects.v10 import common as mavlink1

def parse_packets(filename):
    packets = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Extract hex bytes: try to find '->' for timestamped format
            match = re.search(r'->\s+((?:[0-9A-Fa-f]{2}\s)+)', line)
            if match:
                hex_str = match.group(1).strip()
            else:
                # Fallback: assume the line starts with hex bytes until '[' or double space, or just read the hex chars
                match = re.match(r'^((?:[0-9A-Fa-f]{2}\s*)+)', line)
                if match:
                    hex_str = match.group(1).strip()
                else:
                    continue
                    
            if hex_str:
                raw = bytes.fromhex(hex_str.replace(' ', ''))
                packets.append(raw)
    return packets

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_pymavlink.py <packets.txt>")
        return

    filename = sys.argv[1]
    packets = parse_packets(filename)
    
    # Create a MAVLink parser instance. We don't need a file descriptor to just parse buffers.
    # The MAVLink class takes a file-like object and optionally a srcSystem and srcComponent.
    class DummyFile:
        def write(self, data):
            pass
            
    mav = mavlink1.MAVLink(DummyFile(), srcSystem=1, srcComponent=1)
    # Ensure it's MAVLink v1 (the packets start with FE)
    mav.wire_protocol_version = '1.0'

    byte_stream = bytearray()
    for pkt in packets:
        byte_stream.extend(pkt)

    print(f"Loaded {len(packets)} packets, parsing with pymavlink...")
    
    parsed_msgs = []
    while True:
        # Provide bytes to the parser
        msg = mav.parse_char(byte_stream[0:1]) if byte_stream else None
        if not msg and len(byte_stream) > 0:
            byte_stream = byte_stream[1:]
            continue
        elif msg:
            parsed_msgs.append(msg)
            byte_stream = byte_stream[1:]
        else:
            break

    print(f"Successfully parsed {len(parsed_msgs)} messages.\n")
    
    # Display the parsed messages
    for i, msg in enumerate(parsed_msgs):
        print(f"Message {i}: {msg.get_type()} (ID: {msg.get_msgId()})")
        
        # Display fields for common messages
        if msg.get_msgId() not in [7, 52]:  # Skip proprietary messages for detailed breakdown 
            # Or just print the whole object as dictionary
            msg_dict = msg.to_dict()
            for key, value in msg_dict.items():
                if key != 'mavpackettype':
                    print(f"  {key}: {value}")
        else:
            print(f"  [Proprietary/Unknown format, payload structure unknown in 'common' dialect]")
        
        print()

if __name__ == "__main__":
    main()
