import os
from flask import Blueprint, jsonify
from actions.reset import reset
from actions.clean import clean_position
from hardware.setup import clean_gpio
from hardware.scale import tare, calibrate
from core.logger import setup_logger

log = setup_logger()
hardware_bp = Blueprint('hardware', __name__)


@hardware_bp.route('/tare', methods=['POST'])
def tare_scale():
    try:
        tare()
        return jsonify({"message": "Scale tared"}), 200
    except Exception as e:
        log.exception("Error while taring scale")
        return jsonify({"error": f"Error while taring scale: {str(e)}"}), 500


@hardware_bp.route('/reset', methods=['POST'])
def reset_hardware():
    try:
        reset()
        return jsonify({"message": "Hardware successfully reset"}), 200
    except Exception as e:
        log.exception("Error while resetting hardware")
        return jsonify({"error": f"Error while resetting hardware: {str(e)}"}), 500


@hardware_bp.route('/clean', methods=['POST'])
def clean():
    try:
        from flask import request
        data = request.get_json()
        if 'position' not in data:
            log.exception("Missing 'position' parameter in /clean request")
            return jsonify({"error": "Missing required parameter"}), 400

        position = data['position']
        clean_position(position)
        return jsonify({"message": "Successfully cleaned"}), 200
    except Exception as e:
        log.exception("Error while cleaning position")
        return jsonify({"error": f"Error while cleaning: {str(e)}"}), 500


@hardware_bp.route('/calibrate', methods=['POST'])
def calibrate_scale():
    try:
        calibrate(100)
        return jsonify({"message": "Successfully calibrated"}), 200
    except Exception as e:
        log.exception("Error while calibrating scale")
        return jsonify({"error": f"Error while calibrating: {str(e)}"}), 500


@hardware_bp.route('/shutdown', methods=['POST'])
def shutdown():
    try:
        clean_gpio()
        os.system("sudo shutdown now")
        return jsonify({"message": "Raspberry Pi will be shut down"}), 200
    except Exception as e:
        log.exception("Error while shutting down Raspberry Pi")
        return jsonify({"error": f"Error while shutting down: {str(e)}"}), 500

