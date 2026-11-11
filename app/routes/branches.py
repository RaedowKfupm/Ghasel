from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import Database, query_model, require_roles
from app.core.enums import UserRole
from app.models.Users import User
from app.schemas.branch import BranchResponse, BranchUpdate, NearbyBranchResponse, NearbySearch
from app.services import branches as branch_service

router = APIRouter(prefix="/branches", tags=["Branches"])

BranchStaff = Annotated[User, Depends(require_roles(UserRole.LAUNDRY, UserRole.MANAGER))]


@router.get("/nearby", response_model=list[NearbyBranchResponse])
def search_nearby_branches(search: Annotated[NearbySearch, Depends(query_model(NearbySearch))], db: Database):
    """Branches within ``radius_km`` of a point, nearest first."""
    return branch_service.search_nearby_branches(search, db)


@router.get("/{branch_id}", response_model=BranchResponse)
def get_branch(branch_id: int, db: Database):
    return branch_service.get_branch(branch_id, db)


@router.patch("/{branch_id}", response_model=BranchResponse)
def update_branch(branch_id: int, changes: BranchUpdate, user: BranchStaff, db: Database):
    return branch_service.update_branch(branch_id, changes, user, db)
