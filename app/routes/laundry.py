from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import ManagerOrder, OwnedLaundry, require_roles
from app.core.enums import UserRole
from app.db.session import get_db
from app.models.Users import User
from app.schemas.laundry import (
    BranchCreate,
    BranchResponse,
    LaundryCreate,
    LaundryResponse,
    Pagination,
)

router = APIRouter(
    prefix="/laundries",
    tags=["Laundries"],
)

#laundryOwner
@router.post("/", response_model=LaundryResponse)
def create_laundry(
    laundry_data: LaundryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.LAUNDRY)),
):
    pass

#laundryOwner
@router.post("/{laundry_id}/branches", response_model=BranchResponse)
def create_laundry_branch(
    laundry_id: int,
    branch_data: BranchCreate,
    laundry: OwnedLaundry,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.LAUNDRY)),
):
    pass
#LaudnryManager
@router.post("/acceptorder", status_code=204)
def accept_order(
    order_id: int,
    order: ManagerOrder,
    db: Session = Depends(get_db),
):
    pass



@router.get("/{laundry_id}", response_model=LaundryResponse)
def get_laundry(laundry_id: int, db: Session = Depends(get_db)):
    pass


@router.get("/{laundry_id}/branches", response_model=list[BranchResponse])
def get_laundry_branches(
    laundry_id: int,
    pagination: Annotated[Pagination, Depends()],
    db: Session = Depends(get_db),
):
    pass


@router.get("/")
def get_nearby_laundries(
    pagination: Annotated[Pagination, Depends()],
    db: Session = Depends(get_db),
):
    pass

