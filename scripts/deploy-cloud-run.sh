#!/usr/bin/env bash
# Build and deploy LexLens as one Cloud Run service (UI + API).
# Reads public frontend values and backend secrets from local .env files.
# Does not print secret values.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${GCP_PROJECT_ID:-lexlens-509608}"
REGION="${CLOUD_RUN_REGION:-us-central1}"
SERVICE="${CLOUD_RUN_SERVICE:-lexlens}"
REPO="${ARTIFACT_REPO:-lexlens}"

env_value() {
  local file="$1"
  local key="$2"
  python3 - "$file" "$key" <<'PY'
from pathlib import Path
import sys
path, key = Path(sys.argv[1]), sys.argv[2]
if not path.exists():
    raise SystemExit(f"missing {path}")
for raw in path.read_text().splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    name, _, value = line.partition("=")
    if name.strip() == key:
        print(value.strip().strip('"').strip("'"), end="")
        raise SystemExit(0)
raise SystemExit(f"missing {key} in {path}")
PY
}

optional_env() {
  local file="$1"
  local key="$2"
  local default="${3:-}"
  python3 - "$file" "$key" "$default" <<'PY'
from pathlib import Path
import sys
path, key, default = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
if not path.exists():
    print(default, end="")
    raise SystemExit(0)
for raw in path.read_text().splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    name, _, value = line.partition("=")
    if name.strip() == key:
        print(value.strip().strip('"').strip("'"), end="")
        raise SystemExit(0)
print(default, end="")
PY
}

BACKEND_ENV="$ROOT/backend/.env"
FRONTEND_ENV="$ROOT/frontend/.env"

VITE_SUPABASE_URL="$(optional_env "$FRONTEND_ENV" VITE_SUPABASE_URL)"
VITE_SUPABASE_ANON_KEY="$(optional_env "$FRONTEND_ENV" VITE_SUPABASE_ANON_KEY)"
GEMINI_API_KEY="$(env_value "$BACKEND_ENV" GEMINI_API_KEY)"
SUPABASE_URL="$(optional_env "$BACKEND_ENV" SUPABASE_URL "$VITE_SUPABASE_URL")"
if [[ -z "$VITE_SUPABASE_URL" && -n "$SUPABASE_URL" ]]; then
  VITE_SUPABASE_URL="$SUPABASE_URL"
fi
SUPABASE_JWKS_URL="$(optional_env "$BACKEND_ENV" SUPABASE_JWKS_URL)"
GCP_PROJECT="$(optional_env "$BACKEND_ENV" GCP_PROJECT_ID "$PROJECT")"
GCS_BUCKET="$(optional_env "$BACKEND_ENV" GCS_BUCKET lexlens-docs)"
DOCUMENT_AI_LOCATION="$(optional_env "$BACKEND_ENV" DOCUMENT_AI_LOCATION us)"
DOCUMENT_AI_PROCESSOR_ID="$(optional_env "$BACKEND_ENV" DOCUMENT_AI_PROCESSOR_ID)"
AUTH_DEV_JWT_SECRET="$(env_value "$BACKEND_ENV" AUTH_DEV_JWT_SECRET)"
AUTH_DEMO_LOGIN_ENABLED="$(optional_env "$BACKEND_ENV" AUTH_DEMO_LOGIN_ENABLED false)"
GEMINI_ANALYSIS_MODEL="$(optional_env "$BACKEND_ENV" GEMINI_ANALYSIS_MODEL gemini-3-flash-preview)"
GEMINI_CHAT_MODEL="$(optional_env "$BACKEND_ENV" GEMINI_CHAT_MODEL gemini-3-flash-preview)"
GEMINI_FALLBACK_MODELS="$(optional_env "$BACKEND_ENV" GEMINI_FALLBACK_MODELS gemini-3.5-flash,gemini-2.5-flash,gemini-flash-latest,gemini-3.1-pro-preview)"

if [[ -z "$GEMINI_API_KEY" ]]; then
  echo "GEMINI_API_KEY is empty in backend/.env" >&2
  exit 1
fi
if [[ -z "$VITE_SUPABASE_URL" || -z "$VITE_SUPABASE_ANON_KEY" ]]; then
  echo "Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in frontend/.env so production sign-in works." >&2
  exit 1
fi

IMAGE="${REGION}-docker.pkg.dev/${GCP_PROJECT}/${REPO}/${SERVICE}"

echo "Project: ${GCP_PROJECT}"
echo "Region:  ${REGION}"
echo "Service: ${SERVICE}"
echo "Image:   ${IMAGE}"

gcloud config set project "$GCP_PROJECT"
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  documentai.googleapis.com \
  storage.googleapis.com

if ! gcloud artifacts repositories describe "$REPO" --location="$REGION" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$REPO" --repository-format=docker --location="$REGION" --description="LexLens Cloud Run images"
fi

if ! gcloud secrets describe GEMINI_API_KEY >/dev/null 2>&1; then
  printf '%s' "$GEMINI_API_KEY" | gcloud secrets create GEMINI_API_KEY --data-file=-
else
  printf '%s' "$GEMINI_API_KEY" | gcloud secrets versions add GEMINI_API_KEY --data-file=-
fi

PROJECT_NUMBER="$(gcloud projects describe "$GCP_PROJECT" --format='value(projectNumber)')"
RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

if ! gcloud secrets describe AUTH_DEV_JWT_SECRET >/dev/null 2>&1; then
  printf '%s' "$AUTH_DEV_JWT_SECRET" | gcloud secrets create AUTH_DEV_JWT_SECRET --data-file=-
else
  printf '%s' "$AUTH_DEV_JWT_SECRET" | gcloud secrets versions add AUTH_DEV_JWT_SECRET --data-file=-
fi

gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/secretmanager.secretAccessor" >/dev/null
gcloud secrets add-iam-policy-binding AUTH_DEV_JWT_SECRET \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/secretmanager.secretAccessor" >/dev/null

for ROLE in \
  roles/storage.objectAdmin \
  roles/documentai.apiUser \
  roles/logging.logWriter \
  roles/artifactregistry.writer \
  roles/cloudbuild.builds.builder
do
  gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
    --member="serviceAccount:${RUNTIME_SA}" \
    --role="$ROLE" >/dev/null
done
gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/artifactregistry.writer" >/dev/null

echo "Building container in Cloud Build..."
gcloud builds submit "$ROOT" \
  --config="$ROOT/cloudbuild.yaml" \
  --substitutions="_IMAGE=${IMAGE},_VITE_SUPABASE_URL=${VITE_SUPABASE_URL},_VITE_SUPABASE_ANON_KEY=${VITE_SUPABASE_ANON_KEY}"

ENV_FILE="$(mktemp)"
cat > "$ENV_FILE" <<EOF
APP_ENV: production
LOG_LEVEL: INFO
DATABASE_URL: sqlite:////tmp/lexlens.db
FRONTEND_DIST_DIR: /app/static
AUTH_DEV_LOGIN_ENABLED: "false"
AUTH_DEMO_LOGIN_ENABLED: "${AUTH_DEMO_LOGIN_ENABLED}"
GCP_PROJECT_ID: ${GCP_PROJECT}
GCS_BUCKET: ${GCS_BUCKET}
DOCUMENT_AI_LOCATION: ${DOCUMENT_AI_LOCATION}
DOCUMENT_AI_PROCESSOR_ID: ${DOCUMENT_AI_PROCESSOR_ID}
SUPABASE_URL: ${SUPABASE_URL}
SUPABASE_JWKS_URL: ${SUPABASE_JWKS_URL}
GEMINI_ANALYSIS_MODEL: ${GEMINI_ANALYSIS_MODEL}
GEMINI_CHAT_MODEL: ${GEMINI_CHAT_MODEL}
GEMINI_FALLBACK_MODELS: "${GEMINI_FALLBACK_MODELS}"
CORS_ORIGINS: http://localhost:5173
EOF

echo "Deploying Cloud Run service..."
gcloud run deploy "$SERVICE" \
  --image="$IMAGE" \
  --region="$REGION" \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300 \
  --concurrency=10 \
  --cpu-boost \
  --no-cpu-throttling \
  --set-secrets="GEMINI_API_KEY=GEMINI_API_KEY:latest,AUTH_DEV_JWT_SECRET=AUTH_DEV_JWT_SECRET:latest" \
  --env-vars-file="$ENV_FILE"
rm -f "$ENV_FILE"

URL="$(gcloud run services describe "$SERVICE" --region="$REGION" --format='value(status.url)')"
gcloud run services update "$SERVICE" \
  --region="$REGION" \
  --update-env-vars="CORS_ORIGINS=${URL}"

echo
echo "Deployed: ${URL}"
echo "Health:   ${URL}/api/health"
echo
echo "In Supabase → Authentication → URL configuration, set:"
echo "  Site URL:      ${URL}"
echo "  Redirect URLs: ${URL}/**"
