from fastapi import APIRouter, status

from app.core.dependencies import Database
from app.schemas.auth import ResponseUser, UserLogin, UserRegister
from app.services.auth import login_user_service, register_user_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=ResponseUser, status_code=status.HTTP_201_CREATED)
def register_user(info: UserRegister, db: Database):
    return register_user_service(info, db)


@router.post("/login", response_model=ResponseUser)
def login_user(info: UserLogin, db: Database):
    return login_user_service(info, db)
