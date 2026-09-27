from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, insert
from app.db.session import get_db
from app.core.dependencies import current_user
from app.core.security import create_access_token, authenticate_user, hash_password, decode_access_token
from app.schemas.auth import ResponseUser, UserLogin, UserRegister
from app.models.Users import User


def register_user_service(info: UserRegister, db: Session):
    q = db.scalar(select(User).where(User.email== info.email))
    if q: 
        raise HTTPException(status_code=400, detail="Email already registered")
    info.password = hash_password(info.password)
    user_data = info.model_dump()
    db.execute(insert(User).values(password_hash=user_data.pop("password"), **user_data))
    db.commit()
    jwt_token = create_access_token({"sub": str(db.scalar(select(User.id).where(User.email== info.email)))})
    return ResponseUser(access_token=jwt_token, token_type="Bearer", **user_data)


def login_user_service(info: UserLogin, db: Session):
   user = authenticate_user(info.email, info.password, db)
   if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

   token = create_access_token({"sub": str(user.id)})
   return ResponseUser(
    access_token=token,
    token_type="Bearer",
    name=user.name,
    email=user.email,
    role=user.role,
    )