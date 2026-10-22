import asyncio
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import ROOT, Settings, load_settings
from .database import Conflict, Database, Missing
from .models import (ConversationIn, ConversationOut, Health, MessageOut, Preference,
                     PreferenceOut, Question, RequestOut, SessionEvent, SessionOut, StartSession)
from .provider import BOUNDARY, Provider, ProviderError, crisis_related
from .retrieval import RetrievalError, retrieve


def create_app(settings: Settings | None = None):
    settings = settings or load_settings()
    db = Database(settings.database)
    provider = Provider(settings)

    @asynccontextmanager
    async def lifespan(app):
        db.init()
        yield

    app = FastAPI(title='Breathing Break — coursework API', lifespan=lifespan)
    app.state.db = db
    app.state.provider = provider
    app.state.live_verified = False

    @app.exception_handler(Conflict)
    async def conflict(request, exc):
        return JSONResponse(status_code=409, content={'detail': str(exc)})

    @app.exception_handler(Missing)
    async def missing(request, exc):
        return JSONResponse(status_code=404, content={'detail': str(exc)})

    @app.exception_handler(sqlite3.Error)
    async def database_error(request, exc):
        return JSONResponse(status_code=503, content={'detail': 'The database could not save or load this operation. Do not assume it was saved. Retry with the same request ID.'})

    @app.middleware('http')
    async def local_only(request: Request, call_next):
        # Local fictional demo only; no authentication or real-user service is implied.
        if request.url.path.startswith('/api'):
            origin = request.headers.get('origin')
            if origin and origin not in ('http://127.0.0.1:5173', 'http://localhost:5173', 'http://127.0.0.1:8000', 'http://localhost:8000'):
                return JSONResponse(status_code=403, content={'detail': 'Use the local coursework interface.'})
            length = request.headers.get('content-length')
            if length and (not length.isdigit() or int(length) > 16000):
                return JSONResponse(status_code=413, content={'detail': 'Request too large.'})
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.get('/api/health', response_model=Health)
    def health():
        return {'status': 'ok', 'model_mode': settings.model_mode,
                'provider_configured': bool(settings.api_key and settings.model),
                'live_verified': app.state.live_verified}

    @app.get('/api/sessions', response_model=list[SessionOut])
    def sessions():
        return db.sessions()

    @app.post('/api/sessions', response_model=SessionOut)
    def start_session(body: StartSession):
        return db.start_session(body)

    @app.post('/api/sessions/{session_id}/events', response_model=SessionOut)
    def session_event(session_id: UUID, body: SessionEvent):
        return db.session_event(str(session_id), body)

    @app.get('/api/preferences', response_model=PreferenceOut)
    def preference():
        return db.preference()

    @app.put('/api/preferences', response_model=PreferenceOut)
    def save_preference(body: Preference):
        return db.save_preference(body)

    @app.post('/api/conversations', response_model=ConversationOut)
    def conversation(body: ConversationIn):
        return db.conversation(body.request_id)

    @app.get('/api/conversations', response_model=list[ConversationOut])
    def conversations():
        return db.conversations()

    @app.get('/api/conversations/{conversation_id}/messages', response_model=list[MessageOut])
    def messages(conversation_id: UUID):
        return db.messages(str(conversation_id))

    @app.get('/api/conversations/{conversation_id}/requests/{request_id}', response_model=RequestOut)
    def request_result(conversation_id: UUID, request_id: UUID):
        result = db.request_result(str(request_id))
        if result['messages'] and result['messages'][0]['conversation_id'] != str(conversation_id):
            raise Missing('Request not found in this conversation.')
        return result

    @app.post('/api/conversations/{conversation_id}/messages', response_model=RequestOut)
    async def ask(conversation_id: UUID, body: Question):
        cid, rid = str(conversation_id), str(body.request_id)
        if body.simulate_failure and settings.model_mode != 'mock':
            raise HTTPException(422, 'Failure simulation is only available in mock mode.')
        fresh = db.begin_request(cid, rid, body.content, settings.model_mode, settings.max_questions)
        if not fresh:
            return db.request_result(rid)
        records, query = [], None
        try:
            if body.simulate_failure:
                raise ProviderError('Simulated provider failure for coursework verification. No assistant reply was saved.')
            if crisis_related(body.content):
                db.finish_request(rid, answer=BOUNDARY, mode='static-boundary')
            else:
                # Two calls maximum; each has a finite timeout, plus an overall request bound.
                async with asyncio.timeout(2 * settings.timeout + 3):
                    query = await provider.plan(body.content)
                    records = retrieve(settings.database, cid, query)
                    answer, ids = await provider.answer(body.content, records)
                db.finish_request(rid, answer=answer, record_ids=ids, records=records, query=query)
                if settings.model_mode == 'openai':
                    app.state.live_verified = True
        except (ProviderError, RetrievalError, TimeoutError) as exc:
            message = str(exc) or 'The request timed out. No assistant reply was saved.'
            db.finish_request(rid, records=records, query=query, error=message)
        return db.request_result(rid)

    # Build once, then serve Vue from the same local origin. Vite dev proxies /api.
    dist = ROOT / 'frontend' / 'dist'
    if dist.exists():
        app.mount('/', StaticFiles(directory=dist, html=True), name='frontend')
    return app


app = create_app()
