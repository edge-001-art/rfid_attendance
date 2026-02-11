import serial
import requests

SERIAL_PORT = "COM3"  # Change if needed
BAUD_RATE = 9600
SERVER = "http://127.0.0.1:5000/scan/"

ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
print("RFID reader started...")

while True:
    tag = ser.readline().decode().strip()
    if tag:
        print("Scanned:", tag)
        requests.get(SERVER + tag)
