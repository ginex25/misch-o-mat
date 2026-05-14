from flask import Blueprint, send_from_directory, current_app

frontend_bp = Blueprint('frontend', __name__)


@frontend_bp.route('/')
def serve_react_app():
    return send_from_directory(current_app.static_folder, "index.html")

