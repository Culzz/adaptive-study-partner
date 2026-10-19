"""WSGI entry point for production servers (e.g. gunicorn).

Usage: ``gunicorn wsgi:app``
"""

import os

from app import create_app

app = create_app(os.getenv('FLASK_ENV', 'prod'))
