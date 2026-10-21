"""Environment-driven configuration for the Adaptive Study Partner backend.

Loads ``.env`` (see .env.example) and exposes one config class per
environment: ``dev``, ``test`` and ``prod``.
"""

import os

from dotenv import load_dotenv
from sqlalchemy.pool import StaticPool

load_dotenv()


class Config:
    """Base configuration shared by every environment."""

    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-this')

    # Pin the driver dialect: bare ``postgresql://`` resolves to SQLAlchemy 2.1's
    # default Psycopg 3 dialect, which would crash on hosts where only
    # psycopg2-binary is installed. ``+psycopg2`` is explicit and stable on
    # every SQLAlchemy version.
    _database_url = os.getenv(
        'DATABASE_URL',
        'sqlite:///study.db'
    )
    if _database_url.startswith('postgresql://'):
        _database_url = _database_url.replace(
            'postgresql://', 'postgresql+psycopg2://', 1)
    SQLALCHEMY_DATABASE_URI = _database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max


class DevConfig(Config):
    """Local development — debug server, SQLite by default."""
    DEBUG = True
    TESTING = False


class TestConfig(Config):
    """Automated tests — in-memory SQLite, no side effects on disk.

    StaticPool makes every session share one connection, so the
    in-memory database persists across requests in a test run.
    """
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'poolclass': StaticPool,
        'connect_args': {'check_same_thread': False},
    }


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
