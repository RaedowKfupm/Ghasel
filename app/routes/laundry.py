from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.laundry import (
    BranchCreate,
    BranchResponse,
    LaundryCreate,
    LaundryResponse,
    Pagination,
)

router = APIRouter(
    prefix="/laundries",
    tags=["Laundries"]
)
@router.post("/", response_model=LaundryResponse)
def create_laundry(
    laundry_data: LaundryCreate,
    db: Session = Depends(get_db),
):
    pass


@router.post("/{laundry_id}/branches", response_model=BranchResponse)
def create_laundry_branch(
    laundry_id: int,
    branch_data: BranchCreate,
    db: Session = Depends(get_db),
):
    pass

@router.get("/{laundry_id}", response_model=LaundryResponse)
def get_laundry(laundry_id: int, db: Session = Depends(get_db)):
    pass

@router.get("/{laundry_id}/branches", response_model=list[BranchResponse])
def get_laundry_branches(
    laundry_id: int,
    pagination: Annotated[Pagination, Query()],
    db: Session = Depends(get_db),
):
    pass


@router.get("/")
def get_nearby_laundries(
    pagination: Annotated[Pagination, Query()],
    db: Session = Depends(get_db),
):
    pass

