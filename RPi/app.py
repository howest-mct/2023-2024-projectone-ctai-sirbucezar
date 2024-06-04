import socket
import os
import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD

# Initial cleanup to avoid conflicts
GPIO.cleanup()

# Configuration for the I2C LCD display
lcd = CharLCD(i2c_expander='PCF8574', address=0x3f, port=1,
              cols=16, rows=2, charmap='A00', auto_linebreaks=True)

# Server port
SERVER_PORT = 65432

def get_ip_address():
    try:
        # Connect to an external host to get the IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
    except Exception as e:
        ip_address = "No IP"
    return ip_address

def display_on_lcd(message_line1, message_line2=""):
    lcd.clear()
    lcd.write_string(message_line1.ljust(16))  # Ensure the message fits within the display width
    lcd.write_string('\r\n')  # Move to the next line
    lcd.write_string(message_line2.ljust(16))  # Ensure the message fits within the display width

def main():
    ip_address = get_ip_address()
    print(f"IP Address: {ip_address}")
    print(f"Server Port: {SERVER_PORT}")
    display_on_lcd(f"IP: {ip_address}", f"Port: {SERVER_PORT}")

if __name__ == "__main__":
    main()
