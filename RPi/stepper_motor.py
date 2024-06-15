import time
import RPi.GPIO as GPIO
import config

# GPIO Setup for Stepper Motor
GPIO.setup(config.DIR_PIN, GPIO.OUT)
GPIO.setup(config.STEP_PIN, GPIO.OUT)
GPIO.setup(config.ENABLE_PIN, GPIO.OUT)
GPIO.output(config.ENABLE_PIN, GPIO.HIGH)  # Disable stepper motor driver initially

current_bin_position = config.current_bin_position

def move_to_bin_position(target_bin):
    """Moves the stepper motor to the target bin position."""
    global current_bin_position

    if current_bin_position == target_bin:
        return

    GPIO.output(config.ENABLE_PIN, GPIO.LOW)  # Enable the stepper motor driver

    steps_per_bin = 170  # Steps to move from one bin to the next
    steps_needed = ((target_bin - current_bin_position) % 4) * steps_per_bin

    if steps_needed > 340:  # More than half a rotation (340 steps = 2 bins)
        steps_needed = 680 - steps_needed  # Total steps in a full rotation minus the steps needed
        direction = GPIO.HIGH  # Rotate in the given direction
    else:
        direction = GPIO.LOW  # Rotate in the opposite direction

    GPIO.output(config.DIR_PIN, direction)
    for step in range(steps_needed):
        GPIO.output(config.STEP_PIN, GPIO.HIGH)
        time.sleep(0.005)
        GPIO.output(config.STEP_PIN, GPIO.LOW)
        time.sleep(0.005)

    time.sleep(0.5)  # delay to account for inertia

    GPIO.output(config.ENABLE_PIN, GPIO.HIGH)  # Disable the stepper motor driver

    current_bin_position = target_bin  # Update the current bin position
