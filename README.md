# Adaptive Study Partner

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3-blue.svg)](https://flask.palletsprojects.com/)
[![CI](https://github.com/Culzz/adaptive-study-partner/actions/workflows/ci.yml/badge.svg)](https://github.com/Culzz/adaptive-study-partner/actions/workflows/ci.yml)

An adaptive study companion for university students: upload notes, take quizzes, and get a revision plan prioritised by **forgetting risk** — a spaced-repetition signal that estimates which topics you're about to lose.

## How it adapts

Every topic gets a mastery record. After each quiz answer the API updates it:

| Signal | Meaning |
|---|---|
| `score` (0–1) | Rolling accuracy across every attempt on the topic |
| `review_count` | How many questions you've answered on it |
| `last_reviewed` | When you last practised it |
| `forgetting_risk` (%) | Ebbinghaus-style decay: `R = exp(-t/S)`, risk = `(1-R)×100` |

Memory stability `S` grows with practice (`S = (1 + 0.5·reviews) × (0.5 + 1.5·score)` days), so well-learned topics fade slower. `/api/performance/review-plan` orders topics by risk and tells you what to review today.

## Status

**Working today (API complete, tested):**

- ✅ Student registration / login (JWT auth, bcrypt password hashing)
- ✅ Study-note upload and retrieval
- ✅ Quiz creation, answering, and per-question grading
- ✅ Mastery tracking with forgetting-risk computation
- ✅ Revision plan endpoint ordered by forgetting risk
- ✅ 5 end-to-end API tests + CI

**In development:** React frontend (see Roadmap).

## Tech Stack

- **Backend** — Flask · SQLAlchemy (Flask-SQLAlchemy) · PyJWT · bcrypt · Flask-CORS
- **Database** — SQLite by default, PostgreSQL via `DATABASE_URL`
- **Serving** — Flask dev server locally, gunicorn (`wsgi.py`) in production

## Project Structure

```
adaptive-study-partner/
├── app.py            # app factory + local dev server
├── routes.py         # the four API blueprints
├── forgetting.py     # Ebbinghaus forgetting-curve maths
├── wsgi.py           # production entry point (gunicorn wsgi:app)
├── config.py         # dev / test / prod configuration
├── models.py         # 6 SQLAlchemy models (Student, Note, Quiz, ...)
├── tests/            # end-to-end API tests (pytest)
├── .env.example      # environment template
├── requirements.txt  # runtime dependencies
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

### Run the tests

```bash
pip install -r requirements-dev.txt
pytest
```

### Production

```bash
FLASK_ENV=prod gunicorn wsgi:app
```

### Deploy on Vercel + Neon (recommended)

The backend ships as a standard Flask app — Vercel detects `wsgi.py` automatically
(zero build config), and [Neon](https://neon.tech) provides the free Postgres database.

1. **Create the database** — sign up at [neon.tech](https://neon.tech), create a free
   project, and copy the **pooled** connection string
   (`postgresql://user:pass@host/db?sslmode=require`). Add `?sslmode=require` to the
   URL yourself if it isn't already there.
2. **Import the repo** — go to [vercel.com/new](https://vercel.com/new), pick this
   repository, and let Vercel detect the framework (it shows *Flask*). The
   `.python-version` file pins Python 3.12.
3. **Set environment variables** for the Production deployment:
   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | the Neon pooled connection string |
   | `SECRET_KEY` | a long random string (e.g. `openssl rand -hex 32`) |
4. **Deploy.** On first boot the app creates its tables in Neon automatically —
   no migrations to run.

Local development needs none of this: without `DATABASE_URL` it falls back to a
SQLite file, and `python app.py` runs the dev server as before.

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `FLASK_ENV` | `dev` | Selects `dev` / `test` / `prod` config |
| `SECRET_KEY` | dev fallback | Flask secret + JWT signing — **must** be set for production |
| `DATABASE_URL` | `sqlite:///study.db` | SQLAlchemy database URI |
| `FLASK_DEBUG` | `true` | Werkzeug debug mode |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Dev server bind address |

## API Reference

Auth endpoints are public; everything else requires `Authorization: Bearer <token>`.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Create an account → returns token |
| POST | `/api/auth/login` | Verify credentials → returns token |
| GET | `/api/auth/me` | Current student profile |
| GET/POST | `/api/notes/` | List / upload a study note (`.txt`/`.md`) |
| GET | `/api/notes/<id>` | Full note content |
| GET/POST | `/api/quizzes/` | List / create a quiz (title = topic) |
| GET | `/api/quizzes/<id>` | Quiz questions (answers withheld) |
| POST | `/api/quizzes/<id>/answers` | Answer a question → grade + updated mastery |
| GET | `/api/performance/mastery` | Mastery records, most-at-risk first |
| GET | `/api/performance/review-plan` | Revision plan with action hints |

### Quick curl tour

```bash
TOKEN=$(curl -s -X POST localhost:5000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"name":"Ada","email":"ada@school.edu","password":"s3cure-pass","matric":"22/CSC/001"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['token'])")

curl -s -X POST localhost:5000/api/quizzes/ -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Operating Systems","questions":[{"question":"CPU stands for?","options":["A","B","C","D"],"correct":"Central Processing Unit"}]}'

curl -s localhost:5000/api/performance/review-plan -H "Authorization: Bearer $TOKEN"
```

## Data Model

| Model | Purpose |
|---|---|
| `Student` | Accounts with bcrypt-hashed passwords and matric number |
| `Note` | Uploaded study notes with extracted text content (50 MB cap) |
| `Quiz` / `Question` | Quizzes with per-question difficulty (quiz title = topic) |
| `QuizAttempt` | Per-answer correctness and time spent |
| `Mastery` | Per-topic score, review count, and forgetting risk |

## Roadmap

- [x] `routes.py` — auth, notes, quizzes, performance blueprints
- [x] Forgetting-curve computation behind `Mastery.forgetting_risk`
- [x] Review-plan endpoint ordered by forgetting risk
- [x] Test suite + CI
- [ ] React frontend scaffold (`src/`, `public/`)
- [ ] PDF note extraction (`pdfplumber`) — currently `.txt`/`.md` only
- [ ] Quiz generation from uploaded notes

## License

Released under the [MIT License](LICENSE).

## Author

**Omeche Chimaobi Benedict** — [github.com/Culzz](https://github.com/Culzz) · Omechechima@gmail.com
