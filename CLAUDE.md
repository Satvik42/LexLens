# LexLens — Engineering Overview (living document)

> This file describes the **actual implementation state** of the LexLens prototype.
> It does not replace the authoritative requirements:
>
> 1. `IMPLEMENTATION_PLAN.md` — product, architecture, security, AI behaviour, testing, evaluation alignment
> 2. `design_plan.md` — visual system, layouts, interactions, responsive/accessibility rules
> 3. `UI_screens/screens.jpeg` — approved visual reference
>
> Update this file whenever a significant architectural, security, AI, database, API, or frontend decision is made.
> Never record a feature as complete unless it is implemented and verified.

---

## 1. Product overview

**LexLens** — _Legal Companion, not Legal Chatbot._

- Core message: **Understand what you're signing.**
- Supporting principle: **Don't just get an answer. See where it came from.**
- Second principle: **If the document does not contain enough information to answer, say so explicitly.**

LexLens helps a person understand, navigate, compare, and question a legal document they have received. Every document-grounded claim is tied to page/section evidence that can be opened in a document viewer with the supporting text highlighted in yellow.

### Problem being solved

Having access to a legal document is not the same as understanding what matters inside it. People sign employment, rental, freelance, NDA, vendor and SaaS agreements without knowing which clauses matter, where they are, or what the document leaves unsaid.

### Target users

Non-lawyers who have received a document and need to understand it before deciding or before talking to a professional: employees, tenants, freelancers, founders, vendors, interns, small teams.

### Positioning boundaries

LexLens **is** an evidence-backed legal document companion. It is **not** an AI lawyer, a legal-advice engine, an outcome predictor, a legal search engine, or a generic PDF summariser/chatbot.

Persistent disclaimer: _"LexLens provides document-grounded information and assistance. It is not a substitute for professional legal advice."_

---

## 2. Core product loop

```
LANDING → UPLOAD → DOCUMENT READY → "What do you want to understand?"
→ SELECT OPERATION → FOCUSED ANALYSIS → STRUCTURED RESULT → EVIDENCE CHIP
→ DOCUMENT VIEWER → YELLOW HIGHLIGHT → SUGGESTED QUESTIONS → NEXT ACTION
```

Chat ("Ask About the Document") is one operation among nine; it is never the entry point.

---

## 3. Supported document types

Document-agnostic. Detected type (heuristic + Gemini classification) drives operation labels/descriptions and retrieval hints, **not** separate workflows:

`EMPLOYMENT`, `RENTAL`, `NDA`, `FREELANCE`, `VENDOR`, `INTERNSHIP`, `SAAS_TERMS`, `FOUNDER`, `PARTNERSHIP`, `SERVICE`, `POLICY`, `GENERAL`

Adaptation lives in one registry (`backend/app/domain/operations.py`, mirrored for labels in `frontend/src/utils/operations.js`).

## 4. Supported operations (each has a distinct UI)

| Operation key  | UI pattern                                                                               |
| -------------- | ---------------------------------------------------------------------------------------- |
| `KEY_TERMS`    | key/value data cards grid                                                                |
| `COMPENSATION` | financial/payment cards grouped by category                                              |
| `NOTICE_EXIT`  | structured clause analysis with topic nav                                                |
| `RESTRICTIONS` | attention/restriction cards                                                              |
| `CONCERNS`     | review list (concern / inconsistency / important / ambiguous) with inconsistency tables  |
| `OBLIGATIONS`  | checklist with source per item                                                           |
| `DOCUMENT_QA`  | grounded conversation with answer / evidence / suggested questions, not-determined state |
| `LAWYER_PREP`  | numbered question list with add / copy / export                                          |
| `COMPARE`      | evidence-backed comparison table                                                         |

---

## 5. Evidence-first architecture

```
Document → Storage (GCS) → Document AI (or local fallback parser)
→ normalized pages/blocks (+ bounding boxes when available)
→ section/clause segmentation → operation/intent
→ lexical clause retrieval (targeted context, not whole document)
→ Gemini structured output (Pydantic response schema)
→ server-side evidence validation against parsed pages
→ persisted analysis_results + evidence rows
→ operation-specific frontend rendering
```

### AI response states

`EXPLICITLY_STATED` · `PARTIALLY_DETERMINED` · `NOT_FOUND` · `POTENTIAL_INCONSISTENCY`

No numeric confidence score is shown. Trust comes from verified evidence.

### Hallucination / uncertainty strategy

- Prompts require quotes to be verbatim and restrict answers to retrieved clauses.
- Every evidence quote is located in the parsed page text (exact → whitespace-normalised → fuzzy). Located quotes get offsets (and bbox when Document AI supplied it) and `verified: true`.
- Unlocated quotes are dropped. Claims that lose all evidence are downgraded (`EXPLICITLY_STATED → PARTIALLY_DETERMINED`, or `NOT_FOUND` if nothing remains) and flagged `verification_note`.
- One repair retry is made with the failed quotes listed before downgrading.
- `NOT_FOUND` results render the "Cannot be determined from this document" UI with _What I found_ and _You may want to ask a legal professional_ sections.
- Inconsistencies are only reported when both sides have verified evidence; wording never decides which clause governs.

### Prompt-injection defence

System instruction (`backend/app/prompts/system.py`) states that document content is untrusted data, instructions inside documents must never be followed, system prompts/secrets are never revealed. Document text is passed in a delimited data block separate from instructions. Model output is schema-validated and never rendered as HTML.

---

## 6. Frontend architecture

- React 18 + Vite + JavaScript (no TypeScript), React Router, Zustand (small store), plain CSS with design tokens (`src/styles/tokens.css`).
- Structure: `src/components` (ui primitives, domain components, `results/` operation UIs, `viewer/`), `src/pages`, `src/services` (api/auth/documents/analysis), `src/state`, `src/utils`, `src/hooks`.
- Document viewer renders **normalized page text blocks** as document-styled pages with `<mark>` yellow highlights located by evidence offsets/text; bounding boxes are preserved in the data model for a future canvas overlay. This works identically for PDF, DOCX and TXT and keeps highlighted text in the accessibility tree.
- Explicit UI state derived from `document.processing_status`, analysis query state, and viewer `evidenceId`/`page` search params.

## 7. Backend architecture

- Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2 (SQLite by default, `DATABASE_URL` for Postgres).
- Layers: `api/` (routers, thin), `services/` (business logic + external providers), `schemas/` (request/response + AI output schemas), `security/` (auth, file validation, rate limiting), `prompts/`, `domain/` (operation registry), `db/` (engine, models).
- Expensive processing runs as a background task after upload; frontend polls `/status`.
- Caching: content hash (`sha256`) dedupes re-uploads per user; analysis results are cached per `(document, operation)`; QA answers are persisted as messages.

## 8. Google Cloud services (real roles)

| Service                   | Role                                                                                                         | Module                            |
| ------------------------- | ------------------------------------------------------------------------------------------------------------ | --------------------------------- |
| Cloud Storage             | Untrusted upload storage with randomised object keys; source for Document AI                                 | `services/storage_service.py`     |
| Document AI               | Page/layout extraction (text, blocks, bounding boxes)                                                        | `services/document_ai_service.py` |
| Gemini (google-genai SDK) | Document-type classification, structured analysis, grounded QA, suggested/professional questions, comparison | `services/gemini_service.py`      |

Model IDs are configuration (`GEMINI_ANALYSIS_MODEL`, `GEMINI_CHAT_MODEL`). The running primary is `gemini-3-flash`. If that model is unavailable, `GEMINI_FALLBACK_MODELS` is tried in order, starting with `gemini-3.1-pro`. Live/audio models (`gemini-3.8-live`, `gemini-3.8-live-extended-thinking`) are **not** used: the plan's §43 excludes a voice-first assistant from MVP and a Live model only supports `bidiGenerateContent`, not schema-constrained `generateContent`.

`GeminiService` retries `503` on the current model (`TRANSIENT_ATTEMPTS` when it is the only model, two attempts when fallbacks are configured) and then moves to the next model. `429` is not retried on the same model; the request moves to the next fallback. Schema-validation retries (`_MAX_ATTEMPTS`) stay on the model that answered.

Local fallback: when Document AI is not configured, `services/local_parser_service.py` (pypdf / python-docx / txt) produces the same normalized structure (without bounding boxes). When GCS is not configured, files are stored under `LOCAL_STORAGE_DIR`. Gemini is required for analysis; tests inject a fake client.

## 9. Authentication & authorisation

- Supabase Auth (Google OAuth + email magic link) on the frontend via `@supabase/supabase-js`.
- Backend verifies the Supabase JWT (`SUPABASE_JWT_SECRET` HS256, or `SUPABASE_JWKS_URL` for asymmetric keys). User identity comes only from the verified token.
- Development-only sign-in (`AUTH_DEV_LOGIN_ENABLED=true`, refused when `APP_ENV=production`) mints a local JWT through `POST /api/auth/dev-session` so the same verification path is exercised without Supabase.
- Every document route resolves `document` by `(id, owner_user_id)`; missing or foreign documents return 404.

## 10. Storage & document lifecycle

Upload → validate → random key → GCS/local → background processing → pages persisted → analysis. `DELETE /api/documents/:id` removes DB rows and the stored object. `expires_at` is recorded; automated deletion is **not** claimed in the UI unless a lifecycle policy is configured.

## 11. Security requirements (implementation checklist)

- [x] No secrets in frontend; all Google calls server-side
- [x] Extension + MIME + magic-byte validation; size limit; NUL-byte rejection for text
- [x] Filename sanitisation; randomised storage keys
- [x] JWT verification; per-user document ownership on every route
- [x] Rate limiting on upload/analyse/question endpoints
- [x] CORS restricted to configured origins
- [x] Generic error responses; no stack traces; no document text in logs
- [x] Prompt-injection defence; model output schema validation
- [x] Uploaded files never executed

## 12. Accessibility requirements

Semantic HTML, keyboard-operable intent cards and evidence chips, visible focus ring token, labelled upload input, dialog focus management, live regions for processing/errors, status badges with icon + text (never colour only), highlight paired with textual "Source: Page X · §Y", responsive layouts (stacked intents, single-column analysis, full-width viewer on mobile).

## 13. API structure

```
POST   /api/auth/dev-session                    (dev only)
POST   /api/documents                           upload (multipart)
GET    /api/documents                           list own documents
GET    /api/documents/:id
DELETE /api/documents/:id
POST   /api/documents/:id/process               re-run processing
GET    /api/documents/:id/status
GET    /api/documents/:id/pages                 normalized pages for viewer
POST   /api/documents/:id/analyze               { operation, force? }
POST   /api/documents/:id/questions             { question, conversation_id? }
GET    /api/documents/:id/conversations/:cid    messages
GET    /api/documents/:id/evidence/:evidence_id
POST   /api/documents/:id/lawyer-questions      { include_operations?, custom_questions? }
POST   /api/comparisons                         { original_document_id, updated_document_id }
GET    /api/comparisons/:id
```

## 14. Data model

`users` · `documents` (owner, filename, mime, type, page_count, size, storage_key, content_hash, processing_status, error_code, expires_at) · `document_pages` (page_number, text, layout_json) · `analysis_results` (document, operation, status, result_json, unique per document+operation) · `evidence` (analysis_result, page_number, section, text, start/end offsets, location_json, verified) · `conversations` · `messages` (role, content, result_json) · `comparisons`.

## 15. Repository structure

```
LexalLens/
├── CLAUDE.md                     ← this file
├── IMPLEMENTATION_PLAN.md        ← authoritative requirements
├── design_plan.md                ← authoritative design
├── UI_screens/screens.jpeg       ← approved visual reference
├── backend/                      FastAPI application + tests
├── frontend/                     Vite/React application + tests
└── demo_documents/               synthetic demo agreements
```

## 16. Development commands

```bash
# backend
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env            # fill in values
uvicorn app.main:app --reload --port 8000
pytest

# frontend
cd frontend && npm install
cp .env.example .env
npm run dev                      # http://localhost:5173
npm test
```

## 17. Environment variables

Backend (`backend/.env`): `APP_ENV`, `DATABASE_URL`, `CORS_ORIGINS`, `MAX_UPLOAD_MB`,
`SUPABASE_JWT_SECRET` / `SUPABASE_JWKS_URL` / `SUPABASE_URL`, `AUTH_DEV_LOGIN_ENABLED`, `AUTH_DEV_JWT_SECRET`,
`GCP_PROJECT_ID`, `GCS_BUCKET`, `LOCAL_STORAGE_DIR`, `DOCUMENT_AI_LOCATION`, `DOCUMENT_AI_PROCESSOR_ID`,
`GEMINI_API_KEY`, `GEMINI_ANALYSIS_MODEL`, `GEMINI_CHAT_MODEL`, `RATE_LIMIT_PER_MINUTE`,
`FRONTEND_DIST_DIR`.

Frontend (`frontend/.env`): `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_AUTH_DEV_LOGIN`.

Only the Supabase **anon** key is ever exposed to the browser; it is designed to be public.

## 18. Testing strategy

- Backend `pytest`: auth (missing/invalid token, cross-user 404), file validation (type, size, filename, magic bytes), prompt-injection handling, evidence validation (exact/fuzzy/missing/wrong page), analysis pipeline with fake Gemini (explicit / not found / conflicting / malformed output), API contract.
- Frontend `vitest` + Testing Library: UploadZone, IntentCard keyboard activation, EvidenceChip navigation, PageView yellow highlight + textual source, NotDetermined rendering, ComparisonTable.

## 19. Demo workflow

Landing → _Analyze a Document_ → upload `demo_documents/employment_agreement.pdf` → Document Ready → _Notice & Exit Terms_ → "60 days" → click `Page N · §8.2` → viewer with yellow highlight → _Ask_: "What happens to my stock options if I resign?" → "Cannot be determined" → suggested questions → _Potential Concerns_ shows 30-day vs 60-day inconsistency → _Prepare for a Lawyer_.

## 20. Definition of done

See `IMPLEMENTATION_PLAN.md` §45 (20 items). Tracked in §21 below.

---

## 21. Current implementation status

_Last updated: after live GCP verification (2026-09-25)._

### Completed

- Requirements review (`IMPLEMENTATION_PLAN.md`, `design_plan.md`, `UI_screens/screens.jpeg`)
- Architecture decisions recorded in this file
- Backend FastAPI application: config, auth (Supabase JWT + dev session), document upload/process/status/pages/evidence, analysis, QA, lawyer questions, comparison
- Document pipeline: GCS/local storage, Document AI + local parser fallback, clause segmentation, lexical retrieval, Gemini structured output, evidence validation + one repair retry
- Backend tests cover security, parsing, evidence validation, analysis API, Gemini 503 retry, and fallback to `gemini-3.6-flash` then `gemini-3.5-flash`
- Demo documents: employment (30-day vs 60-day notice conflict, no equity clause), revised employment, rental
- Frontend design system, routing, landing, sign-in, upload, document ready, intent grid, operation-specific result UIs, ask, lawyer prep, compare, document viewer with yellow `<mark>` highlights
- Frontend tests: 13 passing (upload validation, intent keyboard, evidence chip navigation, yellow highlight + textual source, not-determined, comparison table)
- **Google Cloud Storage — live-verified**: API starts with `gcs=True`; upload stored under a randomized key using Application Default Credentials.
- **Document AI — live-verified**: `employment_agreement.pdf` processed by the `us` Document OCR processor, returning `parser=document_ai`, 4 pages with bounding boxes.
- **Gemini document classification — live-verified**: the uploaded agreement was classified `EMPLOYMENT` / "Employment Agreement" through the real structured-output path.

- **Cloud Run (single URL) — live-verified**: `https://lexlens-263641821288.us-central1.run.app` serves the Vite SPA and FastAPI together. `/api/health` returns `{"status":"ok"}`; landing and `/signin` render. CPU-always-allocated so upload background processing can finish.

### In progress

- Live Gemini **analysis** operations (NOTICE_EXIT, QA, etc.). Blocked by model availability, not configuration — see Known issues.
- Supabase Auth redirect URLs must include the Cloud Run origin before Google/magic-link sign-in works in production.

### Pending

- Visual polish against `UI_screens/screens.jpeg` at a true 1440px desktop frame (current browser preview is narrower than the reference sheet)
- End-to-end demo of Notice → 60 days → yellow highlight → stock-options NOT_FOUND, once a Gemini model with spare capacity is selected

### Known issues / limitations

- **Gemini 3.x Flash capacity is uneven.** The demo chain uses `gemini-3-flash` then `gemini-3.1-pro` so rate-limited 3.5/3.6/3.7/3.8 Flash ids are not tried first. A `429` skips that model for 60 seconds; a repeated `503` skips it for 20 seconds.
- Retrying `429` on the same model is deliberately not done: it means that model’s quota is already exhausted. The request moves to the next fallback instead. Only `503` is retried on the current model.
- Analysis, QA, lawyer prep and comparison call Gemini. Without `GEMINI_API_KEY` the UI shows a friendly “not configured” error. Tests inject a fake model.
- GCS and Document AI require Application Default Credentials (`gcloud auth application-default login`). If `GCS_BUCKET` is set without ADC, application startup fails rather than falling back to local storage.
- `CORS_ORIGINS` is stored as a string and parsed by `Settings.cors_origin_list()` so dotenv does not JSON-decode a list field.
- Automated deletion is recorded as `expires_at` only; the UI does not claim files are auto-deleted.
- The document viewer renders normalized page text, not a pixel-identical PDF canvas (ADR 1).

### Demo status

- Runnable locally: landing → sign-in (dev session) → upload → document ready → intent cards → viewer.
- Verified end to end against real Google services: upload → Cloud Storage → Document AI (4 pages) → Gemini classification → `READY`.
- Operation analysis (Notice & Exit, QA, lawyer prep, compare) is **not** yet live-verified: the configured model returns `503` under load. Nothing in the pipeline below the model call is implicated.

---

## 22. Important architectural decisions (ADR log)

1. **Text-rendered viewer instead of PDF canvas** — evidence highlighting must be deterministic and accessible for PDF/DOCX/TXT alike. Pages are rendered from normalized blocks with `<mark>`; bounding boxes are kept in `layout_json` for future canvas overlay. (Trade-off: visual fidelity to the original PDF layout is reduced.)
2. **Lexical clause retrieval, no vector DB** — operation keyword sets + query terms score segmented clauses; top clauses are sent to Gemini. Avoids an embedding dependency and whole-document prompts; adequate for 5–50 page contracts.
3. **Single JWT verification path** — Supabase tokens in production, locally-minted tokens in development, both verified identically; no "trust the client" mode exists.
4. **Local parser/storage fallbacks** — the same normalized document structure is produced with or without GCP, so the pipeline, tests and demo work offline while Document AI/GCS are used when configured.
5. **Model IDs are configuration** — analysis and conversational models are separate settings, with `GEMINI_FALLBACK_MODELS` tried in order when the primary is unavailable.
6. **Operation registry as single source of truth** — labels, descriptions per document type, retrieval keywords, topics and result schema selection live in one backend module, mirrored minimally in the frontend for labels/icons.
7. **Single Cloud Run URL** — one container serves the Vite build and FastAPI (`FRONTEND_DIST_DIR`). Same-origin `/api` avoids CORS in production. Cloud Run must use CPU-always-allocated so upload `BackgroundTasks` can finish Document AI after the HTTP response. Demo persistence is SQLite on `/tmp` plus GCS for files.
