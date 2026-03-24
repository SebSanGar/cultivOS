"""Pydantic schemas for authentication and user management."""

import re
from datetime import datetime

from pydantic import BaseModel, field_validator


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

_PIN_PATTERN = re.compile(r"^\d{4,6}$")
_VALID_ROLES = {"staff", "lead", "manager", "admin"}


def _validate_pin(v: str) -> str:
    if not _PIN_PATTERN.match(v):
        raise ValueError("PIN must be 4-6 digits")
    return v


def _validate_role(v: str) -> str:
    if v not in _VALID_ROLES:
        raise ValueError(f"Role must be one of: {', '.join(sorted(_VALID_ROLES))}")
    return v


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class PinLogin(BaseModel):
    user_id: int
    pin: str

    @field_validator("pin")
    @classmethod
    def pin_format(cls, v: str) -> str:
        return _validate_pin(v)


class UserRead(BaseModel):
    id: int
    name: str
    email: str | None
    role: str
    location_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    name: str
    email: str | None = None
    role: str = "staff"
    pin: str
    location_id: int

    @field_validator("pin")
    @classmethod
    def pin_format(cls, v: str) -> str:
        return _validate_pin(v)

    @field_validator("role")
    @classmethod
    def role_valid(cls, v: str) -> str:
        return _validate_role(v)


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    role: str | None = None

    @field_validator("role")
    @classmethod
    def role_valid(cls, v: str | None) -> str | None:
        if v is not None:
            return _validate_role(v)
        return v


class PinUpdate(BaseModel):
    current_pin: str
    new_pin: str

    @field_validator("new_pin")
    @classmethod
    def pin_format(cls, v: str) -> str:
        return _validate_pin(v)
