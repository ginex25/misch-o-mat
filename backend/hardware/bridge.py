from core.logger import setup_logger

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    import mocks.gpio as GPIO

import time

from config.pins import LIN1, LIN2

pause_duration = 0.3

log = setup_logger()

def drive_up():
    try:
        GPIO.output(LIN1, GPIO.LOW)
        GPIO.output(LIN2, GPIO.HIGH)
        time.sleep(pause_duration)
        GPIO.output(LIN1, GPIO.LOW)
        GPIO.output(LIN2, GPIO.LOW)
        log.info("Bridge driven up")
    except Exception:
        log.exception("Error during driving up")


def drive_away():
    try:
        GPIO.output(LIN1, GPIO.HIGH)
        GPIO.output(LIN2, GPIO.LOW)
        time.sleep(pause_duration)
        GPIO.output(LIN1, GPIO.LOW)
        GPIO.output(LIN2, GPIO.LOW)
        log.info("Bridge driven away")
    except Exception:
        log.exception("Error during driving away")
