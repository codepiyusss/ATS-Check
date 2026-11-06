import os
import sys

# Must be set BEFORE `app` is imported, so importing it never builds a
# development app or creates an uploads/ folder inside the project.
os.environ["APP_ENV"] = "testing"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import glob  # noqa: E402

import pytest  # noqa: E402

from app import create_app  # noqa: E402
from routes.analysis import reset_limiter  # noqa: E402


@pytest.fixture()
def app():
    reset_limiter()
    application = create_app("testing")
    # start every test with an empty upload folder
    for f in glob.glob(os.path.join(application.config["UPLOAD_FOLDER"], "*")):
        os.remove(f)
    yield application
    reset_limiter()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def upload_dir(app):
    return app.config["UPLOAD_FOLDER"]
