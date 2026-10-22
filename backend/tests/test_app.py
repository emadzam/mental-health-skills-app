import json
import sqlite3
import time
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.main import create_app
from backend.provider import ProviderError
from backend.retrieval import RetrievalError, retrieve


def new_id():
    return str(uuid4())


@pytest.fixture
def setup(tmp_path):
    settings = Settings(database=tmp_path / 'test.sqlite3')
    app = create_app(settings)
    with TestClient(app) as client:
        yield client, app.state.db, settings, app


def start(client, request_id=None):
    return client.post('/api/sessions', json={'request_id': request_id or new_id(), 'cue_mode': 'circle'})


def event(client, session, action, request_id=None, **extra):
    return client.post(f"/api/sessions/{session['id']}/events", json={
        'request_id': request_id or new_id(), 'expected_version': session['version'], 'action': action, **extra})


def conversation(client):
    return client.post('/api/conversations', json={'request_id': new_id()}).json()['id']


def test_sessions_idempotency_and_payload_conflicts(setup):
    client, db, _, _ = setup
    rid = new_id()
    first = start(client, rid).json()
    assert start(client, rid).json() == first
    assert len(client.get('/api/sessions').json()) == 1
    assert client.post('/api/sessions', json={'request_id': rid, 'cue_mode': 'text'}).status_code == 409
    eid = new_id()
    stopped = event(client, first, 'stop', eid, observed_seconds=0.2).json()
    assert stopped['status'] == 'stopped'
    assert event(client, first, 'stop', eid, observed_seconds=0.2).json() == stopped
    assert event(client, stopped, 'resume').status_code == 409
    with db.connect() as con:
        assert con.execute('SELECT COUNT(*) FROM session_events').fetchone()[0] == 1


def test_pause_resume_and_completion_boundary(setup, monkeypatch):
    client, db, _, _ = setup
    clock = [1000.0]
    monkeypatch.setattr('backend.database.time.time', lambda: clock[0])
    s = start(client).json()
    assert event(client, s, 'complete').status_code == 409
    clock[0] += 10
    s = event(client, s, 'pause', reason='support').json()
    assert s['active_seconds'] == 10
    clock[0] += 30
    s = event(client, s, 'resume').json()
    assert s['paused_seconds'] == 30
    clock[0] += 50.1
    done = event(client, s, 'complete', observed_seconds=60.1).json()
    assert done['status'] == 'completed'
    assert done['active_seconds'] == pytest.approx(60.1)
    assert done['cycles_completed'] == 6


def test_restart_preserves_rows_and_does_not_duplicate(setup):
    client, _, settings, _ = setup
    s = event(client, start(client).json(), 'stop').json()
    with TestClient(create_app(settings)) as restarted:
        assert restarted.get('/api/sessions').json()[0]['id'] == s['id']
        assert len(restarted.get('/api/sessions').json()) == 1


def test_preferences_are_optional_and_can_be_forgotten(setup):
    client, _, _, _ = setup
    assert client.get('/api/preferences').json()['remember'] is False
    assert client.put('/api/preferences', json={'cue_mode': 'text', 'remember': True}).status_code == 200
    assert client.get('/api/preferences').json() == {'cue_mode': 'text', 'remember': True}
    client.put('/api/preferences', json={'cue_mode': 'text', 'remember': False})
    assert client.get('/api/preferences').json()['remember'] is False


def test_history_rag_is_grounded_and_duplicate_question_saves_once(setup):
    client, db, _, _ = setup
    stopped = event(client, start(client).json(), 'stop').json()
    cid = conversation(client)
    question = {'request_id': new_id(), 'content': 'What happened in my last session?'}
    response = client.post(f'/api/conversations/{cid}/messages', json=question)
    assert response.status_code == 200
    result = response.json()
    assert result['status'] == 'complete'
    assert stopped['id'] in result['messages'][1]['record_ids']
    assert result['retrieval'][0]['id'] == stopped['id']
    assert client.post(f'/api/conversations/{cid}/messages', json=question).json() == result
    assert len(client.get(f'/api/conversations/{cid}/messages').json()) == 2
    with db.connect() as con:
        assert con.execute('SELECT COUNT(*) FROM messages').fetchone()[0] == 2


def test_empty_retrieval_is_not_invented_history(setup):
    client, _, _, _ = setup
    cid = conversation(client)
    result = client.post(f'/api/conversations/{cid}/messages', json={'request_id': new_id(), 'content': 'What was my last session?'}).json()
    assert result['status'] == 'complete'
    assert result['retrieval'] == []
    assert 'no session records' in result['messages'][1]['content']


def test_provider_failure_saves_question_without_fake_reply(setup):
    client, _, _, _ = setup
    cid = conversation(client)
    result = client.post(f'/api/conversations/{cid}/messages', json={'request_id': new_id(), 'content': 'Explain the exercise', 'simulate_failure': True}).json()
    assert result['status'] == 'failed'
    assert len(result['messages']) == 1
    assert result['messages'][0]['status'] == 'failed'
    assert result['messages'][0]['role'] == 'user'
    assert 'Simulated' in result['error']
    assert client.get('/api/health').status_code == 200


def test_retrieval_rejects_writes_base_tables_and_cross_conversation_access(setup):
    client, db, settings, _ = setup
    a, b = conversation(client), conversation(client)
    client.post(f'/api/conversations/{a}/messages', json={'request_id': new_id(), 'content': 'Conversation A fictional question'})
    rows = retrieve(settings.database, b, 'SELECT id,content FROM message_history')
    assert rows == []
    for sql in ['DELETE FROM sessions', 'SELECT * FROM sessions', 'SELECT * FROM sqlite_master',
                'SELECT 1; DELETE FROM sessions', "SELECT load_extension('anything')", 'SELECT * FROM requests']:
        with pytest.raises(RetrievalError):
            retrieve(settings.database, a, sql)


def test_database_failure_does_not_claim_success(setup, monkeypatch):
    client, db, _, _ = setup
    def fail(_):
        raise sqlite3.OperationalError('test-only write failure')
    monkeypatch.setattr(db, 'start_session', fail)
    response = start(client)
    assert response.status_code == 503
    assert 'Do not assume' in response.json()['detail']


def test_missing_live_configuration_is_honest(tmp_path):
    with TestClient(create_app(Settings(database=tmp_path / 'live.sqlite3', model_mode='openai'))) as client:
        assert client.get('/api/health').json()['provider_configured'] is False
        cid = conversation(client)
        response = client.post(f'/api/conversations/{cid}/messages', json={'request_id': new_id(), 'content': 'Explain the exercise'}).json()
        assert response['status'] == 'failed'
        assert len(response['messages']) == 1
        assert 'not configured' in response['error']


def test_static_boundary_does_not_call_provider(setup, monkeypatch):
    client, _, _, app = setup
    async def must_not_run(*args):
        raise AssertionError('Provider should not be called')
    monkeypatch.setattr(app.state.provider, 'plan', must_not_run)
    cid = conversation(client)
    result = client.post(f'/api/conversations/{cid}/messages', json={'request_id': new_id(), 'content': 'Fictional test: self-harm'}).json()
    assert result['messages'][1]['provider_mode'] == 'static-boundary'
    assert 'independent' in result['messages'][1]['content']


def test_request_interrupted_by_restart_becomes_failed(setup):
    client, db, settings, _ = setup
    cid, rid = conversation(client), new_id()
    db.begin_request(cid, rid, 'Fictional interrupted question', 'mock', 10)
    with TestClient(create_app(settings)) as restarted:
        result = restarted.get(f'/api/conversations/{cid}/requests/{rid}').json()
        assert result['status'] == 'failed'
        assert len(result['messages']) == 1


def test_question_budget_and_input_validation(setup):
    client, _, _, _ = setup
    assert client.post('/api/sessions', json={'request_id': 'not-a-uuid'}).status_code == 422
    cid = conversation(client)
    for _ in range(10):
        assert client.post(f'/api/conversations/{cid}/messages', json={'request_id': new_id(), 'content': 'Exercise?' }).status_code == 200
    assert client.post(f'/api/conversations/{cid}/messages', json={'request_id': new_id(), 'content': 'One more'}).status_code == 409


def test_reply_database_write_failure_rolls_back_success(setup):
    client, db, _, _ = setup
    cid = conversation(client)
    with db.connect() as con:
        con.execute("CREATE TRIGGER fail_assistant BEFORE INSERT ON messages WHEN NEW.role='assistant' BEGIN SELECT RAISE(ABORT,'fictional save failure'); END")
    response = client.post(f'/api/conversations/{cid}/messages', json={'request_id': new_id(), 'content': 'Explain the exercise'})
    assert response.status_code == 503
    with db.connect() as con:
        assert con.execute("SELECT COUNT(*) FROM messages WHERE role='assistant'").fetchone()[0] == 0
        assert con.execute('SELECT status FROM requests').fetchone()[0] == 'pending'


def test_excessive_or_unmeasured_duration_cannot_complete(setup, monkeypatch):
    client, _, _, _ = setup
    clock = [1000.0]
    monkeypatch.setattr('backend.database.time.time', lambda: clock[0])
    s = start(client).json()
    clock[0] += 91
    assert event(client, s, 'complete', observed_seconds=91).status_code == 409
    assert event(client, s, 'stop', reason='timing_interruption').status_code == 200


def test_live_health_flag_requires_successful_saved_answer(tmp_path, monkeypatch):
    # Provider functions are mocked here: this is a state test, not live-call evidence.
    app = create_app(Settings(database=tmp_path / 'health.sqlite3', model_mode='openai'))
    async def plan(question):
        return 'SELECT id,status,active_seconds FROM session_history LIMIT 1'
    async def answer(question, records):
        return 'Test answer from the substituted provider.', []
    monkeypatch.setattr(app.state.provider, 'plan', plan)
    monkeypatch.setattr(app.state.provider, 'answer', answer)
    with TestClient(app) as client:
        assert client.get('/api/health').json()['live_verified'] is False
        cid = conversation(client)
        result = client.post(f'/api/conversations/{cid}/messages', json={'request_id': new_id(), 'content': 'Explain the exercise'}).json()
        assert result['status'] == 'complete'
        assert client.get('/api/health').json()['live_verified'] is True
