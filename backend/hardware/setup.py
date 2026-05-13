try:
    import RPi.GPIO as GPIO
except RuntimeError:
    import mocks.gpio as GPIO
import config.pins as pins


def setup_gpio():
    import hardware.scale
    GPIO.setmode(GPIO.BCM)

    # Button
    GPIO.setup(pins.BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Stepper
    GPIO.setup(pins.DIR_PIN, GPIO.OUT)
    GPIO.setup(pins.STEP_PIN, GPIO.OUT)
    GPIO.setup(pins.ENABLE_PIN, GPIO.OUT)
    GPIO.setup(pins.ENDSTOP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.output(pins.ENABLE_PIN, GPIO.LOW)

    # Bridge
    GPIO.setup(pins.LIN1, GPIO.OUT)
    GPIO.setup(pins.LIN2, GPIO.OUT)

    # Pump
    GPIO.setup(pins.PUMP_PIN, GPIO.OUT)


def clean_gpio():
    GPIO.cleanup()
