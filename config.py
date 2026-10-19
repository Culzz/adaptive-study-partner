"""Environment-driven configuration for the Adaptive Study Partner backend.

Loads ``.env`` (see .env.example) and exposes one config class per
environment: ``dev``, ``test`` and ``prod``.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration shared by every environment."""

    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-this')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///study.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max


class DevConfig(Config):
    """Local development — debug server, SQLite by default."""
    DEBUG = True
    TESTING = False


class TestConfig(Config):
    """Automated tests — in-memory SQLite, no side effects on disk."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProdConfig(Config):
    """Production — debug off; run behind gunicorn via wsgi.py."""
    DEBUG = False
    TESTING = False


config = {
    'dev': DevConfig,
    'test': TestConfig,
    'prod': ProdConfig,
    'default': DevConfig
}
