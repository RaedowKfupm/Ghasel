from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.enums import UserRole
from app.models.CustomerProfiles import CustomerProfile
from app.models.Users import User
from app.schemas.laundry import Pagination
from app.schemas.users import UpdateUser


def _user_profile_data(user: User) -> dict:
    customer_profile = user.customer_profile
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "phone": customer_profile.phone if customer_profile is not None else None,
        "address": customer_profile.address if customer_profile is not None else None,
        "laundry_id": user.laundry_id,
        "laundry_branch_id": user.laundry_branch_id,
    }


def list_users(pagination: Pagination, db: Session) -> list[dict]:
    users = (
        db.query(User)
        .options(joinedload(User.customer_profile))
        .order_by(User.id)
        .offset((pagination.page - 1) * pagination.limit)
        .limit(pagination.limit)
        .all()
    )
    return [_user_profile_data(user) for user in users]


def get_user(user_id: int, db: Session) -> dict:
    user = (
        db.query(User)
        .options(joinedload(User.customer_profile))
        .filter(User.id == user_id)
        .first()
    )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_profile_data(user)


def get_current_user_profile(user: User) -> dict:
    return _user_profile_data(user)


def update_current_user_profile(user: User, user_data: UpdateUser, db: Session) -> None:
    changes = user_data.model_dump(exclude_unset=True)
    if not changes:
        return

    for required_value in ("name", "email"):
        if required_value in changes and changes[required_value] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{required_value} cannot be null",
            )

    profile_changes = {key: changes[key] for key in ("phone", "address") if key in changes}
    customer_profile = None
    if profile_changes:
        if user.role != UserRole.CUSTOMER:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Phone and address updates are currently supported for customer profiles only",
            )
        customer_profile = user.customer_profile
        if customer_profile is None:
            phone = profile_changes.get("phone")
            if not phone:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="A phone number is required to create a customer profile",
                )
            customer_profile = CustomerProfile(id=user.id, phone=phone)
            db.add(customer_profile)
        elif "phone" in profile_changes and profile_changes["phone"] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Phone cannot be null",
            )

        for field, value in profile_changes.items():
            setattr(customer_profile, field, value)

    for field in ("name", "email"):
        if field in changes:
            setattr(user, field, changes[field])

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from error
