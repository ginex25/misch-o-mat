import time

import config.pins as pins
from core.logger import setup_logger
from database.calibration import get_offset
from hardware import GPIO

HOME_OFFSET = 55
STEPS_PER_REVOLUTION = 3200
STEPS_PER_HOLE = 160  # 3200/360 = 8,89 Schritte pro Grad /// 360/20 = 18 Grad pro Loch /// 18 * 8,89 = 160

MIN_DELAY = 0.0008
MAX_DELAY = 0.004
RAMP_STEPS = 200

log = setup_logger()


def _step(delay: float):
    half = delay / 2
    GPIO.output(pins.STEP_PIN, GPIO.HIGH)
    time.sleep(half)
    GPIO.output(pins.STEP_PIN, GPIO.LOW)
    time.sleep(half)


def _compute_ramp(total_steps: int) -> list[float]:
    ramp = min(RAMP_STEPS, total_steps // 2)
    delays = []

    for i in range(total_steps):
        if i < ramp:
            # speed up
            t = i / ramp
            delay = MAX_DELAY + (MIN_DELAY - MIN_DELAY) * t
        elif i >= total_steps - ramp:
            # slow down
            t = (total_steps - i) / ramp
            delay = MAX_DELAY + (MIN_DELAY - MIN_DELAY) * t
        else:
            # hold
            delay = MIN_DELAY
        delays.append(delay)

    return delays


def home_stepper():
    try:
        log.info("Homing stepper...")
        GPIO.output(pins.DIR_PIN, GPIO.LOW)
        while GPIO.input(pins.ENDSTOP_PIN) == GPIO.HIGH:
            _step(MAX_DELAY)

        GPIO.output(pins.DIR_PIN, GPIO.HIGH)

        for i in range(HOME_OFFSET):
            _step(MAX_DELAY)
    except Exception:
        log.exception("Error during homing")


def move_to_hole(start, target):
    try:
        start_position = get_offset(start)
        target_position = get_offset(target)
        log.info(f"Moving from position {start} (offset: {target_position}) to {target} (offset: {target_position})...")

        target_steps = (target_position - start_position) * STEPS_PER_HOLE

        if target_steps >= 0:
            GPIO.output(pins.DIR_PIN, GPIO.HIGH)
        else:
            GPIO.output(pins.DIR_PIN, GPIO.LOW)

        delays = _compute_ramp(abs(target_steps))

        for delay in delays:
            if GPIO.input(pins.ENDSTOP_PIN) == GPIO.LOW:
                log.warning("Endstop reached during hole movement, homing...")
                home_stepper()
                return
            _step(delay)
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

        delays = _compute_ramp(abs(steps))

        for delay in delays:
            if GPIO.input(pins.ENDSTOP_PIN) == GPIO.LOW:
                log.warning("Endstop reached during hole movement, homing...")
                home_stepper()
                return
            _step(delay)
    except Exception:
        log.exception("Error during step movement")
