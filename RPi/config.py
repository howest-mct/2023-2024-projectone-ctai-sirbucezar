# GPIO Pins
button_pin = 20
start_button_pin = 25
red_pin = 13
green_pin = 6
blue_pin = 5
DIR_PIN = 17
STEP_PIN = 27
ENABLE_PIN = 22

# LCD Configuration
lcd_address = 0x27
lcd_cols = 16
lcd_rows = 2

# Image Crop Coordinates | Adjusted for the camera position according to the identification box on top of the bin. Adjust as needed.
top_left_x = 600
top_left_y = 0
bottom_right_x = 1900
bottom_right_y = 1900

# YOLO Model Path
yolo_model_path = '/home/user/2023-2024-projectone-ctai-sirbucezar/RPi/yolo_finetuned.pt'

# CSV File Path
csv_file_path = '/home/user/2023-2024-projectone-ctai-sirbucezar/RPi/bin_logs.csv'

# Bin Mapping
bin_mapping = {
    'Glass': 1,
    'PMD': 2,
    'Paper': 3,
    'Rest': 4
}

# Initial bin position
current_bin_position = 1 # Default position is 1 - Glass
