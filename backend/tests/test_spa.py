"""Same-origin SPA serving so Cloud Run can host the UI and API on one URL."""

from fastapi.testclient import TestClient

from app.config import get_settings
from app.db.database import init_db
from app.main import create_app


def _spa_client(tmp_path, monkeypatch) -> TestClient:
    dist = tmp_path / "dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><html><title>LexLens</title><div id='root'></div></html>")
    (assets / "app.js").write_text("window.__lexlens = true;")
    (dist / "favicon.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>")
    settings = get_settings()
    monkeypatch.setattr(settings, "frontend_dist_dir", str(dist))
    app = create_app()
    init_db()
    return TestClient(app)


def test_api_only_mode_has_no_spa_when_dist_is_missing(client):
    response = client.get("/")
    assert response.status_code == 404
    assert client.get("/api/health").json() == {"status": "ok"}


def test_health_is_unchanged_when_frontend_is_mounted(tmp_path, monkeypatch):
    with _spa_client(tmp_path, monkeypatch) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_root_and_client_routes_return_the_spa(tmp_path, monkeypatch):
    with _spa_client(tmp_path, monkeypatch) as client:
        for path in ("/", "/upload", "/sign-in", "/documents/abc/intents"):
            response = client.get(path)
            assert response.status_code == 200, path
            assert "text/html" in response.headers["content-type"]
            assert "LexLens" in response.text


def test_built_assets_are_served_from_dist(tmp_path, monkeypatch):
    with _spa_client(tmp_path, monkeypatch) as client:
        response = client.get("/assets/app.js")
        assert response.status_code == 200
        assert "window.__lexlens" in response.text


def test_unknown_api_paths_are_not_replaced_by_the_spa(tmp_path, monkeypatch):
    with _spa_client(tmp_path, monkeypatch) as client:
        response = client.get("/api/does-not-exist")
        assert response.status_code == 404
        assert "text/html" not in response.headers.get("content-type", "")


def test_path_traversal_does_not_escape_the_dist(tmp_path, monkeypatch):
    (tmp_path / "secret.txt").write_text("should-not-leak")
    with _spa_client(tmp_path, monkeypatch) as client:
        response = client.get("/../secret.txt")
        assert "should-not-leak" not in response.text
