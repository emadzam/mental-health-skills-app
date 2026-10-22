"""Execute untrusted retrieval SQL against fixed scoped views, never write tables."""
import sqlite3
import time

from .database import DEMO

SCHEMA = '''
Only query these read-only scoped views:
session_history(id, started_at, ended_at, status, active_seconds, cue_mode)
message_history(id, role, content, created_at, status)
session_history contains only this fictional demo user's sessions.
message_history contains only the current conversation's messages.
Use one SELECT statement, no semicolons, no writes. Return IDs with records.
Use ORDER BY started_at DESC or created_at DESC when asking about the latest.
Never select from any other tables. At most 20 rows are returned.
'''


class RetrievalError(Exception):
    pass


def retrieve(path, conversation_id, query):
    if not isinstance(query, str) or len(query) > 2000 or ';' in query or not query.lstrip().upper().startswith('SELECT '):
        raise RetrievalError('Retrieval query rejected: one allowed SELECT is required.')
    # URI mode=ro rejects writes at the connection level. TEMP views provide scope;
    # authorizer denies direct base-table reads even if the model tries them.
    con = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=1)
    con.row_factory = sqlite3.Row
    try:
        con.execute('CREATE TEMP VIEW session_history AS SELECT id,started_at,ended_at,status,active_seconds,cue_mode FROM main.sessions WHERE demo_user=' + repr(DEMO))
        # UUID is passed through SQLite's own quote() before use in the view definition.
        quoted = con.execute('SELECT quote(?)', (conversation_id,)).fetchone()[0]
        con.execute('CREATE TEMP VIEW message_history AS SELECT m.id,m.role,m.content,m.created_at,m.status FROM main.messages m JOIN main.conversations c ON m.conversation_id=c.id WHERE c.demo_user=' + repr(DEMO) + ' AND m.conversation_id=' + quoted)
        con.execute('PRAGMA query_only = ON')
        views = {'session_history', 'message_history'}
        allowed_functions = {'count', 'max', 'min', 'sum', 'avg', 'round', 'coalesce', 'lower', 'upper', 'length'}

        def authorize(action, arg1, arg2, database, source):
            if action == sqlite3.SQLITE_SELECT:
                return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_READ:
                if (database == 'temp' and arg1 in views) or (database == 'main' and source in views):
                    return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_FUNCTION and (arg2 or '').lower() in allowed_functions:
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY

        deadline = time.monotonic() + 0.1
        con.set_authorizer(authorize)
        con.set_progress_handler(lambda: int(time.monotonic() > deadline), 100)
        rows = con.execute('SELECT * FROM (' + query + ') LIMIT 20').fetchall()
        records = []
        remaining = 12000
        for row in rows:
            item = {k: (v[:1000] if isinstance(v, str) else v) for k, v in dict(row).items()}
            size = len(str(item))
            if size > remaining:
                break
            remaining -= size
            records.append(item)
        return records
    except sqlite3.Error as exc:
        raise RetrievalError('Retrieval query rejected or could not run safely.') from exc
    finally:
        con.close()
