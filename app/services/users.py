from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.enums import UserRole
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.CustomerProfiles import CustomerProfile
from app.models.Users import User
from app.schemas.pagination import Pagination
from app.schemas.users import UpdateUser

REQUIRED_USER_FIELDS = ("name", "email")
CUSTOMER_PROFILE_FIELDS = ("phone", "address")


def _user_profile_data(user: User) -> dict:
    profile = user.customer_profile
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "phone": profile.phone if profile is not None else None,
        "address": profile.address if profile is not None else None,
        "laundry_id": user.laundry_id,
        "laundry_branch_id": user.laundry_branch_id,
    }


def list_users(pagination: Pagination, db: Session) -> list[dict]:
    users = db.scalars(
        select(User)
        .options(joinedload(User.customer_profile))
        .order_by(User.id)
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    return [_user_profile_data(user) for user in users]


def get_user(user_id: int, db: Session) -> dict:
    user = db.get(User, user_id, options=[joinedload(User.customer_profile)])
    if user is None:
        raise NotFoundError("User not found")
    return _user_profile_data(user)


def get_current_user_profile(user: User) -> dict:
    return _user_profile_data(user)


def _apply_customer_profile_changes(user: User, changes: dict, db: Session) -> None:
    if user.role != UserRole.CUSTOMER:
        raise ValidationError("Phone and address can only be set on customer profiles")

    profile = user.customer_profile
    if profile is None:
        if not changes.get("phone"):
            raise ValidationError("A phone number is required to create a customer profile")
        profile = CustomerProfile(id=user.id, phone=changes["phone"])
        db.add(profile)
    elif "phone" in changes and not changes["phone"]:
        raise ValidationError("Phone cannot be empty")

    for field, value in changes.items():
        setattr(profile, field, value)


def update_current_user_profile(user: User, user_data: UpdateUser, db: Session) -> dict:
    changes = user_data.model_dump(exclude_unset=True)

    for field in REQUIRED_USER_FIELDS:
        if field in changes and not changes[field]:
            raise ValidationError(f"{field} cannot be empty")

    profile_changes = {k: changes[k] for k in CUSTOMER_PROFILE_FIELDS if k in changes}
    if profile_changes:
        _apply_customer_profile_changes(user, profile_changes, db)

    for field in REQUIRED_USER_FIELDS:
        if field in changes:
            setattr(user, field, changes[field])

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise ConflictError("Email is already registered") from error
    db.refresh(user)
    return _user_profile_data(user)
