import json
import os
try:
    from hx711 import HX711
except (RuntimeError, ImportError):
    from mocks.hardware.scale import HX711
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    import mocks.gpio as GPIO
import time

GPIO.setmode(GPIO.BCM)

config_path = os.path.join(os.path.dirname(__file__), '../config/scale.json')
with open(config_path, 'r') as config_file:
    config = json.load(config_file)
    ratio = config["RATIO"]

hx = HX711(dout_pin=23, pd_sck_pin=24, gain_channel_A=64)
hx.zero(1)
hx.set_scale_ratio(ratio)


def setup_scale():
    GPIO.setmode(GPIO.BCM)
    hx = HX711(dout_pin=23, pd_sck_pin=24, gain_channel_A=64)
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


def scale(target_weight, trailing):
    setup_scale()
    weight = 0
    previous_weight = 0
    max_increase = 100
    print("Scaling for " + str(target_weight) + "g")
    start_time = time.time()
    false_count = 0

    while weight < target_weight:
        elapsed_time = time.time() - start_time

        if elapsed_time >= 20:
            raise TimeoutError("Scaling operation timed out after 10 seconds")

        current_weight = hx.get_weight_mean(1)
        current_weight = current_weight
        
        if current_weight is False:
            false_count += 1
            if false_count >= 5:
                raise ValueError("Error: Scale returned an invalid value.")
            continue

        false_count = 0
        
        if not trailing:
            if abs(current_weight - previous_weight) <= max_increase:
                weight = current_weight
                previous_weight = weight
                print(weight)
        else:
            weight = current_weight
            previous_weight = weight
            print(weight)
