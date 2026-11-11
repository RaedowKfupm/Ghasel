"""Request-scoped FastAPI dependencies: database session, authentication and authorization."""

import inspect
from collections.abc import Callable
from typing import Annotated, TypeVar

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.security import decode_access_token, oauth2_scheme
from app.db.session import get_db
from app.models.LaundryProfiles import LaundryProfile
from app.models.Users import User
from app.schemas.pagination import Pagination

Database = Annotated[Session, Depends(get_db)]

QueryModel = TypeVar("QueryModel", bound=BaseModel)


def query_model(model: type[QueryModel]) -> Callable[..., QueryModel]:
    """Read query parameters into ``model``, reporting constraint violations as 422.

    FastAPI 0.103 exposes a model's fields as query parameters when it is used as a
    dependency, but its Field constraints only run when the model is built, where a
    ValidationError would otherwise surface as a 500.
    """

    def dependency(**params) -> QueryModel:
        try:
            return model(**params)
        except ValidationError as error:
            raise RequestValidationError(
                [{**e, "loc": ("query", *e["loc"])} for e in error.errors(include_url=False)]
            ) from error

    dependency.__signature__ = inspect.signature(model)
    return dependency


Page = Annotated[Pagination, Depends(query_model(Pagination))]

_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid authentication credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Database) -> User:
    try:
        user_id = int(decode_access_token(token)["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as error:
        raise _INVALID_CREDENTIALS from error

    user = db.get(User, user_id)
    if user is None:
        raise _INVALID_CREDENTIALS
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: UserRole) -> Callable[..., User]:
    def role_checker(user: CurrentUser) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return role_checker


def get_owned_laundry(
    laundry_id: int,
    owner: Annotated[User, Depends(require_roles(UserRole.LAUNDRY))],
    db: Database,
) -> LaundryProfile:
    """Resolve ``laundry_id`` only if it belongs to the authenticated laundry owner."""
    if owner.laundry_id != laundry_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Laundry not found")
    return db.get(LaundryProfile, laundry_id)


OwnedLaundry = Annotated[LaundryProfile, Depends(get_owned_laundry)]
