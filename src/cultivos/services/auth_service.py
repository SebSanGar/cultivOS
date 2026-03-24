"""Authentication service — PIN hashing, JWT tokens, user CRUD."""

from datetime import datetime, timezone, timedelta

import bcrypt
import jwt
from sqlalchemy.orm import Session

from cultivos.db.models import User
from cultivos.models.auth import UserCreate


# ---------------------------------------------------------------------------
# PIN hashing
# ---------------------------------------------------------------------------

def hash_pin(pin: str) -> str:
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()


def verify_pin(pin: str, pin_hash: str) -> bool:
    return bcrypt.checkpw(pin.encode(), pin_hash.encode())


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------

_ALGORITHM = "HS256"


def create_access_token(user: User, secret: str, expires_minutes: int = 480) -> str:
    payload = {
        "sub": str(user.id),
        "location_id": user.location_id,
        "role": user.role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, secret, algorithm=_ALGORITHM)


def decode_access_token(token: str, secret: str) -> dict:
    """Decode and validate a JWT. Raises ValueError on any failure."""
    try:
        return jwt.decode(token, secret, algorithms=[_ALGORITHM])
    except (jwt.InvalidTokenError, Exception) as e:
        raise ValueError(str(e))


# ---------------------------------------------------------------------------
# User operations
# ---------------------------------------------------------------------------

def authenticate_user(db: Session, user_id: int, pin: str) -> User | None:
    user = get_user_by_id(db, user_id)
    if not user or not user.pin_hash:
        return None
    if not verify_pin(pin, user.pin_hash):
        return None
    return user


def create_user(db: Session, data: UserCreate) -> User:
    user = User(
        name=data.name,
        email=data.email,
        role=data.role,
        pin_hash=hash_pin(data.pin),
        location_id=data.location_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session, location_id: int) -> list[User]:
    return (
        db.query(User)
        .filter(User.location_id == location_id, User.deleted_at.is_(None))
        .order_by(User.name)
        .all()
    )


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(
        User.id == user_id, User.deleted_at.is_(None)
    ).first()


def update_user_pin(db: Session, user_id: int, current_pin: str, new_pin: str) -> User | None:
    """Update a user's PIN. Returns None if current PIN is wrong."""
    user = get_user_by_id(db, user_id)
    if not user or not verify_pin(current_pin, user.pin_hash):
        return None
    user.pin_hash = hash_pin(new_pin)
    db.commit()
    db.refresh(user)
    return user
