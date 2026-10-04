from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.security import decode_access_token, oauth2_scheme
from app.db.session import get_db
from app.models.LaundryProfiles import LaundryProfile
from app.models.Users import User

Token = Annotated[str, Depends(oauth2_scheme)]
Database = Annotated[Session, Depends(get_db)]


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(token)
    except (jwt.PyJWTError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


current_user = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: UserRole) -> Callable:
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return role_checker


def get_owned_laundry(
    laundry_id: int,
    user: User = Depends(require_roles(UserRole.LAUNDRY)),
    db: Session = Depends(get_db),
) -> LaundryProfile:
    laundry = (
        db.query(LaundryProfile)
        .filter(
            LaundryProfile.id == laundry_id,
            LaundryProfile.id == user.laundry_id,
        )
        .first()
    )
    if laundry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Laundry not found",
        )
    return laundry


OwnedLaundry = Annotated[LaundryProfile, Depends(get_owned_laundry)]