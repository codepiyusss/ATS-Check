import os

from dotenv import load_dotenv
from flask import Flask

load_dotenv()  # must run before config.py reads os.environ

from config import get_config  # noqa: E402


def create_app(config_name=None):
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    from routes.main import main_bp
    from routes.analysis import analysis_bp
    from routes.errors import register_error_handlers

    app.register_blueprint(main_bp)
    app.register_blueprint(analysis_bp)
    register_error_handlers(app)

    return app


# Gunicorn imports this name: `gunicorn app:app`
app = create_app()

if __name__ == "__main__":
    app.run(port=5000)
