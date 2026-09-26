"""GeminiService: schema enforcement and failure handling with a mocked SDK client."""

from types import SimpleNamespace

import pytest

from app.config import Settings
from app.schemas.analysis import DocumentTypeOutput
from app.services import gemini_service
from app.services.gemini_service import GeminiService, ModelOutputError, ModelUnavailableError


class _FakeModels:
    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []

    def generate_content(self, *, model, contents, config):
        self.requests.append((model, contents, config))
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return SimpleNamespace(text=response)


class _TransientError(Exception):
    """Mirrors google-genai ServerError/ClientError, which expose an HTTP `code`."""

    def __init__(self, code: int = 503) -> None:
        super().__init__(f"{code} UNAVAILABLE")
        self.code = code


def _service(monkeypatch, responses, **settings_kwargs):
    from google import genai

    fake_models = _FakeModels(responses)
    monkeypatch.setattr(genai, "Client", lambda api_key: SimpleNamespace(models=fake_models))
    monkeypatch.setattr(gemini_service.time, "sleep", lambda _: None)  # no real backoff in tests
    settings = Settings(
        **{
            "gemini_api_key": "test-key",
            "gemini_analysis_model": "analysis-model",
            "gemini_chat_model": "chat-model",
            "gemini_fallback_models": "",
            **settings_kwargs,
        }
    )
    return GeminiService(settings), fake_models


def test_valid_json_is_parsed_into_schema(monkeypatch):
    service, fake = _service(monkeypatch, ['{"document_type": "RENTAL", "title": "Residential Lease"}'])
    output = service.generate("classify", DocumentTypeOutput)
    assert output.document_type == "RENTAL"
    model, _, config = fake.requests[0]
    assert model == "analysis-model"
    assert config.response_mime_type == "application/json"
    assert "UNTRUSTED DATA" in config.system_instruction


def test_conversational_flag_uses_chat_model(monkeypatch):
    service, fake = _service(monkeypatch, ['{"document_type": "NDA", "title": "NDA"}'])
    service.generate("q", DocumentTypeOutput, conversational=True)
    assert fake.requests[0][0] == "chat-model"


def test_malformed_output_is_retried_then_rejected(monkeypatch):
    service, fake = _service(monkeypatch, ["not json", '{"document_type": "NOT_A_TYPE", "title": 1}'])
    with pytest.raises(ModelOutputError):
        service.generate("classify", DocumentTypeOutput)
    assert len(fake.requests) == 2


def test_transport_failure_is_surfaced_as_unavailable(monkeypatch):
    service, fake = _service(monkeypatch, [RuntimeError("quota exceeded")])
    with pytest.raises(ModelUnavailableError):
        service.generate("classify", DocumentTypeOutput)
    assert len(fake.requests) == 1, "a non-transient error must not be retried"


def test_transient_capacity_error_is_retried_then_succeeds(monkeypatch):
    """Popular models return 503 under load; a brief retry should absorb it."""
    service, fake = _service(
        monkeypatch,
        [_TransientError(503), _TransientError(503), '{"document_type": "EMPLOYMENT", "title": "Employment Agreement"}'],
    )
    output = service.generate("classify", DocumentTypeOutput)
    assert output.document_type == "EMPLOYMENT"
    assert len(fake.requests) == 3


def test_persistent_capacity_error_becomes_unavailable(monkeypatch):
    service, fake = _service(monkeypatch, [_TransientError(503) for _ in range(10)])
    with pytest.raises(ModelUnavailableError):
        service.generate("classify", DocumentTypeOutput)
    assert len(fake.requests) == gemini_service.TRANSIENT_ATTEMPTS


def test_rate_limit_is_not_retried(monkeypatch):
    """429 means quota is already exhausted; retrying deepens the limit, so fail fast."""
    service, fake = _service(
        monkeypatch, [_TransientError(429), '{"document_type": "NDA", "title": "NDA"}']
    )
    with pytest.raises(ModelUnavailableError):
        service.generate("classify", DocumentTypeOutput)
    assert len(fake.requests) == 1


def test_unavailable_primary_falls_back_to_next_model(monkeypatch):
    service, fake = _service(
        monkeypatch,
        [_TransientError(503), _TransientError(503), '{"document_type": "EMPLOYMENT", "title": "Employment Agreement"}'],
        gemini_fallback_models="gemini-3.6-flash,gemini-3.5-flash",
    )
    output = service.generate("classify", DocumentTypeOutput)
    assert output.document_type == "EMPLOYMENT"
    assert [request[0] for request in fake.requests] == ["analysis-model", "analysis-model", "gemini-3.6-flash"]


def test_rate_limit_moves_to_fallback_without_retrying_the_same_model(monkeypatch):
    service, fake = _service(
        monkeypatch,
        [_TransientError(429), '{"document_type": "NDA", "title": "NDA"}'],
        gemini_fallback_models="gemini-3.6-flash",
    )
    output = service.generate("classify", DocumentTypeOutput)
    assert output.document_type == "NDA"
    assert [request[0] for request in fake.requests] == ["analysis-model", "gemini-3.6-flash"]


def test_fallback_chain_skips_a_duplicate_of_the_primary(monkeypatch):
    service, fake = _service(
        monkeypatch,
        [_TransientError(503), _TransientError(503), '{"document_type": "RENTAL", "title": "Lease"}'],
        gemini_analysis_model="gemini-3.6-flash",
        gemini_fallback_models="gemini-3.6-flash,gemini-3.5-flash",
    )
    output = service.generate("classify", DocumentTypeOutput)
    assert output.document_type == "RENTAL"
    assert [request[0] for request in fake.requests] == ["gemini-3.6-flash", "gemini-3.6-flash", "gemini-3.5-flash"]


def test_service_requires_api_key():
    with pytest.raises(ModelUnavailableError):
        GeminiService(Settings(gemini_api_key=None))
