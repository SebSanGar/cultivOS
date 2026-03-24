"""Auth API routes — login, user profile, PIN management, user CRUD."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cultivos.config import get_settings
from cultivos.db.models import User
from cultivos.db.session import get_db
from cultivos.models.auth import (
    PinLogin,
    PinUpdate,
    TokenResponse,
    UserCreate,
    UserRead,
)
from cultivos.api.deps import get_current_user, require_role
from cultivos.services import auth_service

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
def login(data: PinLogin, db: Session = Depends(get_db)):
    """Authenticate with user_id + PIN, receive JWT."""
    user = auth_service.authenticate_user(db, data.user_id, data.pin)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    settings = get_settings()
    token = auth_service.create_access_token(
        user, settings.jwt_secret_key, settings.jwt_expiry_minutes
    )
    return TokenResponse(
        access_token=token,
        user=UserRead.model_validate(user),
    )


@router.get("/auth/me", response_model=UserRead)
def get_me(user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return UserRead.model_validate(user)


@router.put("/auth/pin")
def update_pin(
    data: PinUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user's PIN."""
    updated = auth_service.update_user_pin(db, user.id, data.current_pin, data.new_pin)
    if not updated:
        raise HTTPException(status_code=401, detail="Current PIN is incorrect")
    return {"detail": "PIN updated"}


@router.post("/users", response_model=UserRead, status_code=201)
def create_user(
    data: UserCreate,
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Create a new user (admin only)."""
    new_user = auth_service.create_user(db, data)
    return UserRead.model_validate(new_user)


@router.get("/users", response_model=list[UserRead])
def list_users(
    location_id: int = Query(...),
    user: User = Depends(require_role("manager", "admin")),
    db: Session = Depends(get_db),
):
    """List users at a location (manager+ only)."""
    return [UserRead.model_validate(u) for u in auth_service.list_users(db, location_id)]
