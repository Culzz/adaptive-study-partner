from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    matric = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    level = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    quizzes = db.relationship('Quiz', backref='student', lazy=True)
    notes = db.relationship('Note', backref='student', lazy=True)
    
    def set_password(self, pwd):
        self.password_hash = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
    
    def check_password(self, pwd):
        return bcrypt.checkpw(pwd.encode(), self.password_hash.encode())
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'matric': self.matric,
            'level': self.level
        }

class Note(db.Model):
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    filename = db.Column(db.String(255))
    content = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'uploaded_at': self.uploaded_at.isoformat(),
            'content_length': len(self.content) if self.content else 0
        }

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    title = db.Column(db.String(200))
    difficulty = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    questions = db.relationship('Question', backref='quiz', lazy=True)
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'difficulty': self.difficulty,
            'created_at': self.created_at.isoformat(),
            'question_count': len(self.questions)
        }

class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON)  # list of 4 options
    correct = db.Column(db.String(500))
    difficulty = db.Column(db.Float, default=1.0)
    
    attempts = db.relationship('QuizAttempt', backref='question', lazy=True)

class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    answer = db.Column(db.String(500))
    is_correct = db.Column(db.Boolean, default=False)
    time_spent = db.Column(db.Integer)  # seconds
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)

class Mastery(db.Model):
    __tablename__ = 'mastery'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    topic = db.Column(db.String(200))
    score = db.Column(db.Float, default=0.0)  # 0-1
    last_reviewed = db.Column(db.DateTime)
    review_count = db.Column(db.Integer, default=0)
    forgetting_risk = db.Column(db.Float, default=100.0)  # percentage