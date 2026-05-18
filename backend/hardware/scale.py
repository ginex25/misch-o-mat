import json
import os

from config.pins import DOUT_PIN, PD_SCK_PIN, GAIN_CHANNEL_A
from core.logger import setup_logger
from hardware import GPIO, HX711
from hardware.setup import setup_gpio

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


def test_scale():
    setup_scale()

    while True:
        weight = hx.get_weight_mean(1)
        print(weight)


import time


def scale(target_weight, trailing, threshold=2, timeout=3) -> float:
    setup_scale()
    weight = 0
    previous_weight = 0
    max_increase = 100
    log.info(f"Starting scaling operation for target weight: {target_weight}g")
    false_count = 0
    weight_error_count = 0
    height_weight_error = 0
    last_height_weight = 0

    last_check_time = time.time()
    last_check_weight = 0

    while weight < target_weight:
        if false_count >= 5 or weight_error_count >= 5 or height_weight_error >= 5:
            raise ValueError("Error: Scale returned an invalid or negative value.")

        current_weight = hx.get_weight_mean(1)
        log.debug(f"first cur weight: {current_weight}")

        if current_weight is False or (isinstance(current_weight, (int, float)) and current_weight < 0):
            false_count += 1
            log.debug("FEHLER (Ungültiger oder negativer Wert)")
            continue

        if current_weight < last_check_weight:
            weight_error_count += 1
            log.debug("current_weight < last_weight")
            continue

        if current_weight - last_height_weight > threshold and height_weight_error >= 4:
            last_check_weight = last_height_weight

        if (current_weight - last_check_weight) > 50:
            height_weight_error += 1
            last_height_weight = current_weight
            log.debug("current weight to height")
            continue

        false_count = 0
        weight_error_count = 0
        height_weight_error = 0

        elapsed_since_check = time.time() - last_check_time
        if elapsed_since_check >= timeout:
            if (current_weight - last_check_weight) < threshold:
                raise TimeoutError(f"Scale stalled: weight increased by less than {threshold}g in {timeout} seconds")
            last_check_time = time.time()

        last_check_weight = current_weight
        weight = last_check_weight

    return weight


def scale_single() -> float:
    return hx.get_weight_mean(1)


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


if __name__ == '__main__':
    setup_gpio()
    test_scale()
