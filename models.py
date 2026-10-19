"""SQLAlchemy models for the Adaptive Study Partner backend.

Defines the six tables behind the adaptive-learning flow:

* ``Student``    — registered student accounts (bcrypt-hashed passwords)
* ``Note``       — uploaded study notes with extracted text content
* ``Quiz``       — a quiz belonging to a student
* ``Question``   — individual multiple-choice questions within a quiz
* ``QuizAttempt``— one answer to one question, with timing
* ``Mastery``    — per-topic mastery state, including the forgetting-risk
  score that drives the adaptive review recommendations.
"""

from datetime import datetime

import bcrypt
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Student(db.Model):
    """A registered student account."""

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
        """Hash and store the given plaintext password with bcrypt."""
        self.password_hash = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

    def check_password(self, pwd):
        """Return True if ``pwd`` matches the stored hash."""
        return bcrypt.checkpw(pwd.encode(), self.password_hash.encode())

    def to_dict(self):
        """Serialise the account for API responses (never exposes the hash)."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'matric': self.matric,
            'level': self.level
        }


class Note(db.Model):
    """A study note uploaded by a student."""

    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    filename = db.Column(db.String(255))
    content = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Serialise the note metadata (content length, not content)."""
        return {
            'id': self.id,
            'filename': self.filename,
            'uploaded_at': self.uploaded_at.isoformat(),
            'content_length': len(self.content) if self.content else 0
        }


class Quiz(db.Model):
    """A quiz created for or by a student."""

    __tablename__ = 'quizzes'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    title = db.Column(db.String(200))
    difficulty = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship('Question', backref='quiz', lazy=True)
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy=True)

    def to_dict(self):
        """Serialise the quiz with its question count."""
        return {
            'id': self.id,
            'title': self.title,
            'difficulty': self.difficulty,
            'created_at': self.created_at.isoformat(),
            'question_count': len(self.questions)
        }


class Question(db.Model):
    """A single multiple-choice question inside a quiz."""

    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON)  # list of 4 options
    correct = db.Column(db.String(500))
    difficulty = db.Column(db.Float, default=1.0)

    attempts = db.relationship('QuizAttempt', backref='question', lazy=True)


class QuizAttempt(db.Model):
    """One answer given to one question, with time spent."""

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
    """Per-topic mastery state — the adaptive core of the app.

    ``score`` (0–1) tracks how well the student knows a topic;
    ``forgetting_risk`` (percentage) estimates how likely the knowledge is
    to have faded since ``last_reviewed``. Review recommendations are
    prioritised by this risk score.
    """

    __tablename__ = 'mastery'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    topic = db.Column(db.String(200))
    score = db.Column(db.Float, default=0.0)  # 0-1
    last_reviewed = db.Column(db.DateTime)
    review_count = db.Column(db.Integer, default=0)
    forgetting_risk = db.Column(db.Float, default=100.0)  # percentage
