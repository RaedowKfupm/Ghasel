from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import Database, OwnedLaundry, Page, require_roles
from app.core.enums import UserRole
from app.models.Users import User
from app.schemas.branch import BranchCreate, BranchResponse, RatedBranchResponse
from app.schemas.laundry import (
    LaundryCreate,
    LaundryRequestResponse,
    LaundryResponse,
    ManagerCreate,
    ManagerResponse,
)
from app.services import laundry as laundry_service

router = APIRouter(prefix="/laundries", tags=["Laundries"])

admin_only = [Depends(require_roles(UserRole.ADMIN))]


@router.post("/", response_model=LaundryRequestResponse, status_code=status.HTTP_201_CREATED)
def apply_for_laundry(
    laundry_data: LaundryCreate,
    db: Database,
    owner: Annotated[User, Depends(require_roles(UserRole.LAUNDRY))],
):
    return laundry_service.create_laundry_request(laundry_data, owner, db)


@router.get("/requests/me", response_model=LaundryRequestResponse | None)
def get_my_laundry_request(db: Database, owner: Annotated[User, Depends(require_roles(UserRole.LAUNDRY))]):
    """The owner's most recent application, or null if they have never applied."""
    return laundry_service.get_latest_request(owner, db)


@router.get("/requests", response_model=list[LaundryRequestResponse], dependencies=admin_only)
def list_laundry_requests(pagination: Page, db: Database):
    return laundry_service.list_laundry_requests(pagination, db)


@router.post(
    "/requests/{request_id}/approve",
    response_model=LaundryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=admin_only,
)
def approve_laundry_request(request_id: int, db: Database):
    return laundry_service.approve_laundry_request(request_id, db)


@router.get("/{laundry_id}", response_model=LaundryResponse)
def get_laundry(laundry_id: int, db: Database):
    return laundry_service.get_laundry(laundry_id, db)


@router.get("/{laundry_id}/branches", response_model=list[RatedBranchResponse])
def list_laundry_branches(laundry_id: int, pagination: Page, db: Database):
    return laundry_service.list_laundry_branches(laundry_id, pagination, db)


@router.post(
    "/{laundry_id}/branches",
    response_model=BranchResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_laundry_branch(branch_data: BranchCreate, laundry: OwnedLaundry, db: Database):
    return laundry_service.create_laundry_branch(branch_data, laundry, db)


@router.post(
    "/{laundry_id}/managers",
    response_model=ManagerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_branch_manager(manager_data: ManagerCreate, laundry: OwnedLaundry, db: Database):
    return laundry_service.create_laundry_manager(laundry, manager_data, db)


@router.get("/{laundry_id}/managers", response_model=list[ManagerResponse])
def list_branch_managers(laundry: OwnedLaundry, db: Database):
    return laundry_service.list_laundry_managers(laundry, db)
