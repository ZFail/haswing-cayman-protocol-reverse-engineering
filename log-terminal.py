import serial
import time
s = serial.Serial('COM11',115000)
text = ""
file = open("a.txt", "w")
while 1:
      if s.in_waiting:
        try:
            val = s.read(s.inWaiting())
            text = val.decode().replace('\r', '')
            print(text, end='')
            file.write(text)
            file.flush() # Optional, but recommended
        except:
            pass