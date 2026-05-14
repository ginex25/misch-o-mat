import time

from core.logger import setup_logger
from hardware.bridge import drive_up, drive_away
from hardware.pump import pump_on, pump_off
from hardware.stepper import move_to_hole, home_stepper

log = setup_logger()


def clean_position(position):
    try:
        move_to_hole(0, position)
        drive_up()

        log.info(f"Cleaning position {position}")
        pump_on()
        time.sleep(10)
        pump_off()

        drive_away()
        home_stepper()

    except Exception:
        log.exception("Error during cleaning")
        pump_off()
        drive_away()

    log.info(f"Cleaning of Position {position} finished")
