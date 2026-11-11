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
from app.schemas.branch import BranchUpdate, NearbyBranchResponse, NearbySearch, RatedBranchResponse
from app.schemas.pagination import Pagination
from app.services.reviews import rating_summary


def _with_ratings(query: Select) -> Select:
    """Add rating_average/rating_count columns (NULL/0 for unreviewed branches)."""
    ratings = rating_summary().subquery("ratings")
    return query.outerjoin(ratings, ratings.c.branch_id == LaundryBranch.id).add_columns(
        ratings.c.rating_average,
        func.coalesce(ratings.c.rating_count, 0).label("rating_count"),
    )


def _rated(branch: LaundryBranch, rating_average: float | None, rating_count: int, **extra) -> dict:
    fields = {name: getattr(branch, name) for name in RatedBranchResponse.model_fields if hasattr(branch, name)}
    return {**fields, "rating_average": rating_average, "rating_count": rating_count, **extra}


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
    query = _with_ratings(nearby_branches_query(search)).options(selectinload(LaundryBranch.laundry))
    return [
        NearbyBranchResponse(**_rated(branch, average, count, distance_km=round(distance / METRES_PER_KM, 3)))
        for branch, distance, average, count in db.execute(query)
    ]


def list_rated_branches(laundry_id: int, pagination: Pagination, db: Session) -> list[RatedBranchResponse]:
    query = _with_ratings(
        select(LaundryBranch)
        .options(selectinload(LaundryBranch.laundry))
        .where(LaundryBranch.laundry_id == laundry_id)
        .order_by(LaundryBranch.id)
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    return [RatedBranchResponse(**_rated(*row)) for row in db.execute(query)]


def get_branch(branch_id: int, db: Session) -> RatedBranchResponse:
    query = _with_ratings(
        select(LaundryBranch).options(selectinload(LaundryBranch.laundry)).where(LaundryBranch.id == branch_id)
    )
    row = db.execute(query).first()
    if row is None:
        raise NotFoundError("Branch not found")
    return RatedBranchResponse(**_rated(*row))


def can_manage_branch(user: User, branch: LaundryBranch) -> bool:
    """Owners manage every branch of their company; managers only their own branch."""
    if user.role == UserRole.LAUNDRY:
        return user.laundry_id is not None and user.laundry_id == branch.laundry_id
    if user.role == UserRole.MANAGER:
        return user.laundry_branch_id == branch.id
    return False


def update_branch(branch_id: int, changes: BranchUpdate, user: User, db: Session) -> RatedBranchResponse:
    branch = db.get(LaundryBranch, branch_id)
    if branch is None:
        raise NotFoundError("Branch not found")
    if not can_manage_branch(user, branch):
        raise PermissionDeniedError("You cannot manage this branch")

    for field, value in changes.model_dump(exclude_unset=True).items():
        if value is None and field not in ("latitude", "longitude"):
            continue  # required columns are never cleared
        setattr(branch, field, value)
    db.commit()
    return get_branch(branch_id, db)
