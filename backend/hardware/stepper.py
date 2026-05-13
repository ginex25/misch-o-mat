import time

from core.logger import setup_logger

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    import mocks.gpio as GPIO
import config.pins as pins

steps_per_revolution = 3200
steps_per_hole = 160  # 3200/360 = 8,89 Schritte pro Grad /// 360/20 = 18 Grad pro Loch /// 18 * 8,89 = 160

log = setup_logger()

def home_stepper():
    try:
        log.info("Homing stepper...")
        GPIO.output(pins.DIR_PIN, GPIO.LOW)
        while GPIO.input(pins.ENDSTOP_PIN) == GPIO.HIGH:
            GPIO.output(pins.STEP_PIN, GPIO.HIGH)
            time.sleep(0.0002)
            GPIO.output(pins.STEP_PIN, GPIO.LOW)
            time.sleep(0.001)

        GPIO.output(pins.DIR_PIN, GPIO.HIGH)

        for i in range(55):
            GPIO.output(pins.STEP_PIN, GPIO.HIGH)
            time.sleep(0.0002)
            GPIO.output(pins.STEP_PIN, GPIO.LOW)
            time.sleep(0.001)
    except Exception:
        log.exception("Error during homing")


def map_position(input_position):
    if 1 <= input_position <= 9:
        return input_position + 4
    elif 10 <= input_position <= 14:
        return input_position - 10
    elif 15 <= input_position <= 19:
        return input_position - 1
    else:
        return 0


def move_to_hole(start, target):
    try:
        start_position = map_position(start)
        target_position = map_position(target)
        log.info(f"Moving from position {start_position} to {target_position}...")

        target_steps = (target_position - start_position) * steps_per_hole

        if target_steps >= 0:
            GPIO.output(pins.DIR_PIN, GPIO.HIGH)
        else:
            GPIO.output(pins.DIR_PIN, GPIO.LOW)

        for i in range(abs(target_steps)):
            if GPIO.input(pins.ENDSTOP_PIN) == GPIO.LOW:
                home_stepper()
                return
            GPIO.output(pins.STEP_PIN, GPIO.HIGH)
            time.sleep(0.0002)
            GPIO.output(pins.STEP_PIN, GPIO.LOW)
            time.sleep(0.0002)
    except Exception:
        log.exception("Error during moving")
