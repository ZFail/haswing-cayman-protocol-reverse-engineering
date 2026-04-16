# Haswing Cayman 55 GPS — Pymavlink Decoding Results

Yes! You can easily use the standard Python `pymavlink` library to automatically parse the messages from your Haswing trolling motor. 

We successfully created a virtual environment, installed `pymavlink`, and parsed your capture file using the `MAVLink 1` protocol and the `common` dialect.

## MAVLink Messages Recognized Directly

Pymavlink successfully extracted these `common` standard messages right out of the box, with full data decodes:

| ID | Message | Parsed Data Elements |
|---|---|---|
| `0` | **HEARTBEAT** | `type: 110`, `autopilot: 0`, `base_mode: 0`, `custom_mode: 103`, `system_status: 4`, `mavlink_version: 3` |
| `26` | **SCALED_IMU** | `time_boot_ms: 0`, `xacc: 1528`, `...`, `xgyro: 0`, `xmag: 217`, `ymag: 32`, `zmag: -350` |
| `27` | **RAW_IMU** | `time_usec: 0`, `xacc: 0`, `yacc: 0`, `zacc: 0`, `ygyro: 250`, `xmag: 2`, `ymag: 0`, `zmag: 0` |
| `30` | **ATTITUDE** | `roll: 0.0`, `pitch: 4.0`, `yaw: 0.146`, `rollspeed: 0.0`, `pitchspeed: 0.0`, `yawspeed: 0.0` |
| `33` | **GLOBAL_POSITION_INT** | `lat: 0`, `lon: 0`, `alt: 0`, `vx: 0`, `vy: 0`, `vz: 0`, `hdg: 8` |

> [!NOTE]  
> The **ATTITUDE** message perfectly decodes the boat's Pitch (4.0°) and Yaw (0.146 rad ~= 8.3°) directly. The **GLOBAL_POSITION_INT** has lat/lon starting at 0, indicating a GPS fix might still be acquiring or there's an offset.

## Proprietary (Custom) Messages

The Haswing uses some non-standard message IDs. By default, `pymavlink`'s `common` dialect tries to map them to its known IDs, or leaves them as unknowns:

* **ID `7`**: Interpreted as `AUTH_KEY` by common MAVLink, but given it clearly contains a string `HSW_m4Cgo` (Haswing m4 Cgo), this is definitely a custom Haswing identification block.
* **ID `52` (`0x34`)**: Handled as `UNKNOWN_52` by Pymavlink, simply giving byte arrays.

## How to parse it yourself

To write scripts reading directly from the Haswing serial port with `pymavlink`:

1.  **Set up the environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install pymavlink
    ```

2.  **Use Pymavlink's mavutil connecting to RS232:**

```python
from pymavlink import mavutil

# Configure serial connection (replace '/dev/ttyUSB0' and baud match your setup)
master = mavutil.mavlink_connection('/dev/ttyUSB0', baud=9600)

print("Waiting for heartbeat...")
master.wait_heartbeat()
print(f"Heartbeat from system (system {master.target_system} component {master.target_component})")

while True:
    try:
        # Fetch a message
        msg = master.recv_match(blocking=True)
        if not msg:
            continue
            
        # Pymavlink parsed object
        msg_type = msg.get_type()
        
        # Display standard messages natively
        if msg_type == 'ATTITUDE':
            print(f"Orientation: Pitch {msg.pitch:0.2f}, Roll {msg.roll:0.2f}, Yaw {msg.yaw:0.2f}")
            
        elif msg_type == 'GLOBAL_POSITION_INT':
            print(f"GPS: Lat {msg.lat}, Lon {msg.lon}, Heading {msg.hdg/100.0} deg")
            
        elif msg_type == 'BAD_DATA':
            # This handles custom IDs Pymavlink doesn't know yet
            pass 
            
    except Exception as e:
        print(f"Error parsing: {e}")
```

If you wish to fully decode IDs 7 and 52, you can also define a [custom XML MAVLink dialect](https://mavlink.io/en/guide/xml_schema.html) locally and tell `pymavlink` to compile it. That way, all Haswing variables get parsed directly!
