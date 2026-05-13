import os
import threading
import time

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    import mocks.gpio as GPIO
from flask import Flask, json, jsonify, request, send_from_directory
from flask_cors import CORS
from json import JSONDecodeError
from actions.dispense import dispense_drink
from actions.reset import reset
from actions.clean import clean_position
from hardware.setup import clean_gpio, setup_gpio
from config.pins import BUTTON_PIN
from hardware.scale import tare, calibrate
from core.logger import setup_logger

log = setup_logger()

app = Flask(__name__, static_folder="../frontend/dist", static_url_path="/")
CORS(app, origins="*")
JSON_FOLDER = "database"


def button_listener():
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            log.info("Emergency Button pressed")
            reset()
            clean_gpio()
        time.sleep(2)
        setup_gpio()


@app.route('/')
def serve_react_app():
    return send_from_directory(app.static_folder, "index.html")


@app.route('/tare', methods=['POST'])
def tare_scale():
    try:
        tare()
        return jsonify({"message": "Scale tared"}), 200
    except Exception as e:
        log.exception("Error while taring scale")
        return jsonify({"error": f"Error while taring scale: {str(e)}"}), 500


@app.route('/reset', methods=['POST'])
def reset_hardware():
    try:
        reset()
        return jsonify({"message": "Hardware successfully reset"}), 200
    except Exception as e:
        log.exception("Error while resetting hardware")
        return jsonify({"error": f"Error while resetting hardware: {str(e)}"}), 500


@app.route('/clean', methods=['POST'])
def clean():
    try:
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


@app.route('/calibrate', methods=['POST'])
def calibrate():
    try:
        calibrate(100)
        return jsonify({"message": "Successfully calibrated"}), 200
    except Exception as e:
        log.exception("Error while calibrating scale")
        return jsonify({"error": f"Error while calibrating: {str(e)}"}), 500


@app.route('/shutdown', methods=['POST'])
def shutdown():
    try:
        clean_gpio()
        os.system("sudo shutdown now")
        return jsonify({"message": "Raspberry Pi will be shut down"}), 200
    except Exception as e:
        log.exception("Error while shutting down Raspberry Pi")
        return jsonify({"error": f"Error while shutting down: {str(e)}"}), 500


@app.route('/liquids', methods=['GET'])
def get_liquids():
    liquids_filepath = os.path.join(JSON_FOLDER, 'liquids.json')

    if not os.path.isfile(liquids_filepath):
        return {"error": "File not found"}, 404

    try:
        with open(liquids_filepath, 'r') as liquids_file:
            liquids_data = json.load(liquids_file)
        return jsonify(liquids_data)
    except JSONDecodeError:
        log.error("Invalid JSON format in liquids.json")
        return {"error": "Invalid JSON format"}, 400


@app.route('/drinks/<filename>', methods=['GET'])
def get_data(filename):
    filepath = os.path.join(JSON_FOLDER, filename + ".json")
    liquids_filepath = os.path.join(JSON_FOLDER, 'liquids.json')

    if not os.path.isfile(filepath) or not os.path.isfile(liquids_filepath):
        log.error("Drinks or liquids file not found in /drinks endpoint")
        return {"error": "File not found"}, 404

    try:
        with open(filepath, 'r') as file:
            drinks_data = json.load(file)

        with open(liquids_filepath, 'r') as liquids_file:
            liquids_data = json.load(liquids_file)

        available_drinks = {}
        overall_drink_ml = 0
        for drink_id, drink in drinks_data.items():
            drink_ml = drink['gesamtmenge_ml']
            overall_drink_ml = drink_ml
            available = True
            for ingredient_id, percentage in drink['zutaten'].items():
                amount = percentage / 100 * drink_ml

                if liquids_data[str(ingredient_id)]['belegungswert'] == 0:
                    if liquids_data[str(ingredient_id)]['fuellstand_ml'] < 150:
                        available = False
                        break
                else:
                    if liquids_data[str(ingredient_id)]['fuellstand_ml'] < 80:
                        available = False
                        break

                if str(ingredient_id) not in liquids_data or liquids_data[str(ingredient_id)][
                    'fuellstand_ml'] < amount or liquids_data[str(ingredient_id)]['anschlussplatz'] == 0:
                    available = False
                    break
            if available:
                available_drinks[drink_id] = drink

        return jsonify(available_drinks, overall_drink_ml)
    except JSONDecodeError:
        log.exception("Invalid JSON format in drinks or liquids file")
        return {"error": "Invalid JSON format"}, 400


@app.route('/preparation', methods=['POST'])
def preparation():
    data = request.get_json()

    if not data or 'drink' not in data or 'strength' not in data or 'category' not in data:
        return jsonify({"error": "Missing required parameters"}), 400

    drink_name = data['drink']
    strength = data['strength']
    filename = "longdrinks.json" if data['category'] == "Longdrinks" else "mixdrinks.json"

    drinks_filepath = os.path.join(JSON_FOLDER, filename)
    liquids_filepath = os.path.join(JSON_FOLDER, 'liquids.json')

    if not os.path.isfile(drinks_filepath) or not os.path.isfile(liquids_filepath):
        log.error("Drinks or liquids file not found in /preparation endpoint")
        return jsonify({"error": "File not found"}), 404

    try:
        with open(drinks_filepath, 'r') as drinks_file:
            drinks_data = json.load(drinks_file)

        with open(liquids_filepath, 'r') as liquids_file:
            liquids_data = json.load(liquids_file)

        drink_data = None
        for drink_id, drink in drinks_data.items():
            if drink['name'] == drink_name:
                drink_data = drink
                break

        if drink_data is None:
            return jsonify({"error": "Drink not found"}), 404

        drink_ml = drink_data['gesamtmenge_ml']
        ingredients = {}

        for ingredient_id, percentage in drink_data['zutaten'].items():
            ing_id_str = str(ingredient_id)

            if ing_id_str not in liquids_data:
                log.warning(f"Ingredient ID {ing_id_str} not found in liquids for drink '{drink_name}'")
                continue

            if filename == "mixdrinks.json":
                is_alcohol = liquids_data[ing_id_str].get('alkohol', False)

                if not is_alcohol:
                    amount = (percentage + 5) / 100 * drink_ml if strength == "mittel" else (
                                                                                                    percentage + 10) / 100 * drink_ml if strength == "schwach" else percentage / 100 * drink_ml
                else:
                    amount = (percentage - 10) / 100 * drink_ml if strength == "schwach" else (
                                                                                                      percentage - 5) / 100 * drink_ml if strength == "mittel" else percentage / 100 * drink_ml
            else:
                amount = percentage / 100 * drink_ml

            liquids_data[ing_id_str]['fuellstand_ml'] -= amount
            ingredients[ingredient_id] = amount

        with open(liquids_filepath, 'w') as liquids_file:
            json.dump(liquids_data, liquids_file, indent=4, sort_keys=False)

        try:
            dispense_drink(ingredients)
        except Exception as e:
            return jsonify({"error": f"Dispensing failed: {str(e)}"}), 500

        return '', 204

    except Exception as e:
        log.exception("Critical error in /preparation endpoint")
        return jsonify({"error": str(e)}), 500


@app.route('/update/<file_name>', methods=['POST'])
def update_value(file_name):
    try:
        data = request.get_json()
        if 'value' not in data or 'index' not in data or 'category' not in data:
            log.warning("Missing required parameters in /update request")
            return jsonify({"error": "Missing required parameters: 'index', 'category', 'value'"}), 400

        value = data['value']
        index = data['index']
        category = data['category']

        if file_name == "liquid":
            filepath = os.path.join(JSON_FOLDER, 'liquids.json')

            with open(filepath, 'r') as file:
                json_data = json.load(file)

            json_data[str(index)][str(category)] = value

            with open(filepath, 'w') as file:
                json.dump(json_data, file, indent=4, sort_keys=False)
            log.debug(f"Updated '{category}' for liquid at index {index} to {value}")
            return jsonify({"message": f"'{category}' updated successfully at index {index}"}), 200

        elif file_name == "longdrinks":
            longdrinks_path = os.path.join(JSON_FOLDER, 'longdrinks.json')
            mixdrinks_path = os.path.join(JSON_FOLDER, 'mixdrinks.json')

            def update_gesamtmenge(filepath, category, new_value):
                try:
                    with open(filepath, 'r') as file:
                        json_data = json.load(file)

                    for key, item in json_data.items():
                        item[category] = new_value

                    with open(filepath, 'w') as file:
                        json.dump(json_data, file, indent=4, sort_keys=False)

                    return {"message": f"'{category}' updated successfully to {new_value}"}, 200

                except JSONDecodeError:
                    return {"error": "Invalid JSON format"}, 400
                except Exception as e:
                    log.exception("Error while updating gesamtmenge_ml in drinks file")
                    return {"error": str(e)}, 500

            update_gesamtmenge(longdrinks_path, category, value)
            update_gesamtmenge(mixdrinks_path, category, value)

            return jsonify({"message": "gesamtmenge_ml updated successfully in 'longdrinks.json' and 'mixdrinks.json'"
                            }), 200

        else:
            log.warning(f"Invalid file_name '{file_name}' in /update request")
            return jsonify({"error": f"Invalid file_name '{file_name}'"}), 400

    except JSONDecodeError:
        log.exception("Error while updating values in /update request")
        return jsonify({"error": "Invalid JSON format in file"}), 400
    except Exception as e:
        log.exception("Error while updating values in /update request")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    setup_gpio()
    reset()
    listener_thread = threading.Thread(target=button_listener, daemon=True)
    listener_thread.start()
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    except KeyboardInterrupt:
        clean_gpio()
