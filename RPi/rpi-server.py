import socket
import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD
import time

# GPIO cleanup at the start to avoid issues with previous runs
GPIO.cleanup()

# Configuration for the I2C LCD display
lcd = CharLCD(i2c_expander='PCF8574', address=0x3f, port=1,
              cols=16, rows=2, charmap='A00', auto_linebreaks=True)

# Configuration for the RGB LED (common cathode)
red_pin = 5
green_pin = 6
blue_pin = 14

GPIO.setmode(GPIO.BCM)
GPIO.setup(red_pin, GPIO.OUT)
GPIO.setup(green_pin, GPIO.OUT)
GPIO.setup(blue_pin, GPIO.OUT)

def set_rgb_color(red, green, blue):
    GPIO.output(red_pin, GPIO.LOW if red else GPIO.HIGH)
    GPIO.output(green_pin, GPIO.LOW if green else GPIO.HIGH)
    GPIO.output(blue_pin, GPIO.LOW if blue else GPIO.HIGH)

def display_on_lcd(message_line1, message_line2=""):
    lcd.clear()
    lcd.write_string(message_line1.ljust(16))  # Ensure the message fits within the display width
    lcd.write_string('\r\n')  # Move to the next line
    lcd.write_string(message_line2.ljust(16))  # Ensure the message fits within the display width

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 65432))
    server_socket.listen(1)
    print("Server is listening for connections...")

    conn, addr = server_socket.accept()
    print(f"Connected by {addr}")

    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break

            material_type, accuracy = data.split(',')
            accuracy = float(accuracy)

            # Display the result on the LCD
            display_on_lcd(f'Material: {material_type[:8]}', f'Accuracy: {accuracy:.2%}')

            # Update the RGB LED
            if accuracy > 0.8:
                set_rgb_color(0, 1, 0)  # Green for high confidence
            else:
                set_rgb_color(1, 1, 0)  # Yellow for low confidence

            for _ in range(5):
                set_rgb_color(0, 1, 0)  # Flash green
                time.sleep(0.2)
                set_rgb_color(0, 0, 0)
                time.sleep(0.2)

    finally:
        conn.close()
        server_socket.close()
        GPIO.cleanup()

if __name__ == "__main__":
    main()


