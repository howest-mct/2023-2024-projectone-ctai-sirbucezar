import os
import cv2
import csv
import time
import requests
from ultralytics import YOLO
import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD

# Determine the script's directory
script_dir = os.path.dirname(os.path.realpath(__file__))

# Construct full paths
model_path = os.path.join(script_dir, 'yolo_finetuned.pt')
img_path = os.path.join(script_dir, 'testphotos', 'test6.png')

# Debug: Print current working directory and paths
print(f"Current working directory: {os.getcwd()}")
print(f"Model path: {model_path}")
print(f"Image path: {img_path}")

# Debug: Check if model file exists
if not os.path.exists(model_path):
    print(f"Model file does not exist: {model_path}")
else:
    print(f"Model file found: {model_path}")

# Load model
model = YOLO(model_path)

# Configuration for the I2C LCD display
lcd = CharLCD(i2c_expander='PCF8574', address=0x3f, port=1,
              cols=16, rows=2, charmap='A00', auto_linebreaks=True)

# Configuration for the RGB LED (common cathode)
red_pin = 5
green_pin = 6
blue_pin = 13

GPIO.setmode(GPIO.BCM)
GPIO.setup(red_pin, GPIO.OUT)
GPIO.setup(green_pin, GPIO.OUT)
GPIO.setup(blue_pin, GPIO.OUT)

# Configuration for the button
button_pin = 20
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def set_rgb_color(red, green, blue):
    GPIO.output(red_pin, GPIO.LOW if red else GPIO.HIGH)
    GPIO.output(green_pin, GPIO.LOW if green else GPIO.HIGH)
    GPIO.output(blue_pin, GPIO.LOW if blue else GPIO.HIGH)

def blink_rgb_color(red, green, blue, duration, blink_rate=0.5):
    end_time = time.time() + duration
    while time.time() < end_time:
        set_rgb_color(red, green, blue)
        time.sleep(blink_rate)
        set_rgb_color(0, 0, 0)
        time.sleep(blink_rate)

def check_internet_connection(url='http://www.google.com/', timeout=5):
    try:
        requests.head(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        return False

bin_mapping = {
    'Glass': 1,
    'PMD': 2,
    'Paper': 3,
    'Rest': 4
}

csv_file_path = 'bin_logs.csv'

def initialize_csv_file(file_path):
    if not os.path.exists(file_path):
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['prediction_id', 'bin_nr', 'accuracy'])

def get_next_prediction_id(file_path):
    if not os.path.exists(file_path):
        return 1
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        rows = list(reader)
        if len(rows) == 1:
            return 1
        return len(rows)

def process_image(img_path):
    print(f"Current working directory: {os.getcwd()}")
    print(f"Image path: {img_path}")
    if not os.path.exists(img_path):
        print(f"File does not exist: {img_path}")
        return None, None
    
    img = cv2.imread(img_path)
    if img is None:
        print(f"Failed to load image {img_path}")
        return None, None
    
    print(f"Image loaded: {img_path}, shape: {img.shape}")
    
    predictions = model.predict(source=img_path, save=False)
    
    if len(predictions) == 0 or len(predictions[0].boxes) == 0:
        print("No predictions or boxes found.")
        return None, None
    
    boxes = predictions[0].boxes.xyxy  
    confs = predictions[0].boxes.conf  
    cls = predictions[0].boxes.cls  
    
    classifications = []
    accuracies = []

    for i in range(len(boxes)):
        label = model.names[int(cls[i])]
        confidence = confs[i]
        classifications.append(label)
        accuracies.append(confidence)
    
    if classifications and accuracies:
        max_confidence_index = accuracies.index(max(accuracies))
        material_type = classifications[max_confidence_index]
        accuracy = accuracies[max_confidence_index]
        return material_type, accuracy

    return None, None

def log_prediction(material_type, accuracy, file_path):
    prediction_id = get_next_prediction_id(file_path)
    bin_nr = bin_mapping.get(material_type, -1)
    accuracy_percentage = accuracy * 100
    
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([prediction_id, bin_nr, f'{accuracy_percentage:.2f}'])

def display_on_lcd(message_line1, message_line2=""):
    lcd.clear()
    lcd.write_string(message_line1.ljust(16))  # Ensure the message fits within the display width
    lcd.write_string('\r\n')  # Move to the next line
    lcd.write_string(message_line2.ljust(16))  # Ensure the message fits within the display width

# Initialization
def initialize_system():
    display_on_lcd('INITIATION...')
    blink_rgb_color(1, 0, 0, 3)  # Blink red for at least 3 seconds
    connected = check_internet_connection()
    while not connected:
        display_on_lcd('INITIATION...')
        blink_rgb_color(1, 0, 0, 3)
        connected = check_internet_connection()
    display_on_lcd('Ready to scan!')
    set_rgb_color(0, 1, 0)  # Static green

# Scan and classify
def scan_and_classify(img_path):
    display_on_lcd('Classifying...')
    blink_rgb_color(1, 1, 0, 3)  # Blink yellow for at least 3 seconds

    material_type, accuracy = process_image(img_path)
    if material_type and accuracy is not None:
        print(f'Material: {material_type}, Accuracy: {accuracy:.2%}')
        log_prediction(material_type, accuracy, csv_file_path)
        
        for _ in range(5):
            set_rgb_color(0, 1, 0)  # Flash green
            time.sleep(0.2)
            set_rgb_color(0, 0, 0)
            time.sleep(0.2)
        
        display_on_lcd(f'Material: {material_type[:8]}', f'Accuracy: {accuracy:.2%}')
    else:
        display_on_lcd("Error", "No prediction")
        set_rgb_color(1, 0, 0)  # Red for error
        time.sleep(2)

# Initialize the CSV file with headers
initialize_csv_file(csv_file_path)

# Main loop
try:
    initialize_system()
    
    while True:
        button_state = GPIO.input(button_pin)
        if button_state == GPIO.LOW:
            # Debounce the button press
            time.sleep(0.1)
            if GPIO.input(button_pin) == GPIO.LOW:
                scan_and_classify(img_path)
                time.sleep(1)  # Add a short delay to prevent multiple detections
finally:
    # Clean up GPIO pins before exiting
    GPIO.cleanup()
