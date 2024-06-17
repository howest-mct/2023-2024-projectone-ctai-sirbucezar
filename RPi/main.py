# main.py
import threading
import os
import csv
import time
import RPi.GPIO as GPIO
from config import BIN_MAPPING, CSV_FILE_PATH, BUTTON_PIN, PWR_BUTTON_PIN, STEP_PIN, DIR_PIN, ENABLE_PIN
from setup_peripherals import setup_gpio, cleanup_gpio, initialize_lcd
from utils import set_rgb_color, blink_rgb_color, display_on_lcd, check_internet_connection, initialize_csv_file, log_prediction
from image_processing import capture_image, process_image, classify_cropped_object

# Global Variables
classification_complete = False
current_bin_position = 1  # Default bin position

# Initialize GPIO and LCD
setup_gpio()
lcd = initialize_lcd()

def initialize_system():
    display_on_lcd(lcd, 'INITIATION...')
    set_rgb_color(1, 0, 1)  # Purple
    blink_rgb_color(1, 0, 1, 5)  # Blink purple for 5 seconds during initialization
    connected = check_internet_connection()
    if not connected:
        display_on_lcd(lcd, 'No Internet', 'Check Connection')
        blink_rgb_color(1, 0, 0, 5, blink_rate=1)  # Flash red for error
        return False
    camera_working = True  # Assuming the camera is working
    if not camera_working:
        display_on_lcd(lcd, 'Camera Error', 'Check Device')
        blink_rgb_color(1, 0, 0, 5, blink_rate=1)  # Flash red for error
        return False
    display_on_lcd(lcd, 'Ready to Scan!', 'Press the button')
    set_rgb_color(0, 1, 0)  # Green
    global current_bin_position
    current_bin_position = read_last_bin_position(CSV_FILE_PATH)
    return True

def read_last_bin_position(file_path=CSV_FILE_PATH):
    if not os.path.exists(file_path):
        return 1  # Default position if no file exists

    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        rows = list(reader)
        if len(rows) > 1:
            last_row = rows[-1]
            return int(last_row[1])
    return 1

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

def blink_yellow_until_complete():
    global classification_complete
    while not classification_complete:
        set_rgb_color(1, 1, 0)  # Yellow
        time.sleep(0.5)
        set_rgb_color(0, 0, 0)
        time.sleep(0.5)

# Main Loop Controlled by the Start Button
def main_loop():
    global classification_complete

    while True:
        try:
            if GPIO.input(BUTTON_PIN) == GPIO.LOW:
                display_on_lcd(lcd, 'Press Start Button')
                set_rgb_color(0, 1, 0)  # Green
                while GPIO.input(PWR_BUTTON_PIN) == GPIO.HIGH:
                    time.sleep(0.1)

                display_on_lcd(lcd, 'Processing...', '')  # Clear second line for loading bar
                classification_complete = False

                # Start flashing yellow LED
                threading.Thread(target=blink_yellow_until_complete).start()

                # Processing Stage
                img_path = capture_image()
                cropped_img_path = process_image(img_path)

                if cropped_img_path:
                    display_on_lcd(lcd, 'Classifying...', '')  # Clear second line for loading bar
                    classified_material, classification_confidence = classify_cropped_object(cropped_img_path)

                    if classified_material and classification_confidence is not None:
                        log_prediction(classified_material, classification_confidence, CSV_FILE_PATH)

                        classification_complete = True  # This will stop the yellow blinking

                        display_on_lcd(lcd, f'Material: {classified_material[:8]}', f'Accuracy: {classification_confidence:.2%}')
                        time.sleep(5)

                        target_bin = BIN_MAPPING.get(classified_material, 1)
                        move_to_bin_position(target_bin)

                        # Flash faster green for 5 times then steady green
                        for _ in range(5):
                            set_rgb_color(0, 1, 0)
                            time.sleep(0.1)
                            set_rgb_color(0, 0, 0)
                            time.sleep(0.1)
                        set_rgb_color(0, 1, 0)  # Steady green
                        display_on_lcd(lcd, 'Throw it :)', 'and scan again')

                    else:
                        display_on_lcd(lcd, 'Error', 'No classification')
                        set_rgb_color(1, 0, 0)  # Red for error
                        time.sleep(2)
                        classification_complete = True  # Stop yellow blinking on error

                else:
                    display_on_lcd(lcd, 'Error', 'No detection')
                    set_rgb_color(1, 0, 0)  # Red for error
                    time.sleep(2)
                    classification_complete = True  # Stop yellow blinking on error

                classification_complete = True  # Ensure yellow blinking stops after each cycle

        except Exception as e:
            print(f"An error occurred: {e}")
            display_on_lcd(lcd, 'Error Occurred')
            set_rgb_color(1, 0, 0)  # Red for error
            time.sleep(2)

# Initialization and Main Execution
initialize_csv_file()  # Use default CSV_FILE_PATH

if initialize_system():
    try:
        main_loop()
    except KeyboardInterrupt:
        lcd.clear()
        cleanup_gpio()
        GPIO.output(DIR_PIN, GPIO.LOW)
        GPIO.output(STEP_PIN, GPIO.LOW)
        GPIO.output(ENABLE_PIN, GPIO.HIGH)
        cleanup_gpio()
