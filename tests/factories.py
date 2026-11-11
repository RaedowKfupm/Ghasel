"""Small helpers that insert realistic rows directly, bypassing the API."""

from itertools import count

from sqlalchemy.orm import Session

from app.core.enums import OrderStatus, UserRole
from app.core.security import create_access_token, hash_password
from app.models.LaundryProfiles import LaundryBranch, LaundryProfile
from app.models.Orders import Orders
from app.models.Users import User

PASSWORD = "correct-horse-battery"
# Default location used by factories (Dhahran); tests needing distances pass their own points.
ORIGIN = (26.3070, 50.1460)
KM_PER_DEGREE_LATITUDE = 110.8  # close enough near latitude 26 for offsets of a few kilometres
_sequence = count(1)


def north_of(origin: tuple[float, float], km: float) -> tuple[float, float]:
    """A point roughly ``km`` kilometres due north of ``origin``."""
    return origin[0] + km / KM_PER_DEGREE_LATITUDE, origin[1]


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


def make_branch(
    db: Session,
    laundry: LaundryProfile | None = None,
    location: tuple[float, float] | None = ORIGIN,
    **fields,
) -> LaundryBranch:
    laundry = laundry or make_laundry(db)
    n = next(_sequence)
    latitude, longitude = location if location else (None, None)
    branch = LaundryBranch(
        laundry_id=laundry.id,
        latitude=latitude,
        longitude=longitude,
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


def make_order(
    db: Session,
    customer: User,
    branch: LaundryBranch | None = None,
    status: OrderStatus = OrderStatus.PENDING,
    details: str = "3 shirts, wash and iron",
    pickup: tuple[float, float] = ORIGIN,
) -> Orders:
    order = Orders(
        customer_id=customer.id,
        branch_id=branch.id if branch else None,
        status=status,
        details=details,
        pickup_address="Building 57, KFUPM",
        pickup_latitude=pickup[0],
        pickup_longitude=pickup[1],
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
