import os
import time
import csv
import subprocess
import cv2
import numpy as np
import requests
from ultralytics import YOLO
import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD
import threading

# Set the display environment variable
os.environ['DISPLAY'] = ':0'

# Determine the script's directory
script_dir = os.path.dirname(os.path.realpath(__file__))

# Construct full paths
model_path = os.path.join(script_dir, 'yolo_finetuned.pt')
img_dir = os.path.join(script_dir, 'captured_images')
csv_file_path = 'RPi/bin_logs.csv'
os.makedirs(img_dir, exist_ok=True)

# Load the YOLO model
yolo_model = YOLO(model_path)

# Roboflow API setup
roboflow_api_url = "https://detect.roboflow.com"
roboflow_api_key = "jVDDnNjzY9vikw8mBH65"
roboflow_model_id = "projectone-classification/2"

# GPIO and peripheral setup
button_pin = 20  # Button to capture images
start_button_pin = 25  # Non-momentary button to start/stop the main loop
red_pin = 13
green_pin = 6
blue_pin = 5

# Power button and LED setup
power_button_pin = 18  # Button to control power state
power_led_pin = 23  # LED to indicate power state

GPIO.setmode(GPIO.BCM)
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(start_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(red_pin, GPIO.OUT)
GPIO.setup(green_pin, GPIO.OUT)
GPIO.setup(blue_pin, GPIO.OUT)

GPIO.setup(power_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(power_led_pin, GPIO.OUT)

lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=2, charmap='A00', auto_linebreaks=True)

# Define bin mapping
bin_mapping = {
    'Glass': 1,
    'PMD': 2,
    'Paper': 3,
    'Rest': 4
}

# State variable to keep track of power status
system_powered_on = False

# Global variable to track classification status
classification_complete = False

# RGB LED control functions
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

# New function to blink yellow LED until classification completes
def blink_yellow_until_complete():
    global classification_complete
    while not classification_complete:
        set_rgb_color(1, 1, 0)  # Yellow
        time.sleep(0.5)
        set_rgb_color(0, 0, 0)
        time.sleep(0.5)

# Check internet connection
def check_internet_connection(url='http://www.google.com/', timeout=1):
    try:
        requests.head(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        return False

# CSV file initialization
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

# Display control for LCD
def display_on_lcd(message_line1, message_line2=""):
    lcd.clear()
    lcd.write_string(message_line1.ljust(16))  # Ensure the message fits within the display width
    lcd.write_string('\r\n')  # Move to the next line
    lcd.write_string(message_line2.ljust(16))  # Ensure the message fits within the display width

# Capture image using libcamera-still
def capture_image():
    img_path = os.path.join(img_dir, 'captured_image.jpg')
    capture_command = ['libcamera-still', '-o', img_path, '--timeout', '1']
    subprocess.run(capture_command)
    return img_path

# Crop the bounding box from the image
def crop_bounding_box(img_path, box):
    img = cv2.imread(img_path)
    x1, y1, x2, y2 = map(int, box)
    margin = 20  # Adding margin to the bounding box
    x1 = max(0, x1 - margin)
    y1 = max(0, y1 - margin)
    x2 = min(img.shape[1], x2 + margin)
    y2 = min(img.shape[0], y2 + margin)
    cropped_img = img[y1:y2, x1:x2]
    cropped_img_path = os.path.join(img_dir, 'cropped_image.png')
    cv2.imwrite(cropped_img_path, cropped_img)
    return cropped_img_path

# Classify the cropped image using the Roboflow model
def classify_cropped_object(cropped_img_path):
    img = cv2.imread(cropped_img_path)
    _, img_encoded = cv2.imencode('.jpg', img)
    files = {
        'file': ('image.jpg', img_encoded.tobytes(), 'image/jpeg')
    }

    url = f"{roboflow_api_url}/{roboflow_model_id}?api_key={roboflow_api_key}"
    response = requests.post(url, files=files)

    if response.status_code == 200:
        classification_result = response.json()
        if 'predictions' in classification_result and classification_result['predictions']:
            predicted_class = classification_result['predictions'][0]['class']
            confidence = classification_result['predictions'][0]['confidence']
            return predicted_class, confidence
        else:
            print("No predictions found in the response.")
    else:
        print(f"Error in classification: {response.status_code}, {response.text}")
    return None, None

# Process image with YOLO and classify detected object
def process_image(img_path):
    print(f"Processing image: {img_path}")
    if not os.path.exists(img_path):
        return None, None, None

    img = cv2.imread(img_path)
    if img is None:
        return None, None, None

    predictions = yolo_model.predict(source=img, save=False)

    if not predictions or not predictions[0].boxes:
        return None, None, None

    boxes = predictions[0].boxes.xyxy
    confs = predictions[0].boxes.conf
    cls = predictions[0].boxes.cls

    max_confidence_index = np.argmax(confs)
    box = boxes[max_confidence_index]
    confidence = confs[max_confidence_index]
    label = yolo_model.names[int(cls[max_confidence_index])]

    # Draw bounding boxes on the image
    x1, y1, x2, y2 = map(int, box)
    cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
    cv2.putText(img, f"{label} {confidence:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    # Save the image with bounding boxes
    output_img_path = img_path.replace('captured_image.jpg', 'captured_image_with_boxes.jpg')
    cv2.imwrite(output_img_path, img)

    cropped_img_path = crop_bounding_box(img_path, box)
    return cropped_img_path, label, confidence

# Log prediction to CSV
def log_prediction(material_type, accuracy, file_path):
    prediction_id = get_next_prediction_id(file_path)
    bin_nr = bin_mapping.get(material_type, -1)
    accuracy_percentage = accuracy * 100

    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([prediction_id, bin_nr, f'{accuracy_percentage:.2f}'])

# Initialization sequence
def initialize_system():
    display_on_lcd('INITIATION...')
    blink_rgb_color(1, 0, 0, 3)  # Blink red for at least 3 seconds
    connected = check_internet_connection()
    while not connected:
        display_on_lcd('INITIATION...')
        blink_rgb_color(1, 0, 0, 3)
        connected = check_internet_connection()
    display_on_lcd('Press the scan' , 'button!')
    set_rgb_color(255, 255, 0)  # Static yellow
def display_on_lcd_with_yellow_reset(message_line1, message_line2=""):
    lcd.clear()
    lcd.write_string(message_line1.ljust(16))  # Ensure the message fits within the display width
    lcd.write_string('\r\n')  # Move to the next line
    lcd.write_string(message_line2.ljust(16))  # Ensure the message fits within the display width
    
    # If the message is "Press the scan button", set the LED to yellow
    if message_line1.startswith('Press the scan'):
        set_rgb_color(1, 1, 0)  # Yellow

# Display alternating message on LCD
def display_alternating_message(material, accuracy, duration=5, interval=1):
    start_time = time.time()
    while time.time() - start_time < duration:
        display_on_lcd(f'Material: {material}', f'Accuracy: {accuracy:.2%}')
        time.sleep(interval)
        display_on_lcd('Press the scan' , 'button!')
        time.sleep(interval)

# Callback function for the power button
def power_button_callback(channel):
    global system_powered_on
    if GPIO.input(power_button_pin) == GPIO.LOW:
        print("Turning system ON.")
        system_powered_on = True
        GPIO.output(power_led_pin, GPIO.HIGH)
        display_on_lcd('System ON')
        initialize_system()
    else:
        print("Turning system OFF.")
        system_powered_on = False
        GPIO.output(power_led_pin, GPIO.LOW)
        time.sleep(0.5)
        display_on_lcd('System OFF')
        # Ensure all LEDs are off
        set_rgb_color(0, 0, 0)

# Main loop controlled by the start button
def main_loop():
    global classification_complete
    
    while system_powered_on:
        try:
            # Check for the start button press to begin scanning
            while GPIO.input(start_button_pin) == GPIO.HIGH and system_powered_on:
                display_on_lcd('Press Start Button')
                time.sleep(1)

            while GPIO.input(start_button_pin) == GPIO.LOW and system_powered_on:
                button_state = GPIO.input(button_pin)
                if button_state == GPIO.LOW:
                    display_on_lcd('Classifying...')  # Display 'Classifying...' message
                    time.sleep(0.3)  # Optional delay for better user experience
                    
                    # Start flashing yellow LED in a separate thread
                    classification_complete = False
                    threading.Thread(target=blink_yellow_until_complete).start()

                    img_path = capture_image()
                    cropped_img_path, label, detection_confidence = process_image(img_path)

                    if cropped_img_path is not None:
                        print(f'Detected: {label} with confidence: {detection_confidence:.2f}')

                        classified_material, classification_confidence = classify_cropped_object(cropped_img_path)

                        if classified_material and classification_confidence is not None:
                            print(f'Classified as: {classified_material} with confidence: {classification_confidence:.2f}')
                            log_prediction(classified_material, classification_confidence, csv_file_path)

                            # Stop yellow flashing by setting classification_complete to True
                            classification_complete = True

                            for _ in range(5):
                                set_rgb_color(0, 1, 0)  # Flash green
                                time.sleep(0.2)
                                set_rgb_color(0, 0, 0)
                                time.sleep(0.2)

                            display_on_lcd(f'Material: {classified_material[:8]}', f'Accuracy: {classification_confidence:.2%}')
                            time.sleep(5)
                            display_alternating_message(classified_material, classification_confidence)
                        else:
                            display_on_lcd('Error' , 'No classification')
                            set_rgb_color(1, 0, 0)  # Red for error
                            time.sleep(2)
                            classification_complete = True  # Ensure to stop yellow flashing

                    else:
                        display_on_lcd('Error' , 'No detection')
                        set_rgb_color(1, 0, 0)  # Red for error
                        time.sleep(2)
                        classification_complete = True  # Ensure to stop yellow flashing
                    
                    # Ensure yellow flashing stops if the process ended unexpectedly
                    classification_complete = True

        except Exception as e:
            print(f"An error occurred: {e}")
            break

# Initialize the CSV file with headers
initialize_csv_file(csv_file_path)

# Main execution
try:
    # Set up a callback for the power button
    GPIO.add_event_detect(power_button_pin, GPIO.BOTH, callback=power_button_callback, bouncetime=200)

    while True:
        if system_powered_on:
            main_loop()
        else:
            # If system is off, ensure LED is off and wait
            GPIO.output(power_led_pin, GPIO.LOW)
            display_on_lcd('System OFF')
            time.sleep(0.5)  # Small delay before checking again

finally:
    print("Cleaning up GPIO...")
    GPIO.cleanup()
