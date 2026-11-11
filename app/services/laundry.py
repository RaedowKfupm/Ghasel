from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import LaundryRequestStatus, UserRole
from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.LaundryProfiles import LaundryBranch, LaundryProfile, LaundryRequest
from app.models.Users import User
from app.schemas.branch import BranchCreate
from app.schemas.laundry import LaundryCreate, ManagerCreate
from app.schemas.pagination import Pagination


def create_laundry_request(request_data: LaundryCreate, owner: User, db: Session) -> LaundryRequest:
    if owner.laundry_id is not None:
        raise ConflictError("You already own an approved laundry company")

    has_pending_request = db.scalar(
        select(LaundryRequest.id).where(
            LaundryRequest.owner_id == owner.id,
            LaundryRequest.status == LaundryRequestStatus.PENDING,
        )
    )
    if has_pending_request is not None:
        raise ConflictError("You already have a pending laundry request")

    laundry_request = LaundryRequest(
        owner_id=owner.id,
        company_name=request_data.company_name,
        status=LaundryRequestStatus.PENDING,
    )
    db.add(laundry_request)
    db.commit()
    db.refresh(laundry_request)
    return laundry_request


def list_laundry_requests(pagination: Pagination, db: Session) -> list[LaundryRequest]:
    return list(
        db.scalars(
            select(LaundryRequest)
            .order_by(LaundryRequest.created_at.desc(), LaundryRequest.id.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
    )


def get_laundry(laundry_id: int, db: Session) -> LaundryProfile:
    laundry = db.get(LaundryProfile, laundry_id)
    if laundry is None:
        raise NotFoundError("Laundry not found")
    return laundry


def list_laundry_branches(laundry_id: int, pagination: Pagination, db: Session) -> list[LaundryBranch]:
    get_laundry(laundry_id, db)
    return list(
        db.scalars(
            select(LaundryBranch)
            .options(selectinload(LaundryBranch.laundry))
            .where(LaundryBranch.laundry_id == laundry_id)
            .order_by(LaundryBranch.id)
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
    )


def approve_laundry_request(request_id: int, db: Session) -> LaundryProfile:
    # Lock the request row so two admins cannot approve it twice.
    laundry_request = db.scalar(
        select(LaundryRequest).where(LaundryRequest.id == request_id).with_for_update()
    )
    if laundry_request is None:
        raise NotFoundError("Laundry request not found")
    if laundry_request.status != LaundryRequestStatus.PENDING:
        raise ConflictError("Laundry request has already been reviewed")

    owner = db.get(User, laundry_request.owner_id)
    if owner is None or owner.laundry_id is not None:
        raise ConflictError("Owner already has a laundry company")

    laundry = LaundryProfile(name=laundry_request.company_name)
    db.add(laundry)
    db.flush()

    laundry_request.status = LaundryRequestStatus.APPROVED
    laundry_request.decided_at = func.now()
    laundry_request.laundry_id = laundry.id
    owner.laundry_id = laundry.id
    db.commit()
    db.refresh(laundry)
    return laundry


def create_laundry_branch(branch_data: BranchCreate, laundry: LaundryProfile, db: Session) -> LaundryBranch:
    branch = LaundryBranch(laundry_id=laundry.id, **branch_data.model_dump())
    db.add(branch)
    db.commit()
    return db.get(LaundryBranch, branch.id, options=[selectinload(LaundryBranch.laundry)])


def create_laundry_manager(laundry: LaundryProfile, manager_data: ManagerCreate, db: Session) -> User:
    branch = db.scalar(
        select(LaundryBranch).where(
            LaundryBranch.id == manager_data.branch_id,
            LaundryBranch.laundry_id == laundry.id,
        )
    )
    if branch is None:
        raise NotFoundError("Branch not found for this laundry")
    if db.scalar(select(User.id).where(User.email == manager_data.email)) is not None:
        raise ConflictError("Email is already registered")

    manager = User(
        name=manager_data.name,
        email=manager_data.email,
        password_hash=hash_password(manager_data.password),
        role=UserRole.MANAGER,
        laundry_branch_id=branch.id,
    )
    db.add(manager)
    db.commit()
    db.refresh(manager)
    return manager


def list_laundry_managers(laundry: LaundryProfile, db: Session) -> list[User]:
    return list(
        db.scalars(
            select(User)
            .join(LaundryBranch, User.laundry_branch_id == LaundryBranch.id)
            .where(LaundryBranch.laundry_id == laundry.id, User.role == UserRole.MANAGER)
            .order_by(User.id)
        )
    )
