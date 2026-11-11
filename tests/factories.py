"""Small helpers that insert realistic rows directly, bypassing the API."""

from itertools import count

from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.security import create_access_token, hash_password
from app.models.LaundryProfiles import LaundryBranch, LaundryProfile
from app.models.Users import User

PASSWORD = "correct-horse-battery"
_sequence = count(1)


def auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user.id)})}"}


def make_user(db: Session, role: UserRole = UserRole.CUSTOMER, **fields) -> User:
    n = next(_sequence)
    user = User(
        name=fields.pop("name", f"{role.value.title()} {n}"),
        email=fields.pop("email", f"{role.value}{n}@example.com"),
        password_hash=hash_password(PASSWORD),
        role=role,
        **fields,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_laundry(db: Session, owner: User | None = None, name: str = "Fresh Fold") -> LaundryProfile:
    laundry = LaundryProfile(name=name)
    db.add(laundry)
    db.flush()
    if owner is not None:
        owner.laundry_id = laundry.id
    db.commit()
    db.refresh(laundry)
    return laundry


def make_branch(db: Session, laundry: LaundryProfile | None = None, **fields) -> LaundryBranch:
    laundry = laundry or make_laundry(db)
    n = next(_sequence)
    branch = LaundryBranch(
        laundry_id=laundry.id,
        branch_name=fields.pop("branch_name", f"Branch {n}"),
        branch_address=fields.pop("branch_address", f"{n} King Fahd Road"),
        phone=fields.pop("phone", f"05000000{n:02d}"),
        **fields,
    )
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


def make_manager(db: Session, branch: LaundryBranch) -> User:
    return make_user(db, UserRole.MANAGER, laundry_branch_id=branch.id)
