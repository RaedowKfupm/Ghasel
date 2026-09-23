from fastapi import APIRouter
from fastapi import Depends

from app.schemas.users import GetUser
from app.db.session import Session, get_db
from app.services.users import get_users_service, get_user_service

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get("/", response_model=list[GetUser], status_code=200)
async def get_users(db: Session = Depends(get_db)):
    return get_users_service(db)
    

@router.get("/{user_id}", response_model=GetUser, status_code=200)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    return get_user_service(user_id, db)
    


@router.patch("/me")
async def update_user():
    