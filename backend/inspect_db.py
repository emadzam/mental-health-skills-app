"""Read-only inspection of the fictional database; never seeds or changes rows."""
import json
import sqlite3
from pathlib import Path


def inspect(path):
    con = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    try:
        schema = [dict(r) for r in con.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name")]
        sessions = [dict(r) for r in con.execute('SELECT id,status,started_at,ended_at,active_seconds,paused_seconds,observed_seconds,stop_reason FROM sessions ORDER BY started_at DESC LIMIT 10')]
        messages = [dict(r) for r in con.execute('SELECT id,conversation_id,request_id,role,content,status,provider_mode,record_ids FROM messages ORDER BY sequence DESC LIMIT 12')]
        counts = {name: con.execute('SELECT COUNT(*) FROM ' + name).fetchone()[0]
                  for name in ('sessions', 'session_events', 'conversations', 'messages', 'requests', 'preferences')}
        return {'database': str(path), 'counts': counts, 'schema': schema, 'sessions': sessions, 'messages': messages}
    finally:
        con.close()


if __name__ == '__main__':
    print(json.dumps(inspect(Path(__file__).resolve().parents[1] / 'data' / 'app.sqlite3'), indent=2))
