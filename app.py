"""
CHECK YOUR RESUME
Main Flask application file.

This is the entry point of the app. It creates the Flask app,
loads configuration, registers the routes (blueprint), and makes
sure the upload folder exists before the server starts.
"""

import os
from flask import Flask
from dotenv import load_dotenv

from config import Config
from routes.main_routes import main_bp

# Load variables from .env file (API keys, secret key, etc.)
load_dotenv()


def create_app():
    """Application factory - builds and configures the Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Make sure the temporary upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Register all the routes defined in routes/main_routes.py
    app.register_blueprint(main_bp)

    return app


app = create_app()


if __name__ == "__main__":
    # debug=True is fine for local development, turn off in production
    app.run(debug=True, port=5000)
