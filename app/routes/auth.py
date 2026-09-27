from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.auth import login_user_service, register_user_service
from app.db.session import get_db
from app.schemas.auth import ResponseUser, UserLogin, UserRegister

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register", status_code=201, response_model=ResponseUser)
async def register_user(info: UserRegister, db: Session = Depends(get_db)):
    return register_user_service(info, db)


@router.post("/login", response_model=ResponseUser, status_code=200)
async def login_user(info: UserLogin, db: Session = Depends(get_db)):
    return login_user_service(info, db)
