from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.laundry import Pagination
from app.schemas.users import GetUser, UpdateUser
# from app.services.users import get_users_service, get_user_service, update_user_service

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get("/", response_model=list[GetUser], status_code=200)
async def get_users(
    pagination: Annotated[Pagination, Depends()],
    db: Session = Depends(get_db),
):
    pass
    # return get_users_service(db, pagination)


@router.patch("/me", status_code=204)
async def update_user(user_data: UpdateUser, db: Session = Depends(get_db)):
    pass
    # update_user_service(user_data, db)


@router.get("/{user_id}", response_model=GetUser, status_code=200)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    pass
    