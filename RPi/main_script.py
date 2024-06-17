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

GPIO.setmode(GPIO.BCM)

# GPIO and Peripheral Setup
button_pin = 20  # GPIO 20 for scan button
start_button_pin = 25  # GPIO 25 for start button
red_pin = 13  # GPIO 13 for RGB LED (Red)
green_pin = 6  # GPIO 6 for RGB LED (Green)
blue_pin = 5  # GPIO 5 for RGB LED (Blue)

# Stepper Motor Setup
DIR_PIN = 17  # GPIO 17
STEP_PIN = 27  # GPIO 27
ENABLE_PIN = 22  # GPIO 22

# LCD Display Setup
lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=2, charmap='A00', auto_linebreaks=True)

# System State Variables
classification_complete = False
current_bin_position = 1  # Default bin position

# Initialize GPIO
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(start_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(red_pin, GPIO.OUT)
GPIO.setup(green_pin, GPIO.OUT)
GPIO.setup(blue_pin, GPIO.OUT)

# Stepper Motor Initialization
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(STEP_PIN, GPIO.OUT)
GPIO.setup(ENABLE_PIN, GPIO.OUT)
GPIO.output(ENABLE_PIN, GPIO.HIGH)  # Disable stepper motor driver initially

# YOLO and Roboflow Setup
script_dir = os.path.dirname(os.path.realpath(__file__))
model_path = os.path.join(script_dir, 'yolo_finetuned.pt')
yolo_model = YOLO(model_path)

roboflow_api_url = "https://detect.roboflow.com"
roboflow_api_key = "jVDDnNjzY9vikw8mBH65"
roboflow_model_id = "projectone-classification/2"

# Directory for Captured Images
img_dir = os.path.join(script_dir, 'captured_images')
os.makedirs(img_dir, exist_ok=True)

# CSV File Path
csv_file_path = '/home/user/2023-2024-projectone-ctai-sirbucezar/RPi/bin_logs.csv'

# Bin Mapping
bin_mapping = {
    'Glass': 1,
    'PMD': 2,
    'Paper': 3,
    'Rest': 4
}

# RGB LED Control Functions
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

def blink_yellow_until_complete():
    global classification_complete
    while not classification_complete:
        set_rgb_color(1, 1, 0)  # Yellow
        time.sleep(0.5)
        set_rgb_color(0, 0, 0)
        time.sleep(0.5)

# LCD Display Control
def display_on_lcd(message_line1, message_line2=""):
    lcd.clear()
    lcd.write_string(message_line1.ljust(16))
    if message_line2:
        lcd.write_string('\r\n')
        lcd.write_string(message_line2.ljust(16))

# Internet Connection Check
def check_internet_connection(url='http://www.google.com/', timeout=1):
    try:
        requests.head(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        return False

# Initialize CSV File
def initialize_csv_file(file_path):
    if not os.path.exists(file_path):
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['prediction_id', 'bin_nr', 'accuracy'])

# Get Next Prediction ID for CSV Logging
def get_next_prediction_id(file_path):
    if not os.path.exists(file_path):
        return 1
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        rows = list(reader)
        if len(rows) == 1:
            return 1
        return len(rows)

# Capture Image Using libcamera-still
def capture_image():
    img_path = os.path.join(img_dir, 'captured_image.jpg')
    capture_command = ['libcamera-still', '-o', img_path, '--timeout', '1000']
    subprocess.run(capture_command)
    if os.path.exists(img_path):
        print(f"Image captured and saved to {img_path}")
    else:
        print("Failed to capture image.")
    return img_path

# Process Image with YOLO and Classify Detected Object
def process_image(img_path):
    print(f"Processing image: {img_path}")
    if not os.path.exists(img_path):
        print(f"Image path does not exist: {img_path}")
        return None, None, None

    img = cv2.imread(img_path)
    if img is None:
        print(f"Failed to load image from path: {img_path}")
        return None, None, None

    # Define the coordinates for the crop area based on the rectangle in the wooden platform
    top_left_x = 600
    top_left_y = 0
    bottom_right_x = 1900
    bottom_right_y = 1900

    # Crop the image to the specified area
    cropped_img = img[top_left_y:bottom_right_y, top_left_x:bottom_right_x]

    # Save the cropped image for verification
    cropped_img_path = os.path.join(img_dir, 'cropped_image.jpg')
    cv2.imwrite(cropped_img_path, cropped_img)
    print(f"Cropped image saved to {cropped_img_path}")

    # Proceed with YOLO object detection on the cropped image
    predictions = yolo_model.predict(source=cropped_img, save=False)

    if not predictions or not predictions[0].boxes:
        return None, None, None

    boxes = predictions[0].boxes.xyxy
    confs = predictions[0].boxes.conf
    cls = predictions[0].boxes.cls

    max_confidence_index = np.argmax(confs)
    box = boxes[max_confidence_index]
    confidence = confs[max_confidence_index]
    label = yolo_model.names[int(cls[max_confidence_index])]

    x1, y1, x2, y2 = map(int, box)
    cv2.rectangle(cropped_img, (x1, y1), (x2, y2), (255, 0, 0), 2)
    cv2.putText(cropped_img, f"{label} {confidence:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    output_img_path = os.path.join(img_dir, 'processed_image_with_boxes.jpg')
    cv2.imwrite(output_img_path, cropped_img)

    # Further crop to the detected object's bounding box if needed
    cropped_detected_img_path = os.path.join(img_dir, 'cropped_detected_image.png')
    detected_obj_img = cropped_img[y1:y2, x1:x2]
    cv2.imwrite(cropped_detected_img_path, detected_obj_img)

    return cropped_detected_img_path, label, confidence

# Classify Cropped Image Using Roboflow
def classify_cropped_object(cropped_img_path):
    print(f"Classifying cropped image: {cropped_img_path}")
    if not os.path.exists(cropped_img_path):
        print(f"Cropped image path does not exist: {cropped_img_path}")
        return None, None

    img = cv2.imread(cropped_img_path)
    if img is None:
        print(f"Failed to load cropped image from path: {cropped_img_path}")
        return None, None

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

# Log Prediction to CSV
def log_prediction(material_type, accuracy, file_path):
    prediction_id = get_next_prediction_id(file_path)
    bin_nr = bin_mapping.get(material_type, -1)
    accuracy_percentage = accuracy * 100

    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([prediction_id, bin_nr, f'{accuracy_percentage:.2f}'])

# Initialization Sequence
def initialize_system():
    display_on_lcd('INITIATION...')
    set_rgb_color(1, 0, 1)  # Purple
    blink_rgb_color(1, 0, 1, 5)  # Blink purple for 5 seconds during initialization
    connected = check_internet_connection()
    if not connected:
        display_on_lcd('No Internet', 'Check Connection')
        blink_rgb_color(1, 0, 0, 5, blink_rate=1)  # Flash red for error
        return False
    camera_working = True  # Assuming the camera is working
    if not camera_working:
        display_on_lcd('Camera Error', 'Check Device')
        blink_rgb_color(1, 0, 0, 5, blink_rate=1)  # Flash red for error
        return False
    display_on_lcd('Ready to Scan!', 'Press the button')
    set_rgb_color(0, 1, 0)  # Green
    global current_bin_position
    current_bin_position = read_last_bin_position(csv_file_path)
    return True

# Function to Read Last Bin Position from CSV
def read_last_bin_position(file_path):
    if not os.path.exists(file_path):
        return 1  # Default position if no file exists

    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        rows = list(reader)
        if len(rows) > 1:
            last_row = rows[-1]
            return int(last_row[1])
    return 1

# Function to Move Stepper Motor to Target Bin Position
def move_to_bin_position(target_bin):
    global current_bin_position

    print(f"Current Bin Position: {current_bin_position}, Target Bin Position: {target_bin}")

    if current_bin_position == target_bin:
        print("Already at the target bin. No movement required.")
        return

    GPIO.output(ENABLE_PIN, GPIO.LOW)  # Enable the stepper motor driver

    steps_per_bin = 170  # Steps to move from one bin to the next
    steps_needed = ((target_bin - current_bin_position) % 4) * steps_per_bin

    # Determine the direction based on the shortest path and invert the direction logic
    if steps_needed > 340:  # More than half a rotation (340 steps = 2 bins)
        steps_needed = 680 - steps_needed  # Total steps in a full rotation minus the steps needed
        direction = GPIO.HIGH  # Rotate in the given direction (invert)
    else:
        direction = GPIO.LOW  # Rotate in the opposite direction (invert)

    GPIO.output(DIR_PIN, direction)
    print(f"Moving {'clockwise' if direction == GPIO.HIGH else 'counter-clockwise'} by {steps_needed} steps.")

    for step in range(steps_needed):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(0.005)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(0.005)
        if step % 10 == 0:
            print(f"Step {step + 1} / {steps_needed}")

    time.sleep(0.5)  # Add a delay to account for inertia

    GPIO.output(ENABLE_PIN, GPIO.HIGH)  # Disable the stepper motor driver

    current_bin_position = target_bin  # Update the current bin position
    print(f"New Bin Position: {current_bin_position}")

# Main Loop Controlled by the Start Button
def main_loop():
    global classification_complete

    while True:
        try:
            if GPIO.input(button_pin) == GPIO.LOW:
                display_on_lcd('Press Start Button')
                set_rgb_color(0, 1, 0)  # Green
                while GPIO.input(start_button_pin) == GPIO.HIGH:
                    time.sleep(0.1)

                display_on_lcd('Processing...', '')  # Clear second line for loading bar
                classification_complete = False

                # Start flashing yellow LED
                threading.Thread(target=blink_yellow_until_complete).start()

                # Processing Stage
                img_path = capture_image()
                cropped_img_path, label, detection_confidence = process_image(img_path)

                if cropped_img_path is not None:
                    display_on_lcd('Classifying...', '')  # Clear second line for loading bar
                    classified_material, classification_confidence = classify_cropped_object(cropped_img_path)

                    if classified_material and classification_confidence is not None:
                        log_prediction(classified_material, classification_confidence, csv_file_path)

                        classification_complete = True  # This will stop the yellow blinking

                        display_on_lcd(f'Material: {classified_material[:8]}', f'Accuracy: {classification_confidence:.2%}')
                        time.sleep(5)

                        target_bin = bin_mapping.get(classified_material, 1)
                        move_to_bin_position(target_bin)

                        # Flash faster green for 5 times then steady green
                        for _ in range(5):
                            set_rgb_color(0, 1, 0)
                            time.sleep(0.1)
                            set_rgb_color(0, 0, 0)
                            time.sleep(0.1)
                        set_rgb_color(0, 1, 0)  # Steady green
                        display_on_lcd('Throw it :)', 'and scan again')

                    else: 
                        display_on_lcd('Error', 'No classification')
                        set_rgb_color(1, 0, 0)  # Red for error
                        time.sleep(2)
                        classification_complete = True  # Stop yellow blinking on error

                else:
                    display_on_lcd('Error', 'No detection')
                    set_rgb_color(1, 0, 0)  # Red for error
                    time.sleep(2)
                    classification_complete = True  # Stop yellow blinking on error

                classification_complete = True  # Ensure yellow blinking stops after each cycle

        except Exception as e:
            print(f"An error occurred: {e}")
            display_on_lcd('Error Occurred')
            set_rgb_color(1, 0, 0)  # Red for error
            time.sleep(2)

# Initialization and Main Execution
initialize_csv_file(csv_file_path)

if initialize_system():
    try:
        main_loop()
    except KeyboardInterrupt:
        lcd.clear()
        GPIO.cleanup()
        GPIO.output(DIR_PIN, GPIO.LOW)
        GPIO.output(STEP_PIN, GPIO.LOW)
        GPIO.output(ENABLE_PIN, GPIO.HIGH)
        GPIO.cleanup()
