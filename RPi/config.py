# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# GPIO Pins
BUTTON_PIN = 20
PWR_BUTTON_PIN = 25
RED_PIN = 13
GREEN_PIN = 6
BLUE_PIN = 5
DIR_PIN = 17
STEP_PIN = 27
ENABLE_PIN = 22

# LCD Configuration
LCD_CONFIG = {
    'i2c_expander': 'PCF8574',
    'address': 0x27,
    'port': 1,
    'cols': 16,
    'rows': 2,
    'charmap': 'A00',
    'auto_linebreaks': True
}

# YOLO Model Path
MODEL_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'yolo_finetuned.pt')

# Roboflow Configuration
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
ROBOFLOW_MODEL_ID = "p1-rh6ko/1"  # Replace with your actual model ID

# Ensure the API key and model ID are set
if not ROBOFLOW_API_KEY:
    raise ValueError("ROBOFLOW_API_KEY environment variable is not set or is None")
if not ROBOFLOW_MODEL_ID:
    raise ValueError("ROBOFLOW_MODEL_ID is not set or is None")

# CSV File Path
CSV_FILE_PATH = "/home/user/2023-2024-projectone-ctai-sirbucezar/RPi/bin_logs.csv"

# Bin Mapping
BIN_MAPPING = {
    'Glass': 1,
    'PMD': 2,
    'Paper': 3,
    'Rest': 4
}

# Directory for Captured Images
IMG_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'captured_images')
os.makedirs(IMG_DIR, exist_ok=True)
