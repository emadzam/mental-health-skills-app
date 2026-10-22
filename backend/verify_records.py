"""Compare current fictional SQLite records with the running HTTP API, read-only."""
import json

import httpx

from .config import ROOT
from .database import Database


def verify():
    db = Database(ROOT / 'data' / 'app.sqlite3')
    with httpx.Client(base_url='http://127.0.0.1:8000', timeout=10) as client:
        response = client.get('/api/sessions')
        response.raise_for_status()
        api_sessions = response.json()
        db_sessions = db.sessions()
        keys = ('id', 'status', 'active_seconds', 'paused_seconds', 'observed_seconds')
        assert [{k: s[k] for k in keys} for s in api_sessions] == [{k: s[k] for k in keys} for s in db_sessions]
        conversations = client.get('/api/conversations').json()
        ids = []
        for c in conversations:
            response = client.get(f"/api/conversations/{c['id']}/messages")
            response.raise_for_status()
            api_messages = response.json()
            db_messages = db.messages(c['id'])
            keys = ('id', 'role', 'content', 'status', 'record_ids')
            assert [{k: m[k] for k in keys} for m in api_messages] == [{k: m[k] for k in keys} for m in db_messages]
            ids.extend(m['id'] for m in api_messages)
        assert len(ids) == len(set(ids)), 'Duplicate message IDs'
        return {'result': 'SQLite and API agree', 'sessions': [s['id'] for s in api_sessions],
                'conversation_ids': [c['id'] for c in conversations], 'message_ids': ids}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
