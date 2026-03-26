"""Authentication routes — register and login."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cultivos.auth import hash_password, verify_password, create_access_token
from cultivos.db.models import User
from cultivos.db.session import get_db
from cultivos.models.user import UserRegister, UserLogin, UserOut, TokenOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: UserRegister, db: Session = Depends(get_db)):
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
def login(body: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.id, user.username, user.role, user.farm_id)
    return {"access_token": token, "token_type": "bearer"}
