import os
from flask import Flask
from dotenv import load_dotenv

from config import Config
from routes.main_routes import main_bp

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.register_blueprint(main_bp)

    return app

def delete_app(self):
    app = Flask(__name__)
    app.config.from_object(Delete)

    os.makedirs(app.config)
app = create_app()
