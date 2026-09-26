"""LexLens API application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import analysis, auth, comparisons, documents, lawyer_questions, questions
from app.api.deps import build_services
from app.config import get_settings
from app.db.database import init_db
from app.logging_config import configure_logging

logger = logging.getLogger(__name__)


def _error_payload(detail: object, fallback_code: str) -> dict:
    if isinstance(detail, dict) and "code" in detail:
        return {"error": detail}
    return {"error": {"code": fallback_code, "message": str(detail) if isinstance(detail, str) else "Request failed."}}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    init_db()
    if getattr(app.state, "services", None) is None:  # tests may inject a container before startup
        app.state.services = build_services(settings)
    logger.info("LexLens API started (env=%s, gcs=%s, document_ai=%s, gemini=%s)", settings.app_env, settings.uses_gcs, settings.uses_document_ai, settings.uses_gemini)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="LexLens API", version="0.1.0", lifespan=lifespan, docs_url=None if settings.is_production else "/docs", redoc_url=None)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=_error_payload(exc.detail, "HTTP_ERROR"), headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": "The request was not valid.", "details": exc.errors()}})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc.__class__.__name__)
        return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "Something went wrong. Please try again."}})

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response

    app.include_router(auth.router)
    app.include_router(documents.router)
    app.include_router(analysis.router)
    app.include_router(questions.router)
    app.include_router(lawyer_questions.router)
    app.include_router(comparisons.router)

    @app.get("/api/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
