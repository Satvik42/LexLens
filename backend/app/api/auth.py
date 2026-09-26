"""Development and demo sign-in. Arbitrary-email /dev-session is disabled in production."""

import hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.config import Settings, get_settings
from app.security.auth import mint_dev_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class DevSessionRequest(BaseModel):
    email: EmailStr


class SessionOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str


def _local_session(email: str, settings: Settings, prefix: str) -> SessionOut:
    user_id = prefix + hashlib.sha256(email.encode("utf-8")).hexdigest()[:24]
    return SessionOut(access_token=mint_dev_token(user_id, email, settings), email=email)


@router.post("/dev-session", response_model=SessionOut)
def create_dev_session(payload: DevSessionRequest, settings: Settings = Depends(get_settings)) -> SessionOut:
    if not settings.dev_login_allowed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "NOT_FOUND", "message": "Not found."})
    return _local_session(payload.email.lower(), settings, "dev-")


@router.post("/demo-session", response_model=SessionOut)
def create_demo_session(settings: Settings = Depends(get_settings)) -> SessionOut:
    """Fixed-email demo account. No inbox required. Used when Supabase OTP is rate-limited."""
    if not settings.demo_login_allowed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "NOT_FOUND", "message": "Not found."})
    return _local_session(settings.auth_demo_login_email.lower(), settings, "demo-")


@router.get("/config")
def auth_config(settings: Settings = Depends(get_settings)) -> dict:
    """Non-secret configuration the frontend needs to pick a sign-in method."""
    return {
        "dev_login": settings.dev_login_allowed,
        "demo_login": settings.demo_login_allowed,
        "supabase_url": settings.supabase_url,
    }
