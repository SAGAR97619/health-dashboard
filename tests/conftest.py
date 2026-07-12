"""
tests/conftest.py
Shared pytest fixtures for the Flask test client.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

os.environ.setdefault("FLASK_ENV", "testing")

from app import create_app


@pytest.fixture()
def app():
    application = create_app()
    application.config.update({"TESTING": True})
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()
