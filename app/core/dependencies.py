from typing import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.Users import User
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

Token = Annotated[str, Depends(oauth2_scheme)]
Database = Annotated[Session, Depends(get_db)]

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    user_id = decode_access_token(token)

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return user

current_user = Annotated[User, Depends(get_current_user)]