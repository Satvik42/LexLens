# LexLens — Legal Companion

GenAI-powered, evidence-backed assistant for understanding a legal document you have received.

**Challenge theme:** Legal information access and basic legal assistance

LexLens helps a non-lawyer understand, navigate, compare, and question a document they already have — an employment agreement, lease, NDA, freelance contract, vendor terms, or a general policy. It is a **legal companion, not a legal chatbot and not a lawyer**. Every document-grounded claim is tied to a page and section that can be opened in a viewer with the supporting text highlighted. If the document does not contain enough information to answer, LexLens says so explicitly.

> LexLens provides document-grounded information and assistance. It is not a substitute for professional legal advice.

## Chosen direction

**Understand what you're signing.**

The product starts from a document the user uploaded, not from a general legal search box. Chat is one operation among nine. It is never the entry point. The persona is a careful document companion: it shows what the text says, where it says it, and what the text leaves unsaid, and it prepares questions for a professional instead of predicting an outcome.

## Problem statement alignment

| Potential use case | How LexLens addresses it |
| --- | --- |
| Simplifying complex legal documents | Focused operations (key terms, compensation, notice, restrictions, obligations) return structured cards, not a generic summary |
| Comparing contracts, agreements, or policies | Evidence-backed comparison of two uploaded versions |
| Highlighting important clauses, obligations, risks, or inconsistencies | Concerns and obligations views; inconsistencies are shown only when both sides have verified quotes |
| Answering questions based on provided legal documents | Grounded Q&A restricted to retrieved clauses |
| Helping users understand options and next steps | Suggested questions and an explicit “cannot be determined” state |
| Generating summaries, checklists, or other actionable outputs | Obligation checklist and lawyer-prep question list |
| Preparing information or questions for a legal professional | Lawyer-prep operation with copy and export |

The product does not give legal advice, predict case outcomes, or decide which of two conflicting clauses governs.

## Approach and logic

**Core design principle: evidence before answer.**

A claim is shown only after the model’s quote is located in the parsed page text. Trust comes from that check, not from a numeric confidence score.

```text
Upload
  → validate file (extension, MIME, magic bytes, size)
  → store in Cloud Storage (or local fallback) under a randomised key
  → Document AI OCR (or local parser) → normalised pages and blocks
  → clause segmentation
  → user selects an operation
  → lexical retrieval of the relevant clauses (not the whole document)
  → Gemini structured output (Pydantic schema)
  → server-side evidence validation (exact → whitespace-normalised → fuzzy)
  → one repair retry if quotes cannot be located
  → persisted result + evidence rows
  → operation-specific UI
  → evidence chip → document viewer → yellow highlight
```

### Decision states

The model must return one of:

- `EXPLICITLY_STATED`
- `PARTIALLY_DETERMINED`
- `NOT_FOUND`
- `POTENTIAL_INCONSISTENCY`

`NOT_FOUND` renders “Cannot be determined from this document,” with what was found and what to ask a professional. An inconsistency is reported only when both sides have verified evidence. The wording never picks a winner.

### Model routing

Analysis and chat call `generateContent` with a JSON schema. The primary model is configuration (`GEMINI_ANALYSIS_MODEL` / `GEMINI_CHAT_MODEL`). The demo primary is `gemini-3-flash-preview`. If that model returns `503` or `429`, `GEMINI_FALLBACK_MODELS` is tried in order (`gemini-3.5-flash`, `gemini-2.5-flash`, `gemini-flash-latest`, then `gemini-3.1-pro-preview`). A `429` is not retried on the same model. Live models are not used: they only support bidirectional streaming, which cannot return schema-constrained JSON.

## How the solution works

```text
Browser (React)
  → Vite dev proxy /api
  → FastAPI
       ├── Supabase JWT verification (or a development-only local JWT)
       ├── Cloud Storage + Document AI
       └── Gemini structured generation
  → SQLite (or Postgres via DATABASE_URL)
```

### Product loop

```text
Landing → Upload → Document ready → “What do you want to know?”
  → select an operation → focused analysis → evidence chip
  → document viewer (yellow highlight) → suggested questions → next action
```

### Operations

| Key | What the user sees |
| --- | --- |
| `KEY_TERMS` | Key/value cards |
| `COMPENSATION` | Payment cards grouped by category |
| `NOTICE_EXIT` | Clause analysis with topic navigation |
| `RESTRICTIONS` | Restriction cards |
| `CONCERNS` | Concerns, ambiguities, and inconsistency tables |
| `OBLIGATIONS` | Checklist with a source per item |
| `DOCUMENT_QA` | Grounded answer, evidence, and suggested questions |
| `LAWYER_PREP` | Numbered questions to take to a professional |
| `COMPARE` | Evidence-backed comparison table |

Document type (`EMPLOYMENT`, `RENTAL`, `NDA`, `FREELANCE`, `VENDOR`, `INTERNSHIP`, `SAAS_TERMS`, `FOUNDER`, `PARTNERSHIP`, `SERVICE`, `POLICY`, `GENERAL`) changes labels and retrieval hints. It does not create a separate workflow.

### Request flow (analysis)

1. The user selects an operation such as Notice & Exit Terms.
2. The API loads segmented clauses and scores them with that operation’s keywords.
3. The top clauses are sent to Gemini inside a delimited untrusted-data block, separate from the system instruction.
4. Gemini returns schema-validated JSON, including verbatim quotes.
5. The server locates each quote in the parsed page. Unlocated quotes are dropped.
6. The UI renders the structured result. An evidence chip opens the viewer on that page with the quote marked in yellow.

### Request flow (question)

1. The user asks, for example, “What happens to my stock options if I resign?”
2. Retrieval uses the question terms plus the document’s clauses.
3. If no verified evidence supports an answer, the response is `NOT_FOUND` rather than an invented clause.

## Project structure

```text
LexLens/
├── frontend/                 # React 18 + Vite
│   └── src/
│       ├── components/       # UI primitives, results, viewer, upload, intents
│       ├── pages/            # Landing, upload, document ready, analysis, ask, compare
│       ├── services/         # API and Supabase auth
│       └── styles/           # Design tokens and layout
├── backend/                  # FastAPI
│   └── app/
│       ├── api/              # Thin routers
│       ├── services/         # Gemini, Document AI, storage, evidence, analysis
│       ├── domain/           # Operation registry
│       ├── prompts/          # System instruction and untrusted-data boundary
│       ├── security/         # JWT, file validation, rate limits
│       └── db/               # SQLAlchemy models
├── demo_documents/           # Synthetic agreements for the demo
├── UI_screens/               # Approved visual reference
├── IMPLEMENTATION_PLAN.md    # Product and engineering requirements
├── design_plan.md            # Visual system
├── CLAUDE.md                 # Living implementation-state notes
└── README.md
```

## Frontend stack

- React 18, Vite, JavaScript
- React Router, Zustand
- Plain CSS with design tokens
- Supabase Auth in the browser (anon key only)
- Document viewer renders normalised page text with a yellow `<mark>`, so the highlight stays in the accessibility tree for PDF, DOCX, and TXT

## Backend stack

- Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2
- SQLite by default; `DATABASE_URL` for Postgres
- `google-genai` for schema-constrained Gemini output
- Google Cloud Storage and Document AI through Application Default Credentials

## Google services

| Service | Role |
| --- | --- |
| Cloud Storage | Untrusted upload storage with randomised object keys. Also the source Document AI reads. |
| Document AI | Page and layout extraction, including bounding boxes when the OCR processor supplies them. |
| Gemini | Document-type classification, structured analysis, grounded Q&A, lawyer questions, and comparison. |

When Cloud Storage or Document AI is not configured, the same normalised document shape is produced by a local parser (`pypdf`, `python-docx`, or plain text) and files are stored under `LOCAL_STORAGE_DIR`. Analysis still requires Gemini. Tests inject a fake model client.

## Security

- No Google or Supabase service secrets in the frontend. Gemini, Storage, and Document AI are called only on the server.
- Uploads are checked by extension, MIME type, and magic bytes, with a size limit. Text uploads reject NUL bytes. Filenames are sanitised. Storage keys are random.
- The API verifies a Supabase JWT (`SUPABASE_JWT_SECRET` or `SUPABASE_JWKS_URL`). Identity comes only from the verified token. Arbitrary-email `/dev-session` is refused when `APP_ENV=production`. An optional fixed-email demo session (`AUTH_DEMO_LOGIN_ENABLED`, default off) uses the same JWT verification path and never accepts a client-supplied user id.
- Every document route resolves the row by `(id, owner_user_id)`. A missing or foreign document returns 404.
- Upload, analysis, and question endpoints are rate limited. CORS is limited to configured origins.
- Errors returned to the client are generic. Stack traces and document text are not logged.
- Document text is untrusted data. The system instruction forbids following instructions found inside a document and forbids revealing prompts or secrets. Model output is schema-validated and is not rendered as HTML.
- Uploaded files are never executed.
- `.env`, virtual environments, `node_modules`, local databases, and service-account JSON files are gitignored.

## Accessibility

- Semantic HTML, keyboard-operable intent cards and evidence chips, and a visible focus ring
- Labelled upload input and dialog focus management
- Live regions for processing and errors
- Status is icon plus text, never colour alone
- Each highlight is paired with “Source: Page X · §Y”
- Layouts stack on small screens: intents, analysis, and a full-width viewer

## Testing

```bash
cd backend && .venv/bin/pytest
cd frontend && npm test
```

Backend tests cover authentication (missing token, invalid token, cross-user 404), file validation, prompt-injection handling, evidence location (exact, fuzzy, missing, wrong page), the analysis pipeline with a fake Gemini client, transient `503` retry, and fallback to the next model.

Frontend tests cover upload validation, keyboard activation of intent cards, evidence-chip navigation, the yellow highlight plus its textual source, the not-determined state, and the comparison table.

## Assumptions

- The user has already received a document and wants to understand it before deciding or before talking to a professional.
- Contracts in the demo set are short (about 5–50 pages). Retrieval is lexical, not a vector database.
- The viewer prioritises a deterministic, accessible highlight over a pixel-identical PDF canvas. Bounding boxes are stored for a later overlay.
- Gemini Flash capacity can return `503` or `429`. The request moves to the configured fallback models instead of failing on the first busy model.
- `expires_at` is recorded on a document. The UI does not claim that files are deleted automatically unless a storage lifecycle policy is configured.
- Supabase is the identity provider. Firebase is not used.

## Local development

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`. Leave `VITE_API_BASE_URL` empty in local development so the Vite proxy forwards `/api` to `http://localhost:8000`.

## Deployment (single Cloud Run URL)

The production image serves the Vite build and the FastAPI API from one origin. `VITE_API_BASE_URL` stays empty. Cloud Run keeps CPU allocated after the upload response so Document AI can finish in a FastAPI background task.

```bash
chmod +x scripts/deploy-cloud-run.sh
./scripts/deploy-cloud-run.sh
```

The script reads `frontend/.env` (Supabase anon values) and `backend/.env` (Gemini, GCS, Document AI, JWKS), builds in Cloud Build, and deploys `lexlens` to Cloud Run in `us-central1`. It does not print secret values.

After the first deploy:

1. Copy the printed URL (currently `https://lexlens-263641821288.us-central1.run.app`).
2. In Supabase → Authentication → URL configuration, set Site URL to that origin and add `https://lexlens-263641821288.us-central1.run.app/**` and `https://lexlens-hszr2ri6ua-uc.a.run.app/**` to Redirect URLs.
3. Submit that origin as the live application link. Health check: `https://lexlens-263641821288.us-central1.run.app/api/health`.

SQLite lives at `/tmp/lexlens.db` inside the revision. Uploaded files stay in Cloud Storage. A new revision starts with an empty database, so re-upload the demo PDF after a redeploy.

Google Cloud Storage and Document AI use Application Default Credentials:

```bash
gcloud auth application-default login
```

### Environment variables

Backend (`backend/.env`):

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | `development` or `production` |
| `DATABASE_URL` | SQLite by default; Postgres when set |
| `CORS_ORIGINS` | Comma-separated allowed origins |
| `SUPABASE_URL`, `SUPABASE_JWKS_URL` or `SUPABASE_JWT_SECRET` | Verify the caller |
| `AUTH_DEV_LOGIN_ENABLED`, `AUTH_DEV_JWT_SECRET` | Development-only sign-in. Refused in production. |
| `AUTH_DEMO_LOGIN_ENABLED` | One-click `demo@lexlens.app` session. Allowed in production when explicitly enabled. |
| `GCP_PROJECT_ID`, `GCS_BUCKET` | Cloud Storage. Empty bucket uses local files. |
| `DOCUMENT_AI_LOCATION`, `DOCUMENT_AI_PROCESSOR_ID` | Document OCR. Empty processor uses the local parser. |
| `GEMINI_API_KEY` | Required for live analysis |
| `GEMINI_ANALYSIS_MODEL`, `GEMINI_CHAT_MODEL` | Primary model ids |
| `GEMINI_FALLBACK_MODELS` | Comma-separated fallbacks, tried in order |
| `FRONTEND_DIST_DIR` | Built Vite `dist` path. Empty for API-only local runs; `/app/static` in Cloud Run |

Frontend (`frontend/.env`):

| Variable | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | API origin. Empty uses the Vite proxy. |
| `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` | Public Supabase client settings. Never a service key. |

## Demo

1. Landing → **Analyze a Document**.
2. Upload `demo_documents/employment_agreement.pdf`.
3. Wait until the document is ready (Cloud Storage → Document AI → Gemini classification).
4. Open **Notice & Exit Terms**, then an evidence chip such as `Page N · §8.2`.
5. The viewer highlights that clause in yellow.
6. Ask “What happens to my stock options if I resign?” The agreement has no equity clause, so the answer is that it cannot be determined from the document.
7. **Potential Concerns** shows the notice-period inconsistency without deciding which clause governs.
8. **Prepare for a Lawyer** turns the gaps into questions.

## Repository

https://github.com/Satvik42/LexLens
