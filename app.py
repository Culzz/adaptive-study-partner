"""Application entry point for the Adaptive Study Partner backend.

Provides the Flask app factory ``create_app`` and a local development server.
See README.md for setup instructions and the current development status.
"""

import os

from flask import Flask
from flask_cors import CORS

from config import config
from models import db


def create_app(env='dev'):
    """Build the Flask application for the given environment.

    Args:
        env: Config key — one of ``dev``, ``test``, ``prod`` (see config.py).

    Returns:
        Flask: configured application with database and CORS initialised.
    """
    app = Flask(__name__)
    app.config.from_object(config[env])

    db.init_app(app)
    CORS(app)

    # Upload folder for study notes (size cap set in config.py).
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register API blueprints (auth, notes, quizzes, performance).
    from routes import auth_bp, notes_bp, quizzes_bp, performance_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(notes_bp, url_prefix='/api/notes')
    app.register_blueprint(quizzes_bp, url_prefix='/api/quizzes')
    app.register_blueprint(performance_bp, url_prefix='/api/performance')

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'dev'))
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'true').lower() in ('1', 'true', 'yes'),
        host=os.getenv('HOST', '127.0.0.1'),
        port=int(os.getenv('PORT', '5000')),
    )
