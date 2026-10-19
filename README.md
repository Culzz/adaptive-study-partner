# Adaptive Study Partner

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3-blue.svg)](https://flask.palletsprojects.com/)
[![Status: Backend skeleton](https://img.shields.io/badge/status-backend%20skeleton-orange.svg)](#status)

An adaptive study companion for university students: upload notes, take quizzes, and get review recommendations prioritised by **forgetting risk** — a spaced-repetition style signal that estimates which topics you're about to lose.

## How it adapts

Every topic a student studies gets a mastery record:

| Signal | Meaning |
|---|---|
| `score` (0–1) | Current mastery of the topic |
| `review_count` | How many times it has been reviewed |
| `last_reviewed` | When it was last revised |
| `forgetting_risk` (%) | Estimated probability the knowledge has faded |

Review recommendations are ordered by `forgetting_risk`, so the student sees the topic most likely to have decayed first — the same principle behind spaced repetition, applied per topic rather than per deck.

## Status

> **This repository currently contains the backend skeleton.** The data model, configuration layer, and app factory are complete and runnable. Two pieces are still in development:

- **`routes.py`** — the four API blueprints (`/api/auth`, `/api/notes`, `/api/quizzes`, `/api/performance`) are designed and registered by the app factory, but their handlers have not landed yet. The server boots cleanly without them.
- **React frontend** — `package.json` declares the intended stack (React 18, React Router, Chart.js); the `src/` scaffold has not been committed yet.

See the [Roadmap](#roadmap) below.

## Tech Stack

- **Backend** — Flask · SQLAlchemy (Flask-SQLAlchemy) · bcrypt password hashing · Flask-CORS
- **Database** — SQLite by default, PostgreSQL via `DATABASE_URL`
- **Frontend (planned)** — React 18 · React Router · Axios · Chart.js
- **Serving** — Flask dev server locally, gunicorn (`wsgi.py`) in production

## Project Structure

```
adaptive-study-partner/
├── app.py            # app factory + local dev server
├── wsgi.py           # production entry point (gunicorn wsgi:app)
├── config.py         # dev / test / prod configuration
├── models.py         # 6 SQLAlchemy models (Student, Note, Quiz, ...)
├── .env.example      # environment template
├── requirements.txt
└── package.json      # frontend stack declaration (source pending)
```

## Getting Started

### Backend

```bash
git clone https://github.com/Culzz/adaptive-study-partner.git
cd adaptive-study-partner

python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
python app.py
```

The API will be available at `http://127.0.0.1:5000`.

### Production

```bash
FLASK_ENV=prod gunicorn wsgi:app
```

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `FLASK_ENV` | `dev` | Selects `dev` / `test` / `prod` config |
| `SECRET_KEY` | dev fallback | Flask secret — **must** be set for production |
| `DATABASE_URL` | `sqlite:///study.db` | SQLAlchemy database URI |
| `FLASK_DEBUG` | `true` | Werkzeug debug mode |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Dev server bind address |

## Data Model

| Model | Purpose |
|---|---|
| `Student` | Accounts with bcrypt-hashed passwords and matric number |
| `Note` | Uploaded study notes with extracted text content (50 MB cap) |
| `Quiz` / `Question` | Quizzes with per-question difficulty |
| `QuizAttempt` | Per-answer correctness and time spent |
| `Mastery` | Per-topic mastery + forgetting risk (the adaptive core) |

## API Design (in development)

| Prefix | Planned scope |
|---|---|
| `/api/auth` | Registration, login, sessions |
| `/api/notes` | Upload, list, and read study notes |
| `/api/quizzes` | Quiz creation, attempt recording |
| `/api/performance` | Mastery, review history, forgetting-risk view |

## Roadmap

- [ ] `routes.py` — implement the four blueprints above
- [ ] React frontend scaffold (`src/`, `public/`)
- [ ] Forgetting-curve calculation behind `Mastery.forgetting_risk`
- [ ] Review-recommendation endpoint ordered by forgetting risk
- [ ] Test suite (the `TestConfig` profile is already wired for it)
- [ ] CI workflow

## License

Released under the [MIT License](LICENSE).

## Author

**Omeche Chimaobi Benedict** — [github.com/Culzz](https://github.com/Culzz) · Omechechima@gmail.com
