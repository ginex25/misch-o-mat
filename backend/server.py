import os
import threading
import time

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(_BACKEND_DIR)

from flask import Flask
from flask_cors import CORS

from actions.reset import reset
from config.pins import BUTTON_PIN
from core.logger import setup_logger
from hardware import GPIO
from hardware.setup import clean_gpio, setup_gpio
from routes.calibration import calibration_bp
from routes.connections import connections_bp
from routes.drinks import drinks_bp
from routes.frontend import frontend_bp
from routes.hardware import hardware_bp
from routes.liquids import liquids_bp

PRODUCTION = os.getenv('ENV') == 'production'
log = setup_logger()
log.info(f"Server runs on production mode: {PRODUCTION}")

app = Flask(__name__, static_folder="../frontend/dist", static_url_path="/")
CORS(app, origins="*")
app.register_blueprint(frontend_bp)
app.register_blueprint(hardware_bp, url_prefix='/api')
app.register_blueprint(liquids_bp, url_prefix='/api')
app.register_blueprint(drinks_bp, url_prefix='/api')
app.register_blueprint(connections_bp, url_prefix='/api/connections')
app.register_blueprint(calibration_bp, url_prefix='/api/calibration')


def button_listener():
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            log.info("Emergency Button pressed")
            reset()
            clean_gpio()
        time.sleep(2)
        setup_gpio()


if __name__ == '__main__':
    setup_gpio()
    reset()
    listener_thread = threading.Thread(target=button_listener, daemon=True)
    listener_thread.start()
    try:
        app.run(host="0.0.0.0", port=5000, debug=not PRODUCTION)
    except KeyboardInterrupt:
        clean_gpio()
