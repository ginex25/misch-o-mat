try:
    import RPi.GPIO as GPIO
    from HX711 import HX711
except (ImportError, RuntimeError):
    from mocks.RPi import GPIO
    from mocks.hx711 import HX711
