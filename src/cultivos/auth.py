"""Authentication utilities — JWT tokens, password hashing, FastAPI dependencies."""

import base64
import hashlib
import hmac
import time
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from cultivos.config import get_settings
from cultivos.db.session import get_db

_JWT_ALG = "HS256"
_TOKEN_TTL_SECONDS = 86400  # 24h

_security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256."""
    import os
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return base64.b64encode(salt + dk).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its PBKDF2 hash."""
    decoded = base64.b64decode(hashed.encode())
    salt = decoded[:16]
    stored_dk = decoded[16:]
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return hmac.compare_digest(dk, stored_dk)


def _secret() -> str:
    settings = get_settings()
    if not settings.jwt_secret_key or len(settings.jwt_secret_key) < 16:
        raise HTTPException(status_code=500, detail="Server misconfigured: JWT secret not set")
    return settings.jwt_secret_key


def create_access_token(user_id: int, username: str, role: str, farm_id: Optional[int] = None) -> str:
    """Create a signed JWT (HS256) via PyJWT."""
    now = int(time.time())
    payload = {
        "sub": str(user_id),  # RFC 7519 requires a string subject
        "username": username,
        "role": role,
        "farm_id": farm_id,
        "exp": now + _TOKEN_TTL_SECONDS,
        "iat": now,
    }
    return jwt.encode(payload, _secret(), algorithm=_JWT_ALG)


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT via PyJWT. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(
            token, _secret(), algorithms=[_JWT_ALG],
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    # Coerce sub back to int for downstream code that expects the original type
    if isinstance(payload.get("sub"), str) and payload["sub"].isdigit():
        payload["sub"] = int(payload["sub"])
    return payload


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_security),
    db: Session = Depends(get_db),
):
    """FastAPI dependency — extract and validate user from Bearer token."""
    settings = get_settings()
    if not settings.auth_enabled:
        return None  # Auth disabled — allow all
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_access_token(credentials.credentials)

    from cultivos.db.models import User
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_security),
    db: Session = Depends(get_db),
):
    """FastAPI dependency — returns user if authenticated, None if not. For public-read endpoints."""
    if credentials is None:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        from cultivos.db.models import User
        return db.query(User).filter(User.id == payload["sub"]).first()
    except HTTPException:
        return None


def require_role(*roles: str):
    """Dependency factory — require the current user to have one of the given roles."""
    def _check(user=Depends(get_current_user)):
        if user is None:
            return None  # Auth disabled
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return _check
