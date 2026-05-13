from core.logger import setup_logger

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    import mocks.gpio as GPIO

from config.pins import PUMP_PIN

log = setup_logger()

def pump_on():
    try:
        GPIO.output(PUMP_PIN, GPIO.HIGH)
        log.info("Pump on")
    except Exception:
        log.exception("Error while turning pump on")


def pump_off():
    try:
        GPIO.output(PUMP_PIN, GPIO.LOW)
        log.info("Pump off")
    except Exception:
        log.exception("Error while turning pump off")
