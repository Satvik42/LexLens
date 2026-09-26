# Gemini Availability Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep document analysis and grounded questions available by skipping a Gemini model that just hit a rate limit or a repeated outage, and starting the next request on the next model that can answer.

**Architecture:** `ModelCooldown` stores model-id to “try again after” on the `GeminiService` instance created at process startup. `generate` walks one shared chain, records a 60-second cooldown on HTTP 429 and a 20-second cooldown after a repeated HTTP 503, and does not record a cooldown for schema failures or other errors. Evidence checking is unchanged.

**Tech Stack:** Python 3.13, FastAPI, Pydantic v2, google-genai, pytest with a fake client and a fake clock.

## Global Constraints

- Chain order: `gemini-3.7-flash`, `gemini-3.8-flash`, `gemini-3.5-flash`, `gemini-3.6-flash`, `gemini-3-flash`, `gemini-3.1-pro`.
- Analysis and conversational calls use this same chain. The configured primary id stays first and is not called twice.
- HTTP 429: no retry on that model, cooldown 60 seconds.
- HTTP 503: one retry on that model, then cooldown 20 seconds.
- Other transport errors move to the next model for that request only and write no cooldown.
- Schema-validation retries stay on the model that answered, at most two attempts, and write no cooldown.
- If every model is cooling down, call the one that frees soonest, once. If that call fails, raise `ModelUnavailableError` with message `The analysis service is temporarily unavailable`.
- An empty `GEMINI_FALLBACK_MODELS` keeps the existing single-model path, including `TRANSIENT_ATTEMPTS` retries of HTTP 503.
- Logs may include the model id and exception class. They must not include document text or the API key.
- No database table, no pre-request health probe, no viewer or prompt changes.

---

### Task 1: ModelCooldown

**Files:**
- Create: `backend/app/services/model_cooldown.py`
- Test: `backend/tests/test_model_cooldown.py`

**Interfaces:**
- Consumes: nothing
- Produces: `ModelCooldown.allow(model: str) -> bool`, `ModelCooldown.mark(model: str, seconds: float) -> None`, `ModelCooldown.soonest(models: list[str]) -> str`. Time comes from a callable `clock() -> float` passed to `ModelCooldown`.

- [ ] **Step 1: Write the failing test**

```python
from app.services.model_cooldown import ModelCooldown


def test_mark_hides_a_model_until_the_clock_passes():
    now = {"t": 100.0}
    cooldown = ModelCooldown(clock=lambda: now["t"])
    assert cooldown.allow("gemini-3.7-flash") is True
    cooldown.mark("gemini-3.7-flash", 60)
    assert cooldown.allow("gemini-3.7-flash") is False
    now["t"] = 160.0
    assert cooldown.allow("gemini-3.7-flash") is True


def test_soonest_is_the_model_whose_cooldown_ends_first():
    now = {"t": 0.0}
    cooldown = ModelCooldown(clock=lambda: now["t"])
    cooldown.mark("gemini-3.7-flash", 60)
    cooldown.mark("gemini-3.8-flash", 20)
    assert cooldown.soonest(["gemini-3.7-flash", "gemini-3.8-flash"]) == "gemini-3.8-flash"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/test_model_cooldown.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.model_cooldown'`

- [ ] **Step 3: Write minimal implementation**

```python
"""In-process memory of Gemini models that should not be called yet."""


class ModelCooldown:
    def __init__(self, clock) -> None:
        self._clock = clock
        self._until: dict[str, float] = {}

    def allow(self, model: str) -> bool:
        return self._until.get(model, 0.0) <= self._clock()

    def mark(self, model: str, seconds: float) -> None:
        self._until[model] = self._clock() + seconds

    def soonest(self, models: list[str]) -> str:
        return min(models, key=lambda model: self._until.get(model, 0.0))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/test_model_cooldown.py -v`

Expected: PASS, 2 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/model_cooldown.py backend/tests/test_model_cooldown.py
git commit -m "$(cat <<'EOF'
Add an in-process cooldown for Gemini model ids.

EOF
)"
```

---

### Task 2: Skip cooled models inside GeminiService

**Files:**
- Modify: `backend/app/services/gemini_service.py`
- Test: `backend/tests/test_gemini_service.py`

**Interfaces:**
- Consumes: `ModelCooldown.allow`, `ModelCooldown.mark`, `ModelCooldown.soonest`
- Produces: `GeminiService.generate` records `code` on `ModelUnavailableError`. HTTP 429 marks 60 seconds. Exhausted HTTP 503 marks 20 seconds. The next `generate` on the same instance skips a model while `allow` is false.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_gemini_service.py`:

```python
_OK = '{"document_type": "RENTAL", "title": "Lease"}'


def test_rate_limit_is_remembered_for_the_next_request(monkeypatch):
    now = {"t": 1_000.0}
    monkeypatch.setattr(gemini_service.time, "monotonic", lambda: now["t"])
    service, fake = _service(
        monkeypatch,
        [_TransientError(429), _OK, _OK],
        gemini_analysis_model="gemini-3.7-flash",
        gemini_fallback_models="gemini-3.8-flash",
    )
    service.generate("classify", DocumentTypeOutput)
    service.generate("classify", DocumentTypeOutput)
    assert [request[0] for request in fake.requests] == [
        "gemini-3.7-flash",
        "gemini-3.8-flash",
        "gemini-3.8-flash",
    ]


def test_cooled_model_is_eligible_again_after_sixty_seconds(monkeypatch):
    now = {"t": 1_000.0}
    monkeypatch.setattr(gemini_service.time, "monotonic", lambda: now["t"])
    service, fake = _service(
        monkeypatch,
        [_TransientError(429), _OK, _OK],
        gemini_analysis_model="gemini-3.7-flash",
        gemini_fallback_models="gemini-3.8-flash",
    )
    service.generate("classify", DocumentTypeOutput)
    now["t"] = 1_060.0
    service.generate("classify", DocumentTypeOutput)
    assert fake.requests[-1][0] == "gemini-3.7-flash"


def test_repeated_503_cools_the_model_for_twenty_seconds(monkeypatch):
    now = {"t": 500.0}
    monkeypatch.setattr(gemini_service.time, "monotonic", lambda: now["t"])
    service, fake = _service(
        monkeypatch,
        [_TransientError(503), _TransientError(503), _OK, _OK],
        gemini_analysis_model="gemini-3.7-flash",
        gemini_fallback_models="gemini-3-flash",
    )
    service.generate("classify", DocumentTypeOutput)
    service.generate("classify", DocumentTypeOutput)
    assert [request[0] for request in fake.requests] == [
        "gemini-3.7-flash",
        "gemini-3.7-flash",
        "gemini-3-flash",
        "gemini-3-flash",
    ]


def test_schema_failure_does_not_cool_the_model(monkeypatch):
    now = {"t": 10.0}
    monkeypatch.setattr(gemini_service.time, "monotonic", lambda: now["t"])
    service, fake = _service(
        monkeypatch,
        ["not json", _OK],
        gemini_analysis_model="gemini-3.7-flash",
        gemini_fallback_models="gemini-3-flash",
    )
    service.generate("classify", DocumentTypeOutput)
    assert [request[0] for request in fake.requests] == ["gemini-3.7-flash", "gemini-3.7-flash"]


def test_other_errors_do_not_cool_the_model(monkeypatch):
    now = {"t": 10.0}
    monkeypatch.setattr(gemini_service.time, "monotonic", lambda: now["t"])
    service, fake = _service(
        monkeypatch,
        [RuntimeError("not found"), _OK, _OK],
        gemini_analysis_model="gemini-3-flash",
        gemini_fallback_models="gemini-3.1-pro",
    )
    service.generate("classify", DocumentTypeOutput)
    service.generate("classify", DocumentTypeOutput)
    assert [request[0] for request in fake.requests] == [
        "gemini-3-flash",
        "gemini-3.1-pro",
        "gemini-3-flash",
    ]


def test_when_all_models_are_cooling_the_soonest_is_tried_once(monkeypatch):
    now = {"t": 0.0}
    monkeypatch.setattr(gemini_service.time, "monotonic", lambda: now["t"])
    service, fake = _service(
        monkeypatch,
        [_TransientError(429), _TransientError(429), _TransientError(429)],
        gemini_analysis_model="gemini-3.7-flash",
        gemini_fallback_models="gemini-3.8-flash",
    )
    service._cooldown.mark("gemini-3.7-flash", 50)
    service._cooldown.mark("gemini-3.8-flash", 10)
    with pytest.raises(ModelUnavailableError):
        service.generate("classify", DocumentTypeOutput)
    assert [request[0] for request in fake.requests] == ["gemini-3.8-flash"]
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/test_gemini_service.py::test_rate_limit_is_remembered_for_the_next_request tests/test_gemini_service.py::test_cooled_model_is_eligible_again_after_sixty_seconds tests/test_gemini_service.py::test_repeated_503_cools_the_model_for_twenty_seconds tests/test_gemini_service.py::test_schema_failure_does_not_cool_the_model tests/test_gemini_service.py::test_other_errors_do_not_cool_the_model tests/test_gemini_service.py::test_when_all_models_are_cooling_the_soonest_is_tried_once -v`

Expected: FAIL because `GeminiService` has no `_cooldown` and a second call still starts on `gemini-3.7-flash`.

- [ ] **Step 3: Write minimal implementation**

In `backend/app/services/gemini_service.py`:

- Import `ModelCooldown`.
- Add constants `RATE_LIMIT_COOLDOWN_SECONDS = 60.0` and `OUTAGE_COOLDOWN_SECONDS = 20.0`.
- Change `ModelUnavailableError` so it accepts `code: int | None = None` and stores `self.code`.
- In `GeminiService.__init__`, set `self._cooldown = ModelCooldown(time.monotonic)`.
- In `_generate_content`, raise `ModelUnavailableError(..., code=getattr(exc, "code", None))`.
- Replace the candidate loop in `generate` with:

```python
chain = self._model_chain(conversational)
ready = [model for model in chain if self._cooldown.allow(model)]
rescue = not ready
candidates = ready or [self._cooldown.soonest(chain)]
attempts = 1 if rescue else (_CHAIN_TRANSIENT_ATTEMPTS if len(chain) > 1 else TRANSIENT_ATTEMPTS)
last_unavailable: ModelUnavailableError | None = None
for model in candidates:
    try:
        return self._generate_validated(model, prompt, schema, config, attempts)
    except ModelUnavailableError as exc:
        last_unavailable = exc
        if exc.code == 429:
            self._cooldown.mark(model, RATE_LIMIT_COOLDOWN_SECONDS)
        elif exc.code == 503:
            self._cooldown.mark(model, OUTAGE_COOLDOWN_SECONDS)
        logger.warning("Gemini model unavailable (%s); trying the next model", model)
        if rescue:
            break
raise last_unavailable or ModelUnavailableError("The analysis service is temporarily unavailable")
```

- [ ] **Step 4: Run the Gemini tests**

Run: `cd backend && .venv/bin/pytest tests/test_gemini_service.py tests/test_model_cooldown.py -v`

Expected: PASS. Existing single-model 503 tests still expect `TRANSIENT_ATTEMPTS` requests because their fallback list is empty. Existing fallback tests still see two 503 calls on the first model before moving on.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/gemini_service.py backend/tests/test_gemini_service.py
git commit -m "$(cat <<'EOF'
Skip a Gemini model that just hit a rate limit or repeated outage.

EOF
)"
```

---

### Task 3: Default the chain to the six configured models

**Files:**
- Modify: `backend/app/config.py` (`gemini_analysis_model`, `gemini_chat_model`, `gemini_fallback_models`)
- Modify: `backend/.env.example` (the three `GEMINI_*` model lines)
- Modify: `backend/.env` (those same three lines only; this file stays gitignored)
- Modify: `CLAUDE.md` section 8, the paragraph that names the primary model and `GEMINI_FALLBACK_MODELS`
- Test: `backend/tests/test_gemini_service.py`

**Interfaces:**
- Consumes: `GeminiService._model_chain`
- Produces: default primary `gemini-3.7-flash` and fallbacks `gemini-3.8-flash,gemini-3.5-flash,gemini-3.6-flash,gemini-3-flash,gemini-3.1-pro`

- [ ] **Step 1: Write the failing test**

`_service` overrides the defaults, so this test constructs `Settings` with `_env_file=None` and appends it to `backend/tests/test_gemini_service.py`:

```python
def test_default_settings_chain_matches_the_availability_order():
    settings = Settings(_env_file=None, gemini_api_key="test-key")
    assert settings.gemini_analysis_model == "gemini-3.7-flash"
    assert settings.gemini_chat_model == "gemini-3.7-flash"
    assert settings.gemini_fallback_model_list() == [
        "gemini-3.8-flash",
        "gemini-3.5-flash",
        "gemini-3.6-flash",
        "gemini-3-flash",
        "gemini-3.1-pro",
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/test_gemini_service.py::test_default_settings_chain_matches_the_availability_order -v`

Expected: FAIL because the default primary is `gemini-3.8-flash` and the fallback string is `gemini-3.6-flash,gemini-3.5-flash`.

- [ ] **Step 3: Update defaults and docs**

In `backend/app/config.py` set:

```python
gemini_analysis_model: str = "gemini-3.7-flash"
gemini_chat_model: str = "gemini-3.7-flash"
gemini_fallback_models: str = "gemini-3.8-flash,gemini-3.5-flash,gemini-3.6-flash,gemini-3-flash,gemini-3.1-pro"
```

Set the same three values in `backend/.env.example` and in the local `backend/.env`.

In `CLAUDE.md` section 8, replace the sentence that names only `gemini-3.6-flash` and `gemini-3.5-flash` with: the primary is `gemini-3.7-flash`; if it was rate-limited or unavailable in this process, the request starts on the next eligible model in `gemini-3.8-flash`, `gemini-3.5-flash`, `gemini-3.6-flash`, `gemini-3-flash`, `gemini-3.1-pro`. A 429 skips that model for 60 seconds. A repeated 503 skips it for 20 seconds.

- [ ] **Step 4: Run the cooldown and Gemini tests**

Run: `cd backend && .venv/bin/pytest tests/test_model_cooldown.py tests/test_gemini_service.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/.env.example backend/tests/test_gemini_service.py CLAUDE.md
git commit -m "$(cat <<'EOF'
Default Gemini routing to the six-model availability chain.

EOF
)"
```

Do not `git add backend/.env`.
