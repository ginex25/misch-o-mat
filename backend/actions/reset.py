import time

from core.logger import setup_logger
from hardware.stepper import home_stepper
from hardware.bridge import drive_away
from hardware.pump import pump_off

log = setup_logger()

def reset():
    pump_off()
    time.sleep(1)
    drive_away()
    time.sleep(1)
    home_stepper()
    log.info("Hardware reset")
