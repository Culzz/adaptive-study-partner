from flask import Flask
from flask_cors import CORS
from config import config
from models import db
import os

def create_app(env='dev'):
    app = Flask(__name__)
    app.config.from_object(config[env])
    
    db.init_app(app)
    CORS(app)
    
    # create upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # register blueprints
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
    app.run(debug=True, host='0.0.0.0', port=5000)