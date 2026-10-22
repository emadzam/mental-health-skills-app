import json
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

DEMO = 'fictional-student'


def now():
    return datetime.now(timezone.utc).isoformat()


def uid():
    return str(uuid4())


class Conflict(Exception):
    pass


class Missing(Exception):
    pass


class Database:
    def __init__(self, path):
        self.path = path

    @contextmanager
    def connect(self):
        con = sqlite3.connect(self.path, timeout=5)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys = ON')
        try:
            with con:
                yield con
        finally:
            con.close()

    def init(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as con:
            con.executescript('''
            CREATE TABLE IF NOT EXISTS sessions (
              id TEXT PRIMARY KEY, demo_user TEXT NOT NULL,
              request_id TEXT NOT NULL UNIQUE, cue_mode TEXT NOT NULL,
              started_at TEXT NOT NULL, ended_at TEXT, status TEXT NOT NULL,
              active_seconds REAL NOT NULL DEFAULT 0,
              paused_seconds REAL NOT NULL DEFAULT 0,
              observed_seconds REAL, segment_start REAL NOT NULL,
              version INTEGER NOT NULL DEFAULT 1, stop_reason TEXT);
            CREATE TABLE IF NOT EXISTS session_events (
              request_id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id),
              payload TEXT NOT NULL, result TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS preferences (
              demo_user TEXT PRIMARY KEY, cue_mode TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS conversations (
              id TEXT PRIMARY KEY, demo_user TEXT NOT NULL,
              request_id TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS requests (
              id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES conversations(id),
              question TEXT NOT NULL, status TEXT NOT NULL, error TEXT,
              retrieval TEXT NOT NULL DEFAULT '[]', query TEXT,
              provider_mode TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS messages (
              sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL UNIQUE,
              conversation_id TEXT NOT NULL REFERENCES conversations(id),
              request_id TEXT NOT NULL REFERENCES requests(id),
              role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL,
              status TEXT NOT NULL, provider_mode TEXT NOT NULL,
              record_ids TEXT NOT NULL DEFAULT '[]', UNIQUE(request_id, role));
            CREATE INDEX IF NOT EXISTS messages_conversation ON messages(conversation_id, sequence);
            ''')
            # A request interrupted by an actual service restart must not remain pending forever.
            con.execute("UPDATE messages SET status='failed' WHERE request_id IN (SELECT id FROM requests WHERE status='pending')")
            con.execute("UPDATE requests SET status='failed', error='Request interrupted by backend restart; no reply was saved.' WHERE status='pending'")

    @staticmethod
    def session(row):
        data = dict(row)
        data['cycles_completed'] = min(6, int(data['active_seconds'] // 10))
        return data

    def start_session(self, body):
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT * FROM sessions WHERE request_id=? AND demo_user=?',
                              (str(body.request_id), DEMO)).fetchone()
            if row:
                if row['cue_mode'] != body.cue_mode:
                    raise Conflict('This request ID was already used with different data.')
                return self.session(row)
            session_id = uid()
            con.execute('INSERT INTO sessions(id,demo_user,request_id,cue_mode,started_at,status,segment_start) VALUES(?,?,?,?,?,?,?)',
                        (session_id, DEMO, str(body.request_id), body.cue_mode, now(), 'active', time.time()))
            return self.session(con.execute('SELECT * FROM sessions WHERE id=?', (session_id,)).fetchone())

    def sessions(self):
        with self.connect() as con:
            return [self.session(r) for r in con.execute('SELECT * FROM sessions WHERE demo_user=? ORDER BY started_at DESC,id DESC LIMIT 100', (DEMO,))]

    def session_event(self, session_id, body):
        payload = body.model_dump_json()
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            cached = con.execute('SELECT * FROM session_events WHERE request_id=?', (str(body.request_id),)).fetchone()
            if cached:
                if cached['session_id'] != session_id or cached['payload'] != payload:
                    raise Conflict('This event ID was already used with different data.')
                return json.loads(cached['result'])
            row = con.execute('SELECT * FROM sessions WHERE id=? AND demo_user=?', (session_id, DEMO)).fetchone()
            if not row:
                raise Missing('Session not found.')
            data = dict(row)
            if data['version'] != body.expected_version:
                raise Conflict('Session changed. Refresh history before continuing.')
            valid = {'active': ('pause', 'stop', 'complete'), 'paused': ('resume', 'stop')}
            if body.action not in valid.get(data['status'], ()):
                raise Conflict('This session cannot accept that action.')
            current = time.time()
            elapsed = max(0, current - data['segment_start'])
            data['active_seconds' if data['status'] == 'active' else 'paused_seconds'] += elapsed
            if body.action == 'complete' and (not 60 <= data['active_seconds'] <= 90
                    or body.observed_seconds is None or not 60 <= body.observed_seconds <= 90):
                raise Conflict('Completion needs a full guided sequence within 90 seconds. Stop this interrupted session instead.')
            data['status'] = {'pause': 'paused', 'resume': 'active', 'stop': 'stopped', 'complete': 'completed'}[body.action]
            data['version'] += 1
            data['segment_start'] = current
            if body.action in ('stop', 'complete'):
                data['ended_at'] = now()
                data['stop_reason'] = body.reason if body.action == 'stop' else None
                data['observed_seconds'] = body.observed_seconds
            con.execute('''UPDATE sessions SET status=:status,active_seconds=:active_seconds,
              paused_seconds=:paused_seconds,observed_seconds=:observed_seconds,ended_at=:ended_at,
              segment_start=:segment_start,version=:version,stop_reason=:stop_reason WHERE id=:id''', data)
            result = self.session(data)
            con.execute('INSERT INTO session_events VALUES(?,?,?,?)',
                        (str(body.request_id), session_id, payload, json.dumps(result)))
            return result

    def preference(self):
        with self.connect() as con:
            row = con.execute('SELECT cue_mode FROM preferences WHERE demo_user=?', (DEMO,)).fetchone()
            return {'cue_mode': row['cue_mode'] if row else 'circle', 'remember': bool(row)}

    def save_preference(self, body):
        with self.connect() as con:
            if body.remember:
                con.execute('INSERT INTO preferences VALUES(?,?,?) ON CONFLICT(demo_user) DO UPDATE SET cue_mode=excluded.cue_mode,updated_at=excluded.updated_at', (DEMO, body.cue_mode, now()))
            else:
                con.execute('DELETE FROM preferences WHERE demo_user=?', (DEMO,))
        return {'cue_mode': body.cue_mode, 'remember': body.remember}

    def conversation(self, request_id):
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT id,created_at FROM conversations WHERE request_id=? AND demo_user=?', (str(request_id), DEMO)).fetchone()
            if row:
                return dict(row)
            value = {'id': uid(), 'created_at': now()}
            con.execute('INSERT INTO conversations VALUES(?,?,?,?)', (value['id'], DEMO, str(request_id), value['created_at']))
            return value

    def conversations(self):
        with self.connect() as con:
            return [dict(r) for r in con.execute('SELECT id,created_at FROM conversations WHERE demo_user=? ORDER BY created_at DESC LIMIT 100', (DEMO,))]

    @staticmethod
    def message(row):
        result = dict(row)
        result['record_ids'] = json.loads(result['record_ids'])
        return result

    def messages(self, conversation_id):
        with self.connect() as con:
            self.require_conversation(con, conversation_id)
            return [self.message(r) for r in con.execute('SELECT * FROM messages WHERE conversation_id=? ORDER BY sequence LIMIT 200', (conversation_id,))]

    @staticmethod
    def require_conversation(con, conversation_id):
        if not con.execute('SELECT id FROM conversations WHERE id=? AND demo_user=?', (conversation_id, DEMO)).fetchone():
            raise Missing('Conversation not found.')

    def request_result(self, request_id):
        with self.connect() as con:
            row = con.execute('SELECT * FROM requests WHERE id=?', (request_id,)).fetchone()
            if not row:
                raise Missing('Request not found.')
            messages = [self.message(r) for r in con.execute('SELECT * FROM messages WHERE request_id=? ORDER BY sequence', (request_id,))]
            return {'request_id': row['id'], 'status': row['status'], 'messages': messages,
                    'error': row['error'], 'retrieval': json.loads(row['retrieval']), 'query': row['query']}

    def begin_request(self, conversation_id, request_id, question, mode, budget):
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            self.require_conversation(con, conversation_id)
            existing = con.execute('SELECT * FROM requests WHERE id=?', (request_id,)).fetchone()
            if existing:
                if existing['conversation_id'] != conversation_id or existing['question'] != question:
                    raise Conflict('This request ID was already used with different data.')
                return False
            count = con.execute('SELECT COUNT(*) FROM requests WHERE conversation_id=?', (conversation_id,)).fetchone()[0]
            if count >= budget:
                raise Conflict('Conversation question limit reached. Start a new conversation to continue.')
            created = now()
            con.execute('INSERT INTO requests(id,conversation_id,question,status,provider_mode,created_at) VALUES(?,?,?,?,?,?)',
                        (request_id, conversation_id, question, 'pending', mode, created))
            con.execute('INSERT INTO messages(id,conversation_id,request_id,role,content,created_at,status,provider_mode) VALUES(?,?,?,?,?,?,?,?)',
                        (uid(), conversation_id, request_id, 'user', question, created, 'pending', mode))
            return True

    def finish_request(self, request_id, answer=None, record_ids=None, records=None, query=None, error=None, mode=None):
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            req = con.execute('SELECT * FROM requests WHERE id=?', (request_id,)).fetchone()
            if not req or req['status'] != 'pending':
                raise Conflict('Request is not pending.')
            status = 'failed' if error else 'complete'
            con.execute('UPDATE requests SET status=?,error=?,retrieval=?,query=? WHERE id=?',
                        (status, error, json.dumps(records or []), query, request_id))
            con.execute('UPDATE messages SET status=? WHERE request_id=?', (status, request_id))
            if answer is not None and not error:
                con.execute('INSERT INTO messages(id,conversation_id,request_id,role,content,created_at,status,provider_mode,record_ids) VALUES(?,?,?,?,?,?,?,?,?)',
                            (uid(), req['conversation_id'], request_id, 'assistant', answer, now(), status, mode or req['provider_mode'], json.dumps(record_ids or [])))
