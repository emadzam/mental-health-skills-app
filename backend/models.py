from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class StartSession(Input):
    request_id: UUID
    cue_mode: Literal['circle', 'text'] = 'circle'


class SessionEvent(Input):
    request_id: UUID
    action: Literal['pause', 'resume', 'stop', 'complete']
    expected_version: int = Field(ge=1)
    reason: Literal['user', 'support', 'hidden', 'refresh', 'timing_interruption'] = 'user'
    observed_seconds: float | None = Field(default=None, ge=0, le=86400, allow_inf_nan=False)


class SessionOut(BaseModel):
    id: str
    started_at: datetime
    ended_at: datetime | None
    status: Literal['active', 'paused', 'stopped', 'completed']
    cue_mode: str
    active_seconds: float
    paused_seconds: float
    observed_seconds: float | None
    cycles_completed: int
    version: int
    stop_reason: str | None


class Preference(Input):
    cue_mode: Literal['circle', 'text']
    remember: bool


class PreferenceOut(BaseModel):
    cue_mode: str
    remember: bool


class ConversationIn(Input):
    request_id: UUID


class ConversationOut(BaseModel):
    id: str
    created_at: str


class Question(Input):
    request_id: UUID
    content: str = Field(min_length=1, max_length=1000)
    simulate_failure: bool = False


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: str
    status: str
    provider_mode: str
    record_ids: list[str]


class RequestOut(BaseModel):
    request_id: str
    status: str
    messages: list[MessageOut]
    error: str | None = None
    retrieval: list[dict] = []
    query: str | None = None


class Health(BaseModel):
    status: str
    model_mode: str
    provider_configured: bool
    live_verified: bool = False
    demo_user: str = 'Fictional student'


class ErrorOut(BaseModel):
    detail: str
