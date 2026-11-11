from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentUser, Database, require_roles
from app.core.enums import UserRole
from app.schemas.pagination import Pagination
from app.schemas.users import GetUser, UpdateUser
from app.services import users as user_service

router = APIRouter(prefix="/users", tags=["Users"])

admin_only = [Depends(require_roles(UserRole.ADMIN))]


@router.get("/", response_model=list[GetUser], dependencies=admin_only)
def list_users(pagination: Annotated[Pagination, Depends()], db: Database):
    return user_service.list_users(pagination, db)


@router.get("/me", response_model=GetUser)
def get_my_profile(user: CurrentUser):
    return user_service.get_current_user_profile(user)


@router.patch("/me", response_model=GetUser, status_code=status.HTTP_200_OK)
def update_my_profile(user_data: UpdateUser, user: CurrentUser, db: Database):
    return user_service.update_current_user_profile(user, user_data, db)


@router.get("/{user_id}", response_model=GetUser, dependencies=admin_only)
def get_user(user_id: int, db: Database):
    return user_service.get_user(user_id, db)
