"""Serve a built Vite app from the same origin as the API."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse


def mount_frontend(app: FastAPI, dist_dir: str) -> None:
    if not dist_dir:
        return
    root = Path(dist_dir).resolve()
    index = root / "index.html"
    if not index.is_file():
        return

    @app.get("/")
    def spa_root() -> FileResponse:
        return FileResponse(index)

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str) -> FileResponse:
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Not found."})
        candidate = (root / full_path).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            return FileResponse(index)
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)
