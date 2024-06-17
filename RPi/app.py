# service.py
import RPi.GPIO as GPIO
import time
from RPLCD.i2c import CharLCD
import threading
import subprocess
import signal
import os
from utils import set_rgb_color
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# GPIO Pin Definitions
power_button_pin = 18
power_led_pin = 23

# Setup for LCD Display
lcd = CharLCD(
    i2c_expander='PCF8574',
    address=0x27,
    port=1,
    cols=16,
    rows=2,
    charmap='A00',
    auto_linebreaks=True
)

# Set the GPIO mode
GPIO.setmode(GPIO.BCM)

# GPIO Setup
GPIO.setup(power_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(power_led_pin, GPIO.OUT)

# State to track the power status and the process
system_powered_on = False
main_script_process = None

def update_lcd_display(message_line1, message_line2=""):
    """Helper function to update the LCD display."""
    lcd.clear()
    lcd.write_string(message_line1.ljust(16))
    if message_line2:
        lcd.write_string('\r\n')
        lcd.write_string(message_line2.ljust(16))

def power_button_callback(channel):
    """Callback function to handle power button press."""
    global system_powered_on, main_script_process

    if GPIO.input(power_button_pin) == GPIO.LOW:  # Button pressed
        system_powered_on = True
        GPIO.output(power_led_pin, GPIO.HIGH)    # Turn on LED
        update_lcd_display("System ON")

        # Start the main script if not already running
        if main_script_process is None or main_script_process.poll() is not None:
            main_script_process = subprocess.Popen(
                ["python3", "/home/user/2023-2024-projectone-ctai-sirbucezar/RPi/main.py"],
                preexec_fn=os.setsid
            )
            print("Main script started.")
    else:
        system_powered_on = False
        GPIO.output(power_led_pin, GPIO.LOW)
        update_lcd_display("System OFF")

        if main_script_process is not None and main_script_process.poll() is None:
            os.killpg(os.getpgid(main_script_process.pid), signal.SIGINT)
            main_script_process.wait()
            update_lcd_display("System OFF")
            GPIO.output(power_led_pin, GPIO.LOW)
            main_script_process = None

# Setup the callback for the power button
GPIO.add_event_detect(power_button_pin, GPIO.BOTH, callback=power_button_callback, bouncetime=300)

try:
    update_lcd_display("System OFF")
    GPIO.output(power_led_pin, GPIO.LOW)
    while True:
        time.sleep(1)
finally:
    set_rgb_color(0,0,0)
    GPIO.cleanup()
