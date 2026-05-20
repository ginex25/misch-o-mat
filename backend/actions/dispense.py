import json
import os
from typing import Dict

from actions.reset import reset
from core.logger import setup_logger
from hardware.bridge import drive_up, drive_away
from hardware.pump import pump_off, pump_on
from hardware.scale import scale, scale_single, tare
from hardware.stepper import move_to_hole, home_stepper

log = setup_logger()


def load_liquids_database(file_path="/home/misch-o-mat/misch-o-mat/backend/database/liquids.json"):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    file_path = os.path.join(backend_dir, "database", "liquids.json")

    with open(file_path, "r") as file:
        return json.load(file)


def dispense_drink(ingredients: Dict[str, float]) -> Dict[str, float]:
    start_position = 0
    liquids_data = load_liquids_database()

    dispense_amounts = {}

    try:
        for ingredient_id, amount in ingredients.items():
            target_position = liquids_data[ingredient_id]["anschlussplatz"]

            tare()
            move_to_hole(start_position, target_position)
            drive_up()

            pump_on()
            actual = scale(amount)
            pump_off()

            dispense_amounts[ingredient_id] = actual

            drive_away()

            last_weight = scale_single()
            log.debug(f"last_weight: {last_weight}")
            start_position = target_position
    except Exception as e:
        log.exception("Error during dispensing")
        reset()
        raise e

    home_stepper()
    log.info("Dispensing finished")
    return dispense_amounts
