import csv
import os
import RPi.GPIO as GPIO
import time
from RPLCD.i2c import CharLCD
import config
import requests

# Setup for LCD Display
lcd = CharLCD(
    i2c_expander='PCF8574',
    address=config.lcd_address,
    port=1,
    cols=config.lcd_cols,
    rows=config.lcd_rows,
    charmap='A00',
    auto_linebreaks=True
)

# Initialize GPIO
GPIO.setup(config.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(config.start_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(config.red_pin, GPIO.OUT)
GPIO.setup(config.green_pin, GPIO.OUT)
GPIO.setup(config.blue_pin, GPIO.OUT)

def set_rgb_color(red, green, blue):
    """Sets the RGB LED to the specified color."""
    GPIO.output(config.red_pin, GPIO.LOW if red else GPIO.HIGH)
    GPIO.output(config.green_pin, GPIO.LOW if green else GPIO.HIGH)
    GPIO.output(config.blue_pin, GPIO.LOW if blue else GPIO.HIGH)

def blink_rgb_color(red, green, blue, duration, blink_rate=0.5):
    """Blinks the RGB LED in the specified color."""
    end_time = time.time() + duration
    while time.time() < end_time:
        set_rgb_color(red, green, blue)
        time.sleep(blink_rate)
        set_rgb_color(0, 0, 0)
        time.sleep(blink_rate)

def blink_yellow_until_complete(classification_complete):
    """Blinks the LED yellow until classification is complete."""
    while not classification_complete:
        set_rgb_color(1, 1, 0)  # Yellow
        time.sleep(0.5)
        set_rgb_color(0, 0, 0)
        time.sleep(0.5)

def display_on_lcd(message_line1, message_line2=""):
    """Displays a message on the LCD."""
    lcd.clear()
    lcd.write_string(message_line1.ljust(16))
    if message_line2:
        lcd.write_string('\r\n')
        lcd.write_string(message_line2.ljust(16))

def check_internet_connection(url='http://www.google.com/', timeout=1):
    """Checks if the internet connection is available."""
    try:
        requests.head(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        return False

def initialize_csv_file(file_path):
    """Initializes the CSV file if it does not exist."""
    if not os.path.exists(file_path):
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['prediction_id', 'bin_nr', 'accuracy'])

def get_next_prediction_id(file_path):
    """Gets the next prediction ID for CSV logging."""
    if not os.path.exists(file_path):
        return 1
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        rows = list(reader)
        if len(rows) == 1:
            return 1
        return len(rows)

def log_prediction(material_type, accuracy, file_path):
    """Logs the prediction to the CSV file."""
    prediction_id = get_next_prediction_id(file_path)
    bin_nr = config.bin_mapping.get(material_type, -1)
    accuracy_percentage = accuracy * 100

    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([prediction_id, bin_nr, f'{accuracy_percentage:.2f}'])
