import json
from enum import Enum
from pathlib import Path

from core.logger import setup_logger

_LONGDRINKS_PATH = Path(__file__).parent / "longdrinks.json"
_MIXDRINKS_PATH = Path(__file__).parent / "mixdrinks.json"

log = setup_logger()


class DrinkCategory(Enum):
    LONGDRINKS = "Longdrinks"
    MIXDRINKS = "Mischgetränke"


def get_by_name(drink_name: str, category: DrinkCategory) -> dict | None:
    filepath = _LONGDRINKS_PATH if category == DrinkCategory.LONGDRINKS else _MIXDRINKS_PATH

    try:
        with open(filepath, "r") as f:
            drinks_data = json.load(f)

        for drink_id, drink in drinks_data.items():
            if drink['name'] == drink_name:
                return drink
        return None
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log.error(f"Error loading drinks from {filepath}: {e}")
        raise


def update_total_amount(category: str, new_value: float) -> None:
    for filepath in [_LONGDRINKS_PATH, _MIXDRINKS_PATH]:
        try:
            with open(filepath, "r") as f:
                drinks_data = json.load(f)

            for drink_id in drinks_data:
                drinks_data[drink_id][category] = new_value

            _save(filepath, drinks_data)
            log.debug(f"Updated {category} in {filepath.name}")
        except Exception as e:
            log.error(f"Error updating drinks in {filepath}: {e}")
            raise


def _save(filepath: Path, drinks_data: dict) -> None:
    with open(filepath, "w") as f:
        json.dump(drinks_data, f, indent=4, sort_keys=False)
