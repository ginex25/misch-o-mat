import json
from pathlib import Path

from core.logger import setup_logger

_LIQUIDS_PATH = Path(__file__).parent / "liquids.json"

log = setup_logger()


def get_all() -> dict:
    try:
        with open(_LIQUIDS_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log.error(f"Error loading liquids: {e}")
        raise


def update_all(liquids_data: dict) -> None:
    try:
        _save(liquids_data)
        log.debug("Liquid levels updated successfully")
    except Exception as e:
        log.error(f"Error saving liquids: {e}")
        raise


def _save(liquids_data: dict) -> None:
    with open(_LIQUIDS_PATH, "w") as f:
        json.dump(liquids_data, f, indent=4, sort_keys=False)
