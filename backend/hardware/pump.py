from config.pins import PUMP_PIN
from core.logger import setup_logger
from hardware import GPIO

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
