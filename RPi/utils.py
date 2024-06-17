# utils.py
import os
import csv
import time
import requests
import RPi.GPIO as GPIO
from config import RED_PIN, GREEN_PIN, BLUE_PIN, CSV_FILE_PATH, BIN_MAPPING

# Function to set RGB color using the GPIO pins
def set_rgb_color(red, green, blue):
    GPIO.output(RED_PIN, GPIO.LOW if red else GPIO.HIGH)
    GPIO.output(GREEN_PIN, GPIO.LOW if green else GPIO.HIGH)
    GPIO.output(BLUE_PIN, GPIO.LOW if blue else GPIO.HIGH)

# Function to blink the RGB LED with specified color, duration, and blink rate
def blink_rgb_color(red, green, blue, duration, blink_rate=0.5):
    end_time = time.time() + duration
    while time.time() < end_time:
        set_rgb_color(red, green, blue)
        time.sleep(blink_rate)
        set_rgb_color(0, 0, 0)
        time.sleep(blink_rate)

# Function to display messages on the LCD screen
def display_on_lcd(lcd, message_line1, message_line2=""):
    lcd.clear()
    lcd.write_string(message_line1.ljust(16))
    if message_line2:
        lcd.write_string('\r\n')
        lcd.write_string(message_line2.ljust(16))

# Function to check the internet connection by pinging a URL
def check_internet_connection(url='http://www.google.com/', timeout=1):
    try:
        requests.head(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        return False

def initialize_csv_file(file_path=None):
    # Use the default path from config if no file_path is provided
    if file_path is None:
        file_path = CSV_FILE_PATH
    
    # Ensure the file_path is not None
    if file_path is None:
        raise ValueError("CSV file path is not provided and the default CSV_FILE_PATH is None")

    if not os.path.exists(file_path):
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['prediction_id', 'bin_nr', 'accuracy'])

# Function to get the next prediction ID for logging in the CSV file
def get_next_prediction_id(file_path=None):
    # Use the default path from config if no file_path is provided
    if file_path is None:
        file_path = CSV_FILE_PATH

    if not os.path.exists(file_path):
        return 1
    
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        rows = list(reader)
        if len(rows) == 1:
            return 1
        return len(rows)

# Function to log the prediction details to the CSV file
def log_prediction(material_type, accuracy, file_path=None):
    # Use the default path from config if no file_path is provided
    if file_path is None:
        file_path = CSV_FILE_PATH

    prediction_id = get_next_prediction_id(file_path)
    bin_nr = BIN_MAPPING.get(material_type, -1)
    accuracy_percentage = accuracy * 100

    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([prediction_id, bin_nr, f'{accuracy_percentage:.2f}'])
