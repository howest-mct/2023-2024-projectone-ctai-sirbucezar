import os
import cv2
import csv
import time
import requests
import threading
from ultralytics import YOLO
import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD

# Set the display environment variable
os.environ['DISPLAY'] = ':0'

# Determine the script's directory
script_dir = os.path.dirname(os.path.realpath(__file__))

# Construct full paths
model_path = os.path.join(script_dir, 'yolo_finetuned.pt')
img_dir = os.path.join(script_dir, 'captured_images')

# Ensure the image directory exists
os.makedirs(img_dir, exist_ok=True)

# Debug: Print current working directory and paths
print(f"Current working directory: {os.getcwd()}")
print(f"Model path: {model_path}")
print(f"Image directory: {img_dir}")

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

def check_internet_connection(url='http://www.google.com/', timeout=3):
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

def crop_center(image, new_width, new_height):
    height, width, _ = image.shape
    startx = width // 2 - new_width // 2
    starty = height // 2 - new_height // 2
    return image[starty:starty + new_height, startx:startx + new_width]

def process_frame(frame):
    # Crop the center of the frame
    cropped_frame = crop_center(frame, 640, 480)  # Adjust the cropping dimensions as needed
    predictions = model.predict(source=cropped_frame, save=False)

    if len(predictions) == 0 or len(predictions[0].boxes) == 0:
        return cropped_frame, None, None

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
        # Draw the bounding box on the cropped frame
        x1, y1, x2, y2 = map(int, boxes[i])
        cv2.rectangle(cropped_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(cropped_frame, f"{label} {confidence:.2f}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    if classifications and accuracies:
        max_confidence_index = accuracies.index(max(accuracies))
        material_type = classifications[max_confidence_index]
        accuracy = accuracies[max_confidence_index]
        return cropped_frame, material_type, accuracy

    return cropped_frame, None, None

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

# Capture image from webcam
def capture_image():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        display_on_lcd("Camera Error")
        return None

    print("Press GPIO button to capture an image.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            display_on_lcd("Capture Error")
            break

        cv2.imshow('Capture Image', frame)

        button_state = GPIO.input(button_pin)
        if button_state == GPIO.LOW:
            # Debounce the button press
            time.sleep(0.1)
            if GPIO.input(button_pin) == GPIO.LOW:
                img_path = os.path.join(img_dir, 'captured_image.png')
                cv2.imwrite(img_path, frame)
                break

        if cv2.waitKey(1) & 0xFF == ord('q'):  # Allow quitting the capture with 'q'
            break

    cap.release()
    cv2.destroyAllWindows()
    return img_path

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

# Main processing function
def capture_and_process():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        display_on_lcd("Camera Error")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set frame width
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Set frame height
    cap.set(cv2.CAP_PROP_FPS, 30)  # Set frame rate

    print("Press GPIO button to capture the result.")
    material_type, accuracy = None, None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            display_on_lcd("Capture Error")
            break

        frame, material_type, accuracy = process_frame(frame)
        cv2.imshow('Capture Image', frame)

        button_state = GPIO.input(button_pin)
        if button_state == GPIO.LOW:
            # Debounce the button press
            time.sleep(0.1)
            if GPIO.input(button_pin) == GPIO.LOW:
                img_path = os.path.join(img_dir, 'captured_image.png')
                cv2.imwrite(img_path, frame)
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
                break

        if cv2.waitKey(1) & 0xFF == ord('q'):  # Allow quitting the capture with 'q'
            break

    cap.release()
    cv2.destroyAllWindows()

# Initialize the CSV file with headers
initialize_csv_file(csv_file_path)

# Main loop
try:
    initialize_system()
    capture_and_process()  # Start the capture and processing function
finally:
    # Clean up GPIO pins before exiting
    GPIO.cleanup()
