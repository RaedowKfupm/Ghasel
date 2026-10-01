from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import ManagerOrder, OwnedLaundry, require_roles
from app.core.enums import OrderStatus, UserRole
from app.db.session import get_db
from app.models.Users import User
from app.services.laundry import (
    approve_laundry_request,
    create_laundry_branch as create_laundry_branch_service,
    create_laundry_manager,
    create_laundry_request,
    get_laundry as get_laundry_service,
    list_laundry_branches,
    list_laundry_requests,
)
from app.services.orders import set_manager_order_status
from app.schemas.laundry import (
    BranchCreate,
    BranchResponse,
    LaundryCreate,
    LaundryResponse,
    Pagination,
)
from app.schemas.laundry import (
    LaundryRequestResponse,
    ManagerCreate,
    ManagerResponse,
)
router = APIRouter(
    prefix="/laundries",
    tags=["Laundries"],
)

@router.post("/", response_model=LaundryRequestResponse, status_code=status.HTTP_201_CREATED)
def create_laundry(
    laundry_data: LaundryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.LAUNDRY)),
):
    return create_laundry_request(laundry_data, user, db)

@router.get("/requests", response_model=list[LaundryRequestResponse])
def get_laundry_requests(
    pagination: Annotated[Pagination, Depends()],
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN)),
):
    return list_laundry_requests(pagination, db)


@router.post(
    "/requests/{request_id}/approve",
    response_model=LaundryResponse,
    status_code=status.HTTP_201_CREATED,
)
def approve_laundry(
    request_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ADMIN)),
):
    return approve_laundry_request(request_id, db)


@router.post("/{laundry_id}/branches", response_model=BranchResponse)
def create_laundry_branch(
    laundry_id: int,
    branch_data: BranchCreate,
    laundry: OwnedLaundry,
    db: Session = Depends(get_db),
):
    return create_laundry_branch_service(branch_data, laundry, db)


@router.post("/{laundry_id}/managers", response_model=ManagerResponse, status_code=201)
def register_manager(
    laundry_id: int,
    manager_data: ManagerCreate,
    laundry: OwnedLaundry,
    db: Session = Depends(get_db),
):
    return create_laundry_manager(laundry, manager_data, db)


@router.post("/acceptorder", status_code=204)
def accept_order(
    order_id: int,
    order: ManagerOrder,
    db: Session = Depends(get_db),
):
    set_manager_order_status(order, OrderStatus.ACCEPTED, db)



@router.get("/{laundry_id}", response_model=LaundryResponse)
def get_laundry(laundry_id: int, db: Session = Depends(get_db)):
    return get_laundry_service(laundry_id, db)


@router.get("/{laundry_id}/branches", response_model=list[BranchResponse])
def get_laundry_branches(
    laundry_id: int,
    pagination: Annotated[Pagination, Depends()],
    db: Session = Depends(get_db),
):
    return list_laundry_branches(laundry_id, pagination, db)


@router.get("/")
def get_nearby_laundries(
    pagination: Annotated[Pagination, Depends()],
    db: Session = Depends(get_db),
):
    pass

