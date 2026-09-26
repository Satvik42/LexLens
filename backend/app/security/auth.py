"""Token verification. Identity is derived only from a verified JWT, never from client-provided IDs."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

DEV_ISSUER = "lexlens-dev"
DEV_TOKEN_TTL = timedelta(hours=12)

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str | None


class AuthError(HTTPException):
    def __init__(self, detail: str = "Authentication required") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


@lru_cache
def _jwks_client(url: str) -> PyJWKClient:
    return PyJWKClient(url, cache_keys=True)


def _decode_with_options(token: str, key: str, algorithms: list[str]) -> dict:
    return jwt.decode(
        token,
        key,
        algorithms=algorithms,
        audience="authenticated",
        options={"require": ["sub", "exp"]},
    )


def _decode_supabase(token: str, settings: Settings) -> dict:
    if settings.supabase_jwks_url:
        signing_key = _jwks_client(settings.supabase_jwks_url).get_signing_key_from_jwt(token)
        return _decode_with_options(token, signing_key.key, ["RS256", "ES256"])
    if settings.supabase_jwt_secret:
        return _decode_with_options(token, settings.supabase_jwt_secret, ["HS256"])
    raise AuthError("Authentication is not configured")


def _decode_dev(token: str, settings: Settings) -> dict:
    return jwt.decode(
        token,
        settings.auth_dev_jwt_secret,
        algorithms=["HS256"],
        issuer=DEV_ISSUER,
        options={"require": ["sub", "exp", "iss"]},
    )


def decode_token(token: str, settings: Settings) -> AuthenticatedUser:
    """Verify a bearer token and return the authenticated identity."""
    try:
        unverified = jwt.decode(token, options={"verify_signature": False})
    except jwt.PyJWTError as exc:
        raise AuthError("Invalid token") from exc

    try:
        if unverified.get("iss") == DEV_ISSUER:
            if not settings.local_session_allowed:
                raise AuthError("Invalid token")
            claims = _decode_dev(token, settings)
        else:
            claims = _decode_supabase(token, settings)
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Session expired") from exc
    except jwt.PyJWTError as exc:
        logger.info("Rejected token: %s", exc.__class__.__name__)
        raise AuthError("Invalid token") from exc

    return AuthenticatedUser(id=str(claims["sub"]), email=claims.get("email"))


def mint_dev_token(user_id: str, email: str, settings: Settings) -> str:
    """Create a LexLens-issued session token. Only callable when local sessions are allowed."""
    if not settings.local_session_allowed:
        raise RuntimeError("Development login is disabled")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "iss": DEV_ISSUER,
        "iat": now,
        "exp": now + DEV_TOKEN_TTL,
    }
    return jwt.encode(payload, settings.auth_dev_jwt_secret, algorithm="HS256")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthError()
    return decode_token(credentials.credentials, settings)
