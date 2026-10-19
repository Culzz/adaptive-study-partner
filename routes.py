"""REST API blueprints for the Adaptive Study Partner backend.

Four blueprints are registered by the app factory (see app.py):

* ``/api/auth``        — registration, login, current-student profile
* ``/api/notes``       — upload, list, and read study notes
* ``/api/quizzes``     — create quizzes, answer questions, record attempts
* ``/api/performance`` — mastery state and forgetting-risk review plan

All endpoints except registration and login require a Bearer token issued
at login (JWT, signed with the app's SECRET_KEY).
"""

import jwt
from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized

from forgetting import forgetting_risk
from models import Mastery, Note, Quiz, QuizAttempt, Question, Student, db

auth_bp = Blueprint("auth", __name__)
notes_bp = Blueprint("notes", __name__)
quizzes_bp = Blueprint("quizzes", __name__)
performance_bp = Blueprint("performance", __name__)

TOKEN_TTL_DAYS = 7


# ── Auth helpers ───────────────────────────────────────────────────────────

def _issue_token(student: Student) -> str:
    """Create a signed JWT for the given student."""
    payload = {
        "sub": str(student.id),
        "exp": datetime.utcnow() + timedelta(days=TOKEN_TTL_DAYS),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def _current_student() -> Student:
    """Resolve the request's Bearer token to a Student, or raise 401."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise Unauthorized("Missing bearer token.")
    try:
        payload = jwt.decode(header[7:], current_app.config["SECRET_KEY"],
                             algorithms=["HS256"])
        student_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise Unauthorized("Invalid or expired token.")
    student = db.session.get(Student, student_id)
    if student is None:
        raise Unauthorized("Unknown student.")
    return student


def _require_fields(data: dict, *fields) -> dict:
    """Validate that a JSON body exists and contains the given fields."""
    if not isinstance(data, dict):
        raise BadRequest("JSON body expected.")
    missing = [f for f in fields if not data.get(f) and data.get(f) != 0]
    if missing:
        raise BadRequest(f"Missing required fields: {', '.join(missing)}")
    return data


# ── /api/auth ──────────────────────────────────────────────────────────────

@auth_bp.post("/register")
def register():
    """Create a student account and return a token."""
    data = _require_fields(request.get_json(silent=True), "name", "email", "password")
    if Student.query.filter_by(email=data["email"]).first():
        raise BadRequest("An account with that email already exists.")

    student = Student(
        name=data["name"],
        email=data["email"],
        matric=data.get("matric"),
        level=data.get("level"),
    )
    student.set_password(data["password"])
    db.session.add(student)
    db.session.commit()
    return jsonify({"token": _issue_token(student), "student": student.to_dict()}), 201


@auth_bp.post("/login")
def login():
    """Verify credentials and return a token."""
    data = _require_fields(request.get_json(silent=True), "email", "password")
    student = Student.query.filter_by(email=data["email"]).first()
    if student is None or not student.check_password(data["password"]):
        raise Unauthorized("Invalid email or password.")
    return jsonify({"token": _issue_token(student), "student": student.to_dict()})


@auth_bp.get("/me")
def me():
    """Return the authenticated student's profile."""
    return jsonify(_current_student().to_dict())


# ── /api/notes ─────────────────────────────────────────────────────────────

@notes_bp.get("/")
def list_notes():
    """List the student's uploaded notes (metadata only)."""
    student = _current_student()
    notes = Note.query.filter_by(student_id=student.id).order_by(Note.uploaded_at.desc()).all()
    return jsonify([n.to_dict() for n in notes])


@notes_bp.post("/")
def upload_note():
    """Upload a plain-text/markdown study note.

    Accepts multipart form data with a ``file`` field (.txt or .md), or a
    JSON body ``{"filename": ..., "content": ...}``.
    """
    student = _current_student()

    if "file" in request.files:
        file = request.files["file"]
        if not file.filename.lower().endswith((".txt", ".md")):
            raise BadRequest("Only .txt and .md notes are supported right now.")
        content = file.read().decode("utf-8", errors="replace")
        filename = file.filename
    else:
        data = _require_fields(request.get_json(silent=True), "filename", "content")
        filename, content = data["filename"], data["content"]

    note = Note(student_id=student.id, filename=filename, content=content)
    db.session.add(note)
    db.session.commit()
    return jsonify(note.to_dict()), 201


@notes_bp.get("/<int:note_id>")
def read_note(note_id: int):
    """Return one note including its full text content."""
    student = _current_student()
    note = db.session.get(Note, note_id)
    if note is None or note.student_id != student.id:
        raise NotFound("Note not found.")
    return jsonify({**note.to_dict(), "content": note.content})


# ── /api/quizzes ───────────────────────────────────────────────────────────

@quizzes_bp.post("/")
def create_quiz():
    """Create a quiz with questions. Each question:
    ``{"question": str, "options": [4 choices], "correct": str, "difficulty": float}``
    The quiz ``title`` doubles as the mastery topic.
    """
    student = _current_student()
    data = _require_fields(request.get_json(silent=True), "title", "questions")
    questions = data["questions"]
    if not isinstance(questions, list) or not questions:
        raise BadRequest("questions must be a non-empty list.")

    quiz = Quiz(student_id=student.id, title=data["title"],
                difficulty=float(data.get("difficulty", 1.0)))
    db.session.add(quiz)
    db.session.flush()

    for q in questions:
        _require_fields(q, "question", "options", "correct")
        if len(q["options"]) != 4:
            raise BadRequest("Each question needs exactly 4 options.")
        db.session.add(Question(
            quiz_id=quiz.id,
            question=q["question"],
            options=q["options"],
            correct=q["correct"],
            difficulty=float(q.get("difficulty", 1.0)),
        ))
    db.session.commit()
    return jsonify(quiz.to_dict()), 201


@quizzes_bp.get("/")
def list_quizzes():
    """List the student's quizzes."""
    student = _current_student()
    quizzes = Quiz.query.filter_by(student_id=student.id).order_by(Quiz.created_at.desc()).all()
    return jsonify([q.to_dict() for q in quizzes])


@quizzes_bp.get("/<int:quiz_id>")
def get_quiz(quiz_id: int):
    """Return a quiz with its questions (correct answers withheld)."""
    student = _current_student()
    quiz = db.session.get(Quiz, quiz_id)
    if quiz is None or quiz.student_id != student.id:
        raise NotFound("Quiz not found.")
    return jsonify({
        **quiz.to_dict(),
        "questions": [
            {"id": q.id, "question": q.question, "options": q.options,
             "difficulty": q.difficulty}
            for q in quiz.questions
        ],
    })


@quizzes_bp.post("/<int:quiz_id>/answers")
def answer_question(quiz_id: int):
    """Record an answer: body ``{"question_id": int, "answer": str,
    "time_spent": int seconds}``. Updates the topic's mastery and
    forgetting risk, and returns the grade plus new mastery state.
    """
    student = _current_student()
    quiz = db.session.get(Quiz, quiz_id)
    if quiz is None or quiz.student_id != student.id:
        raise NotFound("Quiz not found.")

    data = _require_fields(request.get_json(silent=True), "question_id", "answer")
    question = db.session.get(Question, int(data["question_id"]))
    if question is None or question.quiz_id != quiz.id:
        raise NotFound("Question not found in this quiz.")

    is_correct = str(question.correct).strip().lower() == str(data["answer"]).strip().lower()
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        student_id=student.id,
        question_id=question.id,
        answer=str(data["answer"]),
        is_correct=is_correct,
        time_spent=int(data.get("time_spent", 0)),
    )
    db.session.add(attempt)
    db.session.flush()  # make the new attempt visible to the queries below

    mastery = Mastery.query.filter_by(student_id=student.id, topic=quiz.title).first()
    if mastery is None:
        mastery = Mastery(student_id=student.id, topic=quiz.title)
        db.session.add(mastery)

    # Rolling accuracy across every attempt on this topic.
    topic_filter = (QuizAttempt.student_id == student.id) & (Quiz.title == quiz.title)
    total = QuizAttempt.query.join(Quiz).filter(topic_filter).count()
    correct = (QuizAttempt.query.join(Quiz)
               .filter(topic_filter, QuizAttempt.is_correct.is_(True)).count())

    mastery.score = round(correct / total, 3)
    mastery.review_count = (mastery.review_count or 0) + 1
    mastery.last_reviewed = datetime.utcnow()
    mastery.forgetting_risk = forgetting_risk(
        mastery.last_reviewed, mastery.score, mastery.review_count
    )
    db.session.commit()

    return jsonify({
        "is_correct": is_correct,
        "correct_answer": question.correct,
        "mastery": {
            "topic": mastery.topic,
            "score": mastery.score,
            "review_count": mastery.review_count,
            "forgetting_risk": mastery.forgetting_risk,
        },
    })


# ── /api/performance ───────────────────────────────────────────────────────

@performance_bp.get("/mastery")
def mastery():
    """All mastery records, most-at-risk topic first."""
    student = _current_student()
    rows = Mastery.query.filter_by(student_id=student.id).all()
    rows.sort(key=lambda m: m.forgetting_risk or 0.0, reverse=True)
    return jsonify([
        {
            "topic": m.topic,
            "score": m.score,
            "review_count": m.review_count,
            "last_reviewed": m.last_reviewed.isoformat() if m.last_reviewed else None,
            "forgetting_risk": m.forgetting_risk,
        }
        for m in rows
    ])


@performance_bp.get("/review-plan")
def review_plan():
    """Revision plan: topics ordered by forgetting risk, with an action hint."""
    student = _current_student()
    rows = Mastery.query.filter_by(student_id=student.id).all()
    rows.sort(key=lambda m: m.forgetting_risk or 0.0, reverse=True)

    plan = []
    for m in rows:
        risk = m.forgetting_risk or 0.0
        action = ("review today" if risk >= 60
                  else "review this week" if risk >= 30
                  else "still fresh")
        plan.append({"topic": m.topic, "forgetting_risk": risk,
                     "score": m.score, "action": action})
    return jsonify(plan)
