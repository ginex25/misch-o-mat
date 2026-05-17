from flask import Blueprint, request

from core.logger import setup_logger
from services.calibration_service import CalibrationService

log = setup_logger()
calibration_bp = Blueprint("calibration", __name__)

_service = CalibrationService()


@calibration_bp.route("/step", methods=["POST"])
def step():
    try:
        data = request.get_json() or {}
        steps = data["steps"]
        connection = data["connection"]

        if connection is None:
            return {"error": "connection is required"}, 400
        if steps is None:
            return {"error": "steps is required"}, 400
        if not isinstance(steps, int):
            return {"error": "steps must be an integer"}, 400

        _service.adjust_step(connection, steps)

        return {}, 204
    except Exception as e:
        log.exception("Error during calibration step")
        return {"error": str(e)}, 400


@calibration_bp.route("/move-to/<int:connection>", methods=["POST"])
def move_to(connection):
    try:
        _service.move_to(connection)
        return {}, 204
    except Exception as e:
        log.exception("Error during calibration step")
        return {"error": str(e)}, 400


@calibration_bp.route("/test/<int:connection>", methods=["POST"])
def test(connection):
    try:
        success = _service.test_connection(connection)

        return {"success": success}, 200
    except Exception as e:
        log.exception("Error during calibration step")
        return {"error": str(e)}, 400

@calibration_bp.route("/reset", methods=["POST"])
def reset_session():
    try:
        _service.reset_session()
        return {}, 204
    except Exception as e:
        log.exception("Error during calibration reset")
        return {"error": str(e)}, 400
