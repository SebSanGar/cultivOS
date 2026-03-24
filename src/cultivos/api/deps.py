"""FastAPI auth dependencies — current user, optional user, role gates."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from cultivos.config import get_settings
from cultivos.db.models import User
from cultivos.db.session import get_db
from cultivos.services import auth_service

_bearer = HTTPBearer()
_bearer_optional = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Mandatory auth — 401 if missing or invalid token."""
    settings = get_settings()
    try:
        payload = auth_service.decode_access_token(
            credentials.credentials, settings.jwt_secret_key
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = auth_service.get_user_by_id(db, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
    db: Session = Depends(get_db),
) -> User | None:
    """Optional auth — None if no token, 401 if token is invalid."""
    if credentials is None:
        return None
    settings = get_settings()
    try:
        payload = auth_service.decode_access_token(
            credentials.credentials, settings.jwt_secret_key
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return auth_service.get_user_by_id(db, int(payload["sub"]))


def require_role(*allowed_roles: str):
    """Dependency factory — 403 if user's role not in allowed_roles."""
    def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return _check
