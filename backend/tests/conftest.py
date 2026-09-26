"""Test fixtures: isolated settings, in-memory-ish SQLite, fake Gemini, authenticated clients."""

import os
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="lexlens-test-")
os.environ.update(
    {
        "APP_ENV": "test",
        "DATABASE_URL": f"sqlite:///{_TMP}/test.db",
        "LOCAL_STORAGE_DIR": f"{_TMP}/storage",
        "AUTH_DEV_LOGIN_ENABLED": "true",
        "AUTH_DEV_JWT_SECRET": "test-secret-not-for-production-0123456789abcdef",
        "GEMINI_API_KEY": "",
        "GCS_BUCKET": "",
        "DOCUMENT_AI_PROCESSOR_ID": "",
        "RATE_LIMIT_PER_MINUTE": "50",
    }
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api.deps import ServiceContainer, build_services  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.db.database import Base, engine, init_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.security.auth import mint_dev_token  # noqa: E402
from app.security.rate_limit import limiter  # noqa: E402
from app.services.document_processing_service import DocumentParser, DocumentProcessingService  # noqa: E402
from tests.fake_model import FakeModel  # noqa: E402

DEMO_DIR = Path(__file__).resolve().parents[2] / "demo_documents"


@pytest.fixture(scope="session")
def demo_pdf() -> bytes:
    return (DEMO_DIR / "employment_agreement.pdf").read_bytes()


@pytest.fixture(scope="session")
def demo_txt() -> bytes:
    return (DEMO_DIR / "src" / "employment_agreement.txt").read_bytes()


@pytest.fixture
def fake_model() -> FakeModel:
    return FakeModel()


@pytest.fixture
def client(fake_model: FakeModel) -> TestClient:
    settings = get_settings()
    app = create_app()
    init_db()
    Base.metadata.drop_all(bind=engine)  # every test starts from an empty database
    Base.metadata.create_all(bind=engine)
    base = build_services(settings)
    app.state.services = ServiceContainer(
        storage=base.storage,
        processing=DocumentProcessingService(settings, base.storage, DocumentParser(settings), None),
        model=fake_model,
    )
    limiter.reset()
    with TestClient(app) as test_client:
        yield test_client


def auth_headers(email: str = "alice@example.com") -> dict[str, str]:
    settings = get_settings()
    token = mint_dev_token(f"user-{email}", email, settings)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def alice() -> dict[str, str]:
    return auth_headers("alice@example.com")


@pytest.fixture
def bob() -> dict[str, str]:
    return auth_headers("bob@example.com")


def upload(client: TestClient, headers: dict[str, str], content: bytes, filename: str = "agreement.pdf", mime: str = "application/pdf"):
    return client.post("/api/documents", headers=headers, files={"file": (filename, content, mime)})


@pytest.fixture
def ready_document(client: TestClient, alice: dict[str, str], demo_pdf: bytes) -> dict:
    response = upload(client, alice, demo_pdf)
    assert response.status_code == 201, response.text
    document = response.json()
    status = client.get(f"/api/documents/{document['id']}/status", headers=alice).json()
    assert status["processing_status"] == "READY", status
    return client.get(f"/api/documents/{document['id']}", headers=alice).json()
