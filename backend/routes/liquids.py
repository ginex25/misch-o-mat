import os
import json
from flask import Blueprint, jsonify
from json import JSONDecodeError
from core.logger import setup_logger

log = setup_logger()
liquids_bp = Blueprint('liquids', __name__)
JSON_FOLDER = "database"


@liquids_bp.route('/liquids', methods=['GET'])
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


@liquids_bp.route('/drinks/<filename>', methods=['GET'])
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

