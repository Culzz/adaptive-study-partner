"""Application entry point for the Adaptive Study Partner backend.

Provides the Flask app factory ``create_app`` and a local development server.
See README.md for setup instructions and the current development status.
"""

import os
import tempfile

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

    if env == 'prod' and app.config['SECRET_KEY'] in (None, '', 'dev-key-change-this'):
        raise RuntimeError(
            "SECRET_KEY must be set in production — generate one with "
            "`openssl rand -hex 32` and pass it as an environment variable "
            "(see .env.example / README deployment steps)."
        )

    db.init_app(app)
    CORS(app)

    # Upload folder for study notes (size cap set in config.py).
    # On serverless hosts (e.g. Vercel) the project directory is read-only, so
    # fall back to the system temp directory instead of crashing at boot.
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except OSError:
        fallback = os.path.join(tempfile.gettempdir(), 'study-uploads')
        os.makedirs(fallback, exist_ok=True)
        app.config['UPLOAD_FOLDER'] = fallback

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
    env = os.getenv('FLASK_ENV', 'dev')
    app = create_app(env)
    app.run(
        # The Werkzeug debugger is a remote-code-execution risk — only default
        # it on in the dev environment; `FLASK_DEBUG` can still override.
        debug=(os.getenv('FLASK_DEBUG', 'true' if env == 'dev' else 'false')
               .lower() in ('1', 'true', 'yes')),
        host=os.getenv('HOST', '127.0.0.1'),
        port=int(os.getenv('PORT', '5000')),
    )
