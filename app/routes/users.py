from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import current_user, require_roles
from app.core.enums import UserRole
from app.db.session import get_db
from app.models.Users import User
from app.schemas.laundry import Pagination
from app.schemas.users import GetUser, UpdateUser
from app.services.users import (
    get_current_user_profile,
    get_user as get_user_service,
    list_users,
    update_current_user_profile,
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

#admin
@router.get("/", response_model=list[GetUser], status_code=200)
async def get_users(
    pagination: Annotated[Pagination, Depends()],
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN)),
):
    return list_users(pagination, db)


@router.patch("/me", status_code=204)
async def update_user(
    user_data: UpdateUser,
    user: current_user,
    db: Session = Depends(get_db),
):
    update_current_user_profile(user, user_data, db)


@router.get("/me", response_model=GetUser, status_code=200)
async def get_current_user_details(user: current_user):
    return get_current_user_profile(user)

#admin
@router.get("/{user_id}", response_model=GetUser, status_code=200)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN)),
):
    return get_user_service(user_id, db)
    