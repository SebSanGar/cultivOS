"""Authentication utilities — JWT tokens, password hashing, FastAPI dependencies."""

import hashlib
import hmac
import json
import base64
import time
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from cultivos.config import get_settings
from cultivos.db.session import get_db

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


def create_access_token(user_id: int, username: str, role: str, farm_id: Optional[int] = None) -> str:
    """Create a simple JWT-like token (HS256)."""
    settings = get_settings()
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "farm_id": farm_id,
        "exp": int(time.time()) + 86400,  # 24h
    }
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature_input = f"{header}.{body}".encode()
    sig = hmac.new(settings.jwt_secret_key.encode(), signature_input, hashlib.sha256).digest()
    signature = base64.urlsafe_b64encode(sig).decode().rstrip("=")
    return f"{header}.{body}.{signature}"


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT token. Raises HTTPException on failure."""
    settings = get_settings()
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(status_code=401, detail="Invalid token format")

    header_b, body_b, sig_b = parts
    signature_input = f"{header_b}.{body_b}".encode()
    expected_sig = hmac.new(settings.jwt_secret_key.encode(), signature_input, hashlib.sha256).digest()
    # Pad base64
    sig_padded = sig_b + "=" * (4 - len(sig_b) % 4)
    actual_sig = base64.urlsafe_b64decode(sig_padded)

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise HTTPException(status_code=401, detail="Invalid token signature")

    body_padded = body_b + "=" * (4 - len(body_b) % 4)
    payload = json.loads(base64.urlsafe_b64decode(body_padded))

    if payload.get("exp", 0) < time.time():
        raise HTTPException(status_code=401, detail="Token expired")

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
