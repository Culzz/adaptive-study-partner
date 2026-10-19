"""End-to-end API tests: register → login → notes → quiz → mastery → review plan."""

import pytest

from app import create_app
from models import Student, db


@pytest.fixture()
def client():
    app = create_app('test')
    with app.test_client() as client:
        yield client
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def auth(client):
    """Register a student and return auth headers + id."""
    resp = client.post('/api/auth/register', json={
        'name': 'Test Student', 'email': 'test@student.com',
        'password': 's3cure-pass', 'matric': '22/CSC/001', 'level': '300',
    })
    assert resp.status_code == 201
    token = resp.get_json()['token']
    return {'Authorization': f'Bearer {token}'}


QUIZ = {
    'title': 'Operating Systems',
    'questions': [
        {'question': 'What does CPU stand for?', 'options': ['A', 'B', 'C', 'D'],
         'correct': 'Central Processing Unit', 'difficulty': 1.0},
        {'question': 'Which is a deadlock condition?', 'options': ['A', 'B', 'C', 'D'],
         'correct': 'Mutual Exclusion', 'difficulty': 1.0},
    ],
}


def test_register_and_login(client, auth):
    resp = client.post('/api/auth/login', json={
        'email': 'test@student.com', 'password': 's3cure-pass'})
    assert resp.status_code == 200
    assert resp.get_json()['student']['matric'] == '22/CSC/001'

    bad = client.post('/api/auth/login', json={
        'email': 'test@student.com', 'password': 'wrong'})
    assert bad.status_code == 401


def test_endpoints_require_auth(client):
    for path in ('/api/auth/me', '/api/notes/', '/api/quizzes/', '/api/performance/mastery'):
        assert client.get(path).status_code == 401


def test_note_upload_and_read(client, auth):
    resp = client.post('/api/notes/', headers=auth, json={
        'filename': 'os.txt', 'content': 'Deadlock: mutual exclusion, hold and wait...'})
    assert resp.status_code == 201
    note_id = resp.get_json()['id']

    listing = client.get('/api/notes/', headers=auth)
    assert len(listing.get_json()) == 1

    full = client.get(f'/api/notes/{note_id}', headers=auth)
    assert 'Deadlock' in full.get_json()['content']


def test_quiz_flow_updates_mastery_and_risk(client, auth):
    quiz_id = client.post('/api/quizzes/', json=QUIZ, headers=auth).get_json()['id']
    questions = client.get(f'/api/quizzes/{quiz_id}', headers=auth).get_json()['questions']

    first = client.post(f'/api/quizzes/{quiz_id}/answers', headers=auth, json={
        'question_id': questions[0]['id'], 'answer': 'Central Processing Unit'})
    assert first.get_json()['is_correct'] is True

    second = client.post(f'/api/quizzes/{quiz_id}/answers', headers=auth, json={
        'question_id': questions[1]['id'], 'answer': 'wrong guess'})
    mastery = second.get_json()['mastery']
    assert mastery['score'] == 0.5          # 1 of 2 correct
    assert mastery['review_count'] == 2
    assert mastery['forgetting_risk'] < 100  # freshly reviewed


def test_review_plan_ordered_by_risk(client, auth):
    quiz_id = client.post('/api/quizzes/', json=QUIZ, headers=auth).get_json()['id']
    questions = client.get(f'/api/quizzes/{quiz_id}', headers=auth).get_json()['questions']
    client.post(f'/api/quizzes/{quiz_id}/answers', headers=auth, json={
        'question_id': questions[0]['id'], 'answer': 'Central Processing Unit'})

    plan = client.get('/api/performance/review-plan', headers=auth).get_json()
    assert plan and plan[0]['topic'] == 'Operating Systems'
    assert plan[0]['action'] in ('review today', 'review this week', 'still fresh')
