import os
import time
import threading
import config
import csv
from utils import (set_rgb_color, blink_rgb_color, blink_yellow_until_complete,
                   display_on_lcd, check_internet_connection, initialize_csv_file, log_prediction)
from image_processing import capture_image, process_image
from roboflow_api import classify_cropped_object
from stepper_motor import move_to_bin_position
import RPi.GPIO as GPIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# System State Variables
classification_complete = False
current_bin_position = config.current_bin_position

def initialize_system():
    """Initializes the system and checks for internet and camera readiness."""
    display_on_lcd('INITIATION...')
    set_rgb_color(1, 0, 1)  # Purple
    blink_rgb_color(1, 0, 1, 5)  # Blink purple for 5 seconds during initialization
    connected = check_internet_connection()
    if not connected:
        display_on_lcd('No Internet', 'Check Connection')
        blink_rgb_color(1, 0, 0, 5, blink_rate=1)  # Flash red for error
        return False
    display_on_lcd('Ready to Scan!', 'Press the button')
    set_rgb_color(0, 1, 0)  # Green
    global current_bin_position
    current_bin_position = read_last_bin_position(config.csv_file_path)
    return True

def read_last_bin_position(file_path):
    """Reads the last bin position from the CSV file."""
    if not os.path.exists(file_path):
        return 1  # Default position if no file exists

    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        rows = list(reader)
        if len(rows) > 1:
            last_row = rows[-1]
            return int(last_row[1])
    return 1

def main_loop():
    """Main loop that waits for button press to start the classification process."""
    global classification_complete

    while True:
        try:
            if GPIO.input(config.button_pin) == GPIO.LOW:
                display_on_lcd('Press Start Button')
                set_rgb_color(0, 1, 0)  # Green
                while GPIO.input(config.start_button_pin) == GPIO.HIGH:
                    time.sleep(0.1)

                display_on_lcd('Processing...' , 'Please wait')
                classification_complete = False

                # Start flashing yellow LED
                threading.Thread(target=blink_yellow_until_complete, args=(classification_complete,)).start()

                # Processing Stage
                img_path = capture_image(config.img_dir)
                cropped_img_path, label, detection_confidence = process_image(img_path)

                if cropped_img_path is not None:
                    display_on_lcd('Classifying...', 'Just a bit more')
                    classified_material, classification_confidence = classify_cropped_object(cropped_img_path)

                    if classified_material and classification_confidence is not None:
                        log_prediction(classified_material, classification_confidence, config.csv_file_path)

                        classification_complete = True  # This will stop the yellow blinking

                        display_on_lcd(f'Material: {classified_material[:8]}', f'Accuracy: {classification_confidence:.2%}')
                        time.sleep(5)

                        target_bin = config.bin_mapping.get(classified_material, 1)
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
initialize_csv_file(config.csv_file_path)

if initialize_system():
    try:
        main_loop()
    except KeyboardInterrupt:
        display_on_lcd("System OFF")
        GPIO.cleanup()
        GPIO.output(config.DIR_PIN, GPIO.LOW)
        GPIO.output(config.STEP_PIN, GPIO.LOW)
        GPIO.output(config.ENABLE_PIN, GPIO.HIGH)
        GPIO.cleanup()
