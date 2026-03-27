"""Authentication routes — register and login with rate limiting."""

import time
from collections import defaultdict
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from cultivos.auth import hash_password, verify_password, create_access_token
from cultivos.db.models import User
from cultivos.db.session import get_db
from cultivos.models.user import UserRegister, UserLogin, UserOut, TokenOut


# ── In-memory rate limiter (per-IP, per-endpoint) ───────────────────
_hits: dict[str, list[float]] = defaultdict(list)
_lock = Lock()


def _check_rate_limit(request: Request, max_calls: int, window_seconds: int = 60):
    """Raise 429 if the caller exceeds *max_calls* within *window_seconds*.

    Disabled when DB_URL points to in-memory SQLite (test mode).
    """
    import os
    if os.environ.get("DB_URL", "").startswith("sqlite:///:memory:"):
        return  # skip rate limiting during tests
    client_host = request.client.host if request.client else "unknown"
    key = f"{client_host}:{request.url.path}"
    now = time.monotonic()
    with _lock:
        timestamps = _hits[key]
        # Purge entries outside the window
        cutoff = now - window_seconds
        _hits[key] = [t for t in timestamps if t > cutoff]
        if len(_hits[key]) >= max_calls:
            raise HTTPException(status_code=429, detail="Too many requests — try again later")
        _hits[key].append(now)


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(request: Request, body: UserRegister, db: Session = Depends(get_db)):
    _check_rate_limit(request, max_calls=5, window_seconds=60)
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")
    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        role=body.role,
        farm_id=body.farm_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(request: Request, body: UserLogin, db: Session = Depends(get_db)):
    _check_rate_limit(request, max_calls=10, window_seconds=60)
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.id, user.username, user.role, user.farm_id)
    return {"access_token": token, "token_type": "bearer"}
