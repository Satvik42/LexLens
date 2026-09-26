"""Gemini access through the google-genai SDK with schema-constrained output.

The analysis model and the conversational model are configured separately so either can change independently.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.config import Settings
from app.prompts.system import BASE_SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)

TModel = TypeVar("TModel", bound=BaseModel)

_MAX_ATTEMPTS = 2
_TEMPERATURE = 0.1

# In-demand models answer 503 rather than queueing, which a short retry absorbs. 429 is deliberately
# excluded: it means quota is already exhausted, and retrying the same model deepens the limit.
TRANSIENT_ATTEMPTS = 5
# When fallback models are configured, leave a dead model quickly and try the next one.
_CHAIN_TRANSIENT_ATTEMPTS = 2
_TRANSIENT_CODES = frozenset({503})
_BACKOFF_SECONDS = 2.0


class ModelOutputError(Exception):
    """The model returned output that failed schema validation after retries."""


class ModelUnavailableError(Exception):
    """Gemini is not configured or the request failed."""


class StructuredModel(ABC):
    """Minimal interface the rest of the application depends on (allows fake clients in tests)."""

    @abstractmethod
    def generate(self, prompt: str, schema: type[TModel], *, conversational: bool = False) -> TModel: ...


class GeminiService(StructuredModel):
    def __init__(self, settings: Settings) -> None:
        if not settings.uses_gemini:
            raise ModelUnavailableError("GEMINI_API_KEY is not configured")
        from google import genai

        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._analysis_model = settings.gemini_analysis_model
        self._chat_model = settings.gemini_chat_model
        self._fallback_models = settings.gemini_fallback_model_list()

    def generate(self, prompt: str, schema: type[TModel], *, conversational: bool = False) -> TModel:
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=BASE_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=schema,
            temperature=_TEMPERATURE,
        )
        chain = self._model_chain(conversational)
        attempts = _CHAIN_TRANSIENT_ATTEMPTS if len(chain) > 1 else TRANSIENT_ATTEMPTS
        last_unavailable: ModelUnavailableError | None = None
        for model in chain:
            try:
                return self._generate_validated(model, prompt, schema, config, attempts)
            except ModelUnavailableError as exc:
                last_unavailable = exc
                logger.warning("Gemini model unavailable (%s); trying the next model", model)
        raise last_unavailable or ModelUnavailableError("The analysis service is temporarily unavailable")

    def _model_chain(self, conversational: bool) -> list[str]:
        primary = self._chat_model if conversational else self._analysis_model
        chain: list[str] = []
        for model in (primary, *self._fallback_models):
            if model and model not in chain:
                chain.append(model)
        return chain

    def _generate_validated(self, model: str, prompt: str, schema: type[TModel], config, attempts: int) -> TModel:
        last_error: Exception | None = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            response = self._generate_content(model, prompt, config, attempts)
            try:
                parsed = schema.model_validate_json(response.text or "")
                logger.info("Gemini structured output accepted from %s", model)
                return parsed
            except ValidationError as exc:
                last_error = exc
                logger.info("Model output failed schema validation (attempt %s/%s)", attempt, _MAX_ATTEMPTS)
        raise ModelOutputError("Model output did not match the expected schema") from last_error

    def _generate_content(self, model: str, prompt: str, config, attempts: int = TRANSIENT_ATTEMPTS):
        """Call Gemini, retrying transient capacity errors with linear backoff."""
        for attempt in range(1, attempts + 1):
            try:
                return self._client.models.generate_content(model=model, contents=prompt, config=config)
            except Exception as exc:  # network / quota / safety - surfaced as a generic unavailability
                retryable = getattr(exc, "code", None) in _TRANSIENT_CODES and attempt < attempts
                if not retryable:
                    logger.warning("Gemini request failed (%s): %s", model, exc.__class__.__name__)
                    raise ModelUnavailableError("The analysis service is temporarily unavailable") from exc
                logger.info("Gemini busy (%s), retrying %s/%s", model, attempt, attempts)
                time.sleep(_BACKOFF_SECONDS * attempt)
