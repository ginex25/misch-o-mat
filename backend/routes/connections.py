from json import JSONDecodeError

from flask import Blueprint, jsonify, request

from core.logger import setup_logger
from services.connection_service import ConnectionService

log = setup_logger()
connections_bp = Blueprint("connections", __name__)
_service = ConnectionService(json_folder="database")


@connections_bp.route("", methods=["GET"])
def get_connections():
    try:
        return jsonify(_service.get_connections())
    except FileNotFoundError as e:
        log.exception("File not found when loading connections")
        return {"error": str(e)}, 404
    except JSONDecodeError:
        log.exception("Invalid JSON format")
        return {"error": "Invalid JSON format"}, 400
    except Exception:
        log.exception("Error loading connections")
        return {"error": "Internal server error"}, 500


@connections_bp.route("/set-cup-size", methods=["POST"])
def set_cup_size():
    try:
        data = request.get_json() or {}
        cup_size = data.get("cup_size")

        if cup_size is None:
            return {"error": "cup_size is required"}, 400
        if not isinstance(cup_size, (int, float)):
            return {"error": "cup_size must be a number"}, 400

        _service.set_cup_size(float(cup_size))
        return "", 204

    except FileNotFoundError as e:
        log.exception("File not found when setting cup size")
        return {"error": str(e)}, 404
    except JSONDecodeError:
        log.exception("Invalid JSON format when setting cup size")
        return {"error": "Invalid JSON format"}, 400
    except Exception:
        log.exception("Error setting cup size")
        return {"error": "Internal server error"}, 500


@connections_bp.route("/<int:connection>", methods=["POST"])
def update_connection(connection):
    try:
        data = request.get_json() or {}
        liquid_id = data.get("liquid_id")
        liquid_fill = data.get("liquid_fill")

        if liquid_id is not None:
            liquid_id = int(liquid_id)

        log.debug(f"Updating connection {connection} with liquid_id={liquid_id} and liquid_fill={liquid_fill}")
        if liquid_id == 0:
            _service.clear_connection(connection)
        elif liquid_id is not None:
            _service.assign_liquid(connection, liquid_id, liquid_fill)

        offset = data.get("offset")
        if offset is not None:
            _service.set_offset(connection, int(offset))

        return "", 204

    except FileNotFoundError as e:
        log.exception("File not found when updating connection")
        return {"error": str(e)}, 404
    except KeyError as e:
        log.exception("Error updating connection")
        return {"error": str(e)}, 404
    except TypeError as e:
        log.exception("Error updating connection")
        return {"error": str(e)}, 400
    except JSONDecodeError:
        log.exception("Invalid JSON format when updating connection")
        return {"error": "Invalid JSON format"}, 400
    except Exception:
        log.exception("Error updating connection")
        return {"error": "Internal server error"}, 500
