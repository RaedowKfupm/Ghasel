from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.exceptions import AuthenticationError, ConflictError, PermissionDeniedError
from app.core.security import authenticate_user, create_access_token, hash_password
from app.models.Users import User
from app.schemas.auth import ResponseUser, UserLogin, UserRegister

PUBLIC_ROLES = frozenset({UserRole.CUSTOMER, UserRole.LAUNDRY})


def _session_for(user: User) -> ResponseUser:
    return ResponseUser(
        access_token=create_access_token({"sub": str(user.id)}),
        token_type="Bearer",
        name=user.name,
        email=user.email,
        role=user.role,
    )


def register_user_service(info: UserRegister, db: Session) -> ResponseUser:
    if info.role not in PUBLIC_ROLES:
        raise PermissionDeniedError("Admin and manager accounts cannot be registered publicly")
    if db.scalar(select(User.id).where(User.email == info.email)) is not None:
        raise ConflictError("Email already registered")

    user = User(
        name=info.name,
        email=info.email,
        password_hash=hash_password(info.password),
        role=info.role,
    )
    db.add(user)
    db.commit()
    return _session_for(user)


def login_user_service(info: UserLogin, db: Session) -> ResponseUser:
    user = authenticate_user(info.email, info.password, db)
    if user is None:
        raise AuthenticationError("Invalid email or password")
    return _session_for(user)
