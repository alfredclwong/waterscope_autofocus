"""move.py

Simple script to allow manual movement of servo.
"""

import sys

# I2C communication
import smbus
bus = smbus.SMBus(1)
address = 0x04

# Check for command-line argument
if len(sys.argv) is not 2:
    print("error: expected exactly one command-line argument")
    sys.exit()

# Cast command-line argument to int and write to Arduino
bus.write_byte(address, int(sys.argv[1]))
