import json
import os

from config.pins import DOUT_PIN, PD_SCK_PIN, GAIN_CHANNEL_A
from core.logger import setup_logger

try:
    from hx711 import HX711
except (RuntimeError, ImportError):
    from mocks.hardware.scale import HX711
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    import mocks.gpio as GPIO
import time

log = setup_logger()

GPIO.setmode(GPIO.BCM)

config_path = os.path.join(os.path.dirname(__file__), '../config/scale.json')
with open(config_path, 'r') as config_file:
    config = json.load(config_file)
    ratio = config["RATIO"]

hx = HX711(dout_pin=DOUT_PIN, pd_sck_pin=PD_SCK_PIN, gain_channel_A=GAIN_CHANNEL_A)
hx.zero(1)
hx.set_scale_ratio(ratio)


def setup_scale():
    GPIO.setmode(GPIO.BCM)
    global hx
    hx = HX711(dout_pin=DOUT_PIN, pd_sck_pin=PD_SCK_PIN, gain_channel_A=GAIN_CHANNEL_A)
    hx.zero(1)
    hx.set_scale_ratio(ratio)


def tare():
    setup_scale()
    hx.zero(1)


def calibrate(known_weight):
    setup_scale()
    reading = hx.get_data_mean(100)
    ratio = (reading / float(known_weight))
    hx.set_scale_ratio(ratio)

    config["RATIO"] = ratio
    with open(config_path, 'w') as config_file:
        json.dump(config, config_file)


def scale(target_weight, trailing, threshold=2) -> float:
    setup_scale()
    weight = 0
    previous_weight = 0
    max_increase = 100
    log.info(f"Starting scaling operation for target weight: {target_weight}g")
    false_count = 0

    last_check_time = time.time()
    last_check_weight = 0

    while weight < target_weight:
        current_weight = hx.get_weight_mean(1)

        if current_weight is False:
            false_count += 1
            if false_count >= 5:
                raise ValueError("Error: Scale returned an invalid value.")
            continue

        false_count = 0

        elapsed_since_check = time.time() - last_check_time
        if elapsed_since_check >= 2:
            if (current_weight - last_check_weight) < threshold:
                raise TimeoutError(f"Scale stalled: weight increased by less than {threshold}g in 2 seconds")
            last_check_time = time.time()
            last_check_weight = current_weight

        if not trailing:
            if abs(current_weight - previous_weight) <= max_increase:
                weight = current_weight
                previous_weight = weight
                log.debug(f"Current weight: {weight}g")
        else:
            weight = current_weight
            previous_weight = weight
            log.debug(f"Current weight: {weight}g")

    return weight


def wait_for_weight_increase(timeout: float = 3.0, threshold: float = 2.0, baseline: float | None = None,
                             poll_interval: float = 0.1) -> tuple[bool, float]:
    try:
        setup_scale()

        if baseline is None:
            baseline = hx.get_weight_mean(1)

        if baseline is False:
            baseline = 0

        start = time.time()
        last_weight = baseline

        while (time.time() - start) < timeout:
            w = hx.get_weight_mean(1)

            if w is False:
                time.sleep(poll_interval)
                continue

            log.debug(f"Current weight: {w}g")

            if (w - baseline) > threshold:
                return True, w

            last_weight = w

            time.sleep(poll_interval)

        return False, last_weight
    except Exception:
        log.exception("Error in wait_for_weight_increase")
        return False, baseline or 0.0
