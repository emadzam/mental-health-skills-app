import asyncio
import json

import httpx
import pytest

from backend.config import Settings
from backend.provider import Provider, ProviderError


def test_provider_uses_strict_schema_and_checks_actual_transport_reply(monkeypatch):
    sent = []
    def handler(request):
        payload = json.loads(request.content)
        sent.append(payload)
        assert payload['text']['format']['type'] == 'json_schema'
        assert payload['text']['format']['strict'] is True
        assert payload['store'] is False
        return httpx.Response(200, json={'status': 'completed', 'output': [
            {'type': 'message', 'content': [{'type': 'output_text', 'text': '{"sql":"SELECT id FROM session_history LIMIT 1"}'}]}]})
    original = httpx.AsyncClient
    monkeypatch.setattr('backend.provider.httpx.AsyncClient', lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))
    provider = Provider(Settings(model_mode='openai', api_key='dummy-not-a-real-key', model='test-model'))
    assert asyncio.run(provider.plan('A fictional history question')) == 'SELECT id FROM session_history LIMIT 1'
    assert provider.attempted_calls == 1
    assert len(sent) == 1


def test_provider_error_does_not_expose_response_body_or_key(monkeypatch):
    def handler(request):
        return httpx.Response(400, json={'error': {'param': 'text.format', 'message': 'dummy-private-detail'}})
    original = httpx.AsyncClient
    monkeypatch.setattr('backend.provider.httpx.AsyncClient', lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))
    provider = Provider(Settings(model_mode='openai', api_key='dummy-not-a-real-key', model='test-model'))
    with pytest.raises(ProviderError) as caught:
        asyncio.run(provider.plan('Fictional question'))
    assert 'text.format' in str(caught.value)
    assert 'dummy-private-detail' not in str(caught.value)
    assert 'dummy-not-a-real-key' not in str(caught.value)
