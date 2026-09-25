from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import ResponseUser, UserLogin, UserRegister

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register", status_code=201, response_model=ResponseUser)
async def register_user(info: UserRegister, db: Session = Depends(get_db)):
    raise HTTPException(status_code=501, detail="Registration service is not implemented yet")


@router.post("/login", response_model=ResponseUser, status_code=200)
async def login_user(info: UserLogin, db: Session = Depends(get_db)):
    raise HTTPException(status_code=501, detail="Login service is not implemented yet")

