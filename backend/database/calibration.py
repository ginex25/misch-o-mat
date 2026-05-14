import json
from pathlib import Path

from core.logger import setup_logger

_PATH = Path(__file__).parent / "calibration.json"

_DEFAULTS = {
    "connections": {
        "1": 5, "2": 6, "3": 7, "4": 8, "5": 9,
        "6": 10, "7": 11, "8": 12, "9": 13,
        "10": 0, "11": 1, "12": 2, "13": 3, "14": 4,
        "15": 14, "16": 15, "17": 16, "18": 17, "19": 18,
    },
}

_KEY_CALIBRATION = "connections"

_cache: dict | None = None

log = setup_logger()


def _load() -> dict:
    global _cache
    if _cache is None:
        log.debug("Loading calibration data from file...")
        try:
            with open(_PATH, "r") as f:
                _cache = json.load(f)
            for key, val in _DEFAULTS.items():
                _cache.setdefault(key, val)
        except (FileNotFoundError, json.JSONDecodeError):
            _cache = _DEFAULTS.copy()
    return _cache


def _save(data: dict) -> None:
    global _cache
    with open(_PATH, "w") as f:
        json.dump(data, f, indent=2)
    _cache = data


def reset_to_defaults() -> None:
    _save(_DEFAULTS.copy())


def get_offsets() -> dict[str, int]:
    return _load()[_KEY_CALIBRATION]


def get_offset(connection: int) -> int:
    if connection == 0:
        return 0
    return _load()[_KEY_CALIBRATION][str(connection)]


def set_offset(connection: int, offset: int) -> None:
    data = _load()
    data[_KEY_CALIBRATION][str(connection)] = offset
    _save(data)


def set_offsets(mapping: dict[int, int]) -> None:
    data = _load()
    for connection, offset in mapping.items():
        data[_KEY_CALIBRATION][str(connection)] = offset
    _save(data)
