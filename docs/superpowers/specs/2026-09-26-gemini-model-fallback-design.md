# Gemini availability routing

LexLens analysis and document questions stay available when individual Gemini models are rate-limited or briefly overloaded. Model choice does not change what an answer is allowed to say. Every document-grounded claim still has to match a quote in the parsed document.

## Problem

A person waiting on Notice & Exit, a document question, lawyer prep, or a comparison needs an answer from the document they uploaded. Gemini 3.7 Flash and Gemini 3.8 Flash can already be at their per-minute cap while another Flash or Pro model on the same key still has room. Starting every request on an exhausted model makes the product look broken even though another model could have answered.

## Decision

Remember a failure only inside the running server process. The next request skips a model that recently failed and starts on the next model in a fixed chain. No database row stores this, and no extra health-check call is made before analysis.

The chain, in order, is:

1. `gemini-3.7-flash`
2. `gemini-3.8-flash`
3. `gemini-3.5-flash`
4. `gemini-3.6-flash`
5. `gemini-3-flash`
6. `gemini-3.1-pro`

Analysis and conversational calls use this same chain. `GEMINI_ANALYSIS_MODEL` and `GEMINI_CHAT_MODEL` remain the first id when set, and any id already in the chain is not called twice.

## Behaviour

`GeminiService` owns a map of model id to the time that model may be tried again. The map lives on the service instance that the API process creates at startup, so one upload, one analysis, and the next question in that process share it. A second worker process has its own map. Restarting the process clears it.

For one request:

- Skip any model whose cooldown has not elapsed.
- On HTTP 429, do not retry that model. Mark it unavailable for 60 seconds and continue.
- On HTTP 503, retry that model once. If it fails again, mark it unavailable for 20 seconds and continue.
- On any other transport or model error, continue to the next model for this request only. Do not record a cooldown.
- If the model returns JSON that fails schema validation, retry that validation on the same model, up to the existing two attempts. Do not treat that as unavailability and do not change models for those retries.
- If every model is inside its cooldown, call the one whose cooldown ends soonest, once. If that call fails, raise the existing unavailable error. The user still sees “Analysis is taking longer than expected. Try again.”
- A model id the API does not recognise is treated like any other non-429 transport error for that request: move on, and do not bench the rest of the chain.

Evidence location, the one repair retry for unlocated quotes, prompt-injection boundaries, and operation schemas stay as they are. Logs record the model id and the error class. They do not record document text or the API key.

## Configuration

`GEMINI_FALLBACK_MODELS` defaults to the chain above, excluding whichever id is already the primary. An operator can reorder or shorten the list. An empty fallback list keeps today’s single-model behaviour, including the longer 503 retry, so existing tests of that path remain valid.

## Tests

Unit tests use the fake Gemini client and a fake clock.

- A 429 on the first model is not retried, and the following `generate` call does not use that model until 60 seconds have passed.
- After the fake clock passes 60 seconds, the cooled model is eligible again.
- A 503 is tried twice on that model, then the model is skipped for 20 seconds.
- Invalid JSON does not write a cooldown.
- When every model is cooling down, the single rescue call uses the model that frees soonest.
- The chain does not call a duplicate of the primary.

## Out of scope

No live probe of Google’s rate-limit dashboard, no per-day quota tracker, and no change to the viewer, prompts, or evidence rules.
