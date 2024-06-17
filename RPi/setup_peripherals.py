# setup_peripherals.py
import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD
from config import (
    BUTTON_PIN, PWR_BUTTON_PIN, RED_PIN, GREEN_PIN, BLUE_PIN,
    DIR_PIN, STEP_PIN, ENABLE_PIN, LCD_CONFIG
)

def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PWR_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(RED_PIN, GPIO.OUT)
    GPIO.setup(GREEN_PIN, GPIO.OUT)
    GPIO.setup(BLUE_PIN, GPIO.OUT)
    GPIO.setup(DIR_PIN, GPIO.OUT)
    GPIO.setup(STEP_PIN, GPIO.OUT)
    GPIO.setup(ENABLE_PIN, GPIO.OUT)
    GPIO.output(ENABLE_PIN, GPIO.HIGH)  # Disable stepper motor driver initially

def cleanup_gpio():
    GPIO.cleanup()

def initialize_lcd():
    return CharLCD(**LCD_CONFIG)
