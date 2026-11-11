from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.core.enums import LaundryRequestStatus, UserRole
from app.core.security import hash_password
from app.models.LaundryProfiles import (
    LaundryBranch,
    LaundryProfile,
    LaundryRequest,
)
from app.models.Users import User
from app.schemas.laundry import BranchCreate, LaundryCreate, ManagerCreate, Pagination


def create_laundry_request(
    request_data: LaundryCreate,
    owner: User,
    db: Session,
) -> LaundryRequest:
    existing_request = (
        db.query(LaundryRequest)
        .filter(
            LaundryRequest.owner_id == owner.id,
            LaundryRequest.status == LaundryRequestStatus.PENDING,
        )
        .first()
    )
    if existing_request is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending laundry request",
        )

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
    return (
        db.query(LaundryRequest)
        .order_by(LaundryRequest.created_at.desc())
        .offset((pagination.page - 1) * pagination.limit)
        .limit(pagination.limit)
        .all()
    )


def get_laundry(laundry_id: int, db: Session) -> LaundryProfile:
    laundry = db.get(LaundryProfile, laundry_id)
    if laundry is None:
        raise HTTPException(status_code=404, detail="Laundry not found")
    return laundry


def list_laundry_branches(
    laundry_id: int,
    pagination: Pagination,
    db: Session,
) -> list[LaundryBranch]:
    laundry_exists = db.query(LaundryProfile.id).filter(LaundryProfile.id == laundry_id).first()
    if laundry_exists is None:
        raise HTTPException(status_code=404, detail="Laundry not found")

    return (
        db.query(LaundryBranch)
        .options(selectinload(LaundryBranch.operators))
        .filter(LaundryBranch.laundry_id == laundry_id)
        .order_by(LaundryBranch.id)
        .offset((pagination.page - 1) * pagination.limit)
        .limit(pagination.limit)
        .all()
    )


def approve_laundry_request(request_id: int, db: Session) -> LaundryProfile:
    laundry_request = (
        db.query(LaundryRequest)
        .filter(LaundryRequest.id == request_id)
        .with_for_update()
        .first()
    )
    if laundry_request is None:
        raise HTTPException(status_code=404, detail="Laundry request not found")
    if laundry_request.status != LaundryRequestStatus.PENDING:
        raise HTTPException(status_code=409, detail="Laundry request has already been reviewed")

    owner = db.query(User).filter(User.id == laundry_request.owner_id).first()
    if owner is None or owner.laundry_id is not None:
        raise HTTPException(status_code=409, detail="Owner already has a laundry company")

    laundry = LaundryProfile(name=laundry_request.company_name)
    laundry_request.status = LaundryRequestStatus.APPROVED
    laundry_request.decided_at = func.now()
    db.add(laundry)
    db.flush()
    owner.laundry_id = laundry.id
    laundry_request.laundry_id = laundry.id
    db.commit()
    db.refresh(laundry)
    return laundry


def create_laundry_branch(
    branch_data: BranchCreate,
    laundry: LaundryProfile,
    db: Session,
) -> LaundryBranch:
    branch = LaundryBranch(
        laundry_id=laundry.id,
        branch_name=branch_data.branch_name,
        branch_address=branch_data.branch_address,
        phone=branch_data.phone,
    )
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


def create_laundry_manager(
    laundry: LaundryProfile,
    manager_data: ManagerCreate,
    db: Session,
) -> User:
    branch = (
        db.query(LaundryBranch)
        .filter(
            LaundryBranch.id == manager_data.branch_id,
            LaundryBranch.laundry_id == laundry.id,
        )
        .first()
    )
    if branch is None:
        raise HTTPException(status_code=404, detail="Branch not found for this laundry")

    existing_user = db.query(User).filter(User.email == manager_data.email).first()
    if existing_user is not None:
        raise HTTPException(status_code=409, detail="Email is already registered")

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
