import json
import os

from core.logger import setup_logger

log = setup_logger()


class ConnectionService:
    def __init__(self, json_folder: str):
        self.folder = json_folder

    def _path(self, filename: str) -> str:
        return os.path.join(self.folder, filename)

    def _load(self, filename: str) -> dict:
        path = self._path(filename)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"{filename} not found")
        with open(path, "r") as f:
            return json.load(f)

    def _save(self, filename: str, data: dict) -> None:
        with open(self._path(filename), "w") as f:
            json.dump(data, f, indent=2)

    def get_connections(self) -> dict:
        liquids = self._load("liquids.json")
        longdrinks = self._load("longdrinks.json")
        mixdrinks = self._load("mixdrinks.json")
        calibration = self._load("calibration.json")

        cup_size = None
        if longdrinks:
            cup_size = next(iter(longdrinks.values()))["gesamtmenge_ml"]
        elif mixdrinks:
            cup_size = next(iter(mixdrinks.values()))["gesamtmenge_ml"]

        occupied = {
            info["anschlussplatz"]: {
                "liquid_id": lid,
                "liquid_name": info.get("name"),
                "liquid_level": info.get("fuellstand_ml"),
                "liquid_alcohol": info.get("alkohol"),
            }
            for lid, info in liquids.items()
            if info.get("anschlussplatz", 0) != 0
        }

        connections = [
            {
                "connection": pos,
                "offset": calibration["connections"][str(pos)],
                **occupied.get(pos,
                               {"id": None, "liquid_name": None, "liquid_level": None, "name": None, "alkohol": None})
            }
            for pos in map(int, calibration.get("connections", {}).keys())
        ]

        return {"cup_size": cup_size, "connections": connections}

    def set_cup_size(self, cup_size: float) -> None:
        for filename in ("longdrinks.json", "mixdrinks.json"):
            data = self._load(filename)
            for drink in data.values():
                drink["gesamtmenge_ml"] = cup_size
            self._save(filename, data)
        log.info(f"Cup size updated to {cup_size} ml")

    def clear_connection(self, connection_id: int) -> None:
        liquids = self._load("liquids.json")
        for lid, info in liquids.items():
            if info.get("anschlussplatz") == connection_id:
                info["anschlussplatz"] = 0
                self._save("liquids.json", liquids)
                log.info(f"Removed liquid {lid} from position {connection_id}")
                return

    def assign_liquid(self, connection: int, liquid_id: int, liquid_fill: float | None) -> None:
        liquids = self._load("liquids.json")
        key = str(liquid_id)

        if key not in liquids:
            raise KeyError(f"Liquid {liquid_id} not found")
        if liquid_fill is not None and not isinstance(liquid_fill, (int, float)):
            raise TypeError("liquid_fill must be a number")

        liquids[key]["anschlussplatz"] = connection

        if liquid_fill is not None:
            liquids[key]["fuellstand_ml"] = liquid_fill

        self._save("liquids.json", liquids)
        log.info(
            f"Assigned liquid {key} to position {connection}"
            + (f" with fill {liquid_fill} ml" if liquid_fill is not None else "")
        )

    def set_offset(self, connection: int, offset: int) -> None:
        calibration = self._load("calibration.json")
        calibration["connections"][str(connection)] = offset
        self._save("calibration.json", calibration)
        log.info(f"Set offset for connection {connection} to {offset} steps")
