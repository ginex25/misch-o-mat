import os
import json
from flask import Blueprint, jsonify, request
from json import JSONDecodeError
from actions.dispense import dispense_drink
from core.logger import setup_logger

log = setup_logger()
drinks_bp = Blueprint('drinks', __name__)
JSON_FOLDER = "database"


@drinks_bp.route('/preparation', methods=['POST'])
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


@drinks_bp.route('/update/<file_name>', methods=['POST'])
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

