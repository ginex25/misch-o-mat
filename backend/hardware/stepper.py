import time

from core.logger import setup_logger
from database.calibration import get_offset

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    import mocks.gpio as GPIO
import config.pins as pins

HOME_OFFSET = 55
STEPS_PER_REVOLUTION = 3200
STEPS_PER_HOLE = 160  # 3200/360 = 8,89 Schritte pro Grad /// 360/20 = 18 Grad pro Loch /// 18 * 8,89 = 160

log = setup_logger()


def _step(delay_high: float = 0.0002, delay_low: float = 0.001):
    GPIO.output(pins.STEP_PIN, GPIO.HIGH)
    time.sleep(delay_high)
    GPIO.output(pins.STEP_PIN, GPIO.LOW)
    time.sleep(delay_low)


def home_stepper():
    try:
        log.info("Homing stepper...")
        GPIO.output(pins.DIR_PIN, GPIO.LOW)
        while GPIO.input(pins.ENDSTOP_PIN) == GPIO.HIGH:
            _step()

        GPIO.output(pins.DIR_PIN, GPIO.HIGH)

        for i in range(HOME_OFFSET):
            _step()
    except Exception:
        log.exception("Error during homing")


def move_to_hole(start, target):
    try:
        start_position = get_offset(start)
        target_position = get_offset(target)
        log.info(f"Moving from position {start_position} to {target_position}...")

        target_steps = (target_position - start_position) * STEPS_PER_HOLE

        if target_steps >= 0:
            GPIO.output(pins.DIR_PIN, GPIO.HIGH)
        else:
            GPIO.output(pins.DIR_PIN, GPIO.LOW)

        for i in range(abs(target_steps)):
            if GPIO.input(pins.ENDSTOP_PIN) == GPIO.LOW:
                home_stepper()
                return
            _step(delay_low=0.0002)
    except Exception:
        log.exception("Error during moving")


def move_by_steps(steps: int):
    try:
        if steps == 0:
            return

        log.info(f"Moving {steps} steps...")
        if steps > 0:
            GPIO.output(pins.DIR_PIN, GPIO.HIGH)
        else:
            GPIO.output(pins.DIR_PIN, GPIO.LOW)

        for i in range(abs(steps)):
            if GPIO.input(pins.ENDSTOP_PIN) == GPIO.LOW:
                log.warning("Endstop reached during step movement, homing...")
                home_stepper()
                return
            _step(delay_low=0.0002)
    except Exception:
        log.exception("Error during step movement")
