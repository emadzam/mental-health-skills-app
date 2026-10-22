"""Explicit local configuration. No setting values are returned by health checks."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    database: Path = ROOT / 'data' / 'app.sqlite3'
    model_mode: str = 'mock'
    api_key: str = ''
    model: str = ''
    timeout: float = 20
    max_questions: int = 10


def load_settings():
    load_dotenv(ROOT / 'backend' / '.env', override=False)
    mode = os.getenv('MODEL_MODE', 'mock')
    if mode not in ('mock', 'openai'):
        raise ValueError('MODEL_MODE must be mock or openai')
    return Settings(
        model_mode=mode,
        api_key=os.getenv('OPENAI_API_KEY', ''),
        model=os.getenv('OPENAI_MODEL', ''),
        timeout=min(30, max(1, float(os.getenv('PROVIDER_TIMEOUT_SECONDS', '20')))),
        max_questions=min(20, max(1, int(os.getenv('MAX_QUESTIONS_PER_CONVERSATION', '10')))),
    )
