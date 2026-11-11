"""Branch discovery and branch management.

Distances are computed by PostGIS on the ``geography`` column (metres on the
WGS 84 spheroid). ``ST_DWithin`` is index-aware, so the radius filter uses the
GiST index on ``Branches.location`` instead of scanning every branch.
"""

from sqlalchemy import Float, Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import UserRole
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.db.spatial import METRES_PER_KM, point
from app.models.LaundryProfiles import LaundryBranch
from app.models.Users import User
from app.schemas.branch import BranchUpdate, NearbyBranchResponse, NearbySearch

def nearby_branches_query(search: NearbySearch) -> Select:
    """Branches within the search radius with their distance in metres, nearest first."""
    origin = point(search.latitude, search.longitude)
    distance_m = func.ST_Distance(LaundryBranch.location, origin, type_=Float)
    return (
        select(LaundryBranch, distance_m.label("distance_m"))
        .where(func.ST_DWithin(LaundryBranch.location, origin, search.radius_km * METRES_PER_KM))
        .order_by(distance_m, LaundryBranch.id)
        .offset(search.offset)
        .limit(search.limit)
    )


def search_nearby_branches(search: NearbySearch, db: Session) -> list[NearbyBranchResponse]:
    query = nearby_branches_query(search).options(selectinload(LaundryBranch.laundry))
    return [_nearby_response(branch, distance) for branch, distance in db.execute(query)]


def _nearby_response(branch: LaundryBranch, distance_m: float) -> NearbyBranchResponse:
    fields = {name: getattr(branch, name) for name in NearbyBranchResponse.model_fields if name != "distance_km"}
    return NearbyBranchResponse(**fields, distance_km=round(distance_m / METRES_PER_KM, 3))


def get_branch(branch_id: int, db: Session) -> LaundryBranch:
    branch = db.get(LaundryBranch, branch_id, options=[selectinload(LaundryBranch.laundry)])
    if branch is None:
        raise NotFoundError("Branch not found")
    return branch


def can_manage_branch(user: User, branch: LaundryBranch) -> bool:
    """Owners manage every branch of their company; managers only their own branch."""
    if user.role == UserRole.LAUNDRY:
        return user.laundry_id is not None and user.laundry_id == branch.laundry_id
    if user.role == UserRole.MANAGER:
        return user.laundry_branch_id == branch.id
    return False


def update_branch(branch_id: int, changes: BranchUpdate, user: User, db: Session) -> LaundryBranch:
    branch = get_branch(branch_id, db)
    if not can_manage_branch(user, branch):
        raise PermissionDeniedError("You cannot manage this branch")

    for field, value in changes.model_dump(exclude_unset=True).items():
        if value is None and field not in ("latitude", "longitude"):
            continue  # required columns are never cleared
        setattr(branch, field, value)
    db.commit()
    return get_branch(branch_id, db)
