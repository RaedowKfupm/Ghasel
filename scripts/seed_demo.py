"""Create a separate demo database filled with sample marketplace activity.

Everything here is DEMO DATA: invented companies, people and orders, created in
"<dev database>_demo" (never the development database). Orders are driven through
the real service layer (create -> accept -> advance -> review), so their statuses,
history and ratings obey the same rules as production traffic.

    python -m scripts.seed_demo            # rebuild the demo database
    DATABASE_URL=...<dev>_demo uvicorn app.main:app   # then point the API at it

All demo accounts use the password printed at the end.
"""

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.core.config import settings
from app.core.enums import OrderStatus, UserRole
from app.core.exceptions import NotFoundError
from app.core.order_lifecycle import next_progress_status
from app.core.security import hash_password
from app.models.LaundryProfiles import LaundryBranch
from app.models.Users import User
from app.schemas.branch import BranchCreate
from app.schemas.laundry import LaundryCreate
from app.schemas.order import OrderCreate
from app.schemas.review import ReviewCreate
from app.services import laundry as laundry_service
from app.services import orders as order_service
from app.services.reviews import create_review

PASSWORD = "demo-password"
DOMAIN = "ghasel.demo"

COMPANIES = {
    "Crisp & Clean Laundry": [
        ("Al Khobar Corniche", "Prince Turki St, Al Khobar", 26.2950, 50.2160, 10),
        ("Dhahran Campus", "KFUPM Mall, Dhahran", 26.3070, 50.1460, 8),
        ("Dammam Al Faisaliyah", "King Saud St, Dammam", 26.4250, 50.0700, 12),
    ],
    "Bubble House": [
        ("Al Rakah", "Al Rakah Al Shamaliyah, Al Khobar", 26.3480, 50.1950, 10),
        ("Doha District", "Doha Al Janubiyah, Dhahran", 26.2930, 50.1210, 6),
        ("Riyadh Olaya", "Olaya St, Riyadh", None, None, 10),  # no location yet
    ],
}

PENDING_COMPANY = "Fresh Fold Co."

MANAGERS = ["Khalid Al Dosari", "Dana Al Mutairi", "Majed Al Shehri", "Huda Al Ghamdi", "Tariq Al Zahrani", "Rana Al Otaibi"]

CUSTOMERS = ["Sara Al Qahtani", "Omar Haddad", "Lina Nasser", "Faisal Al Harbi", "Noura Al Saud", "Yousef Karim"]

# (customer index, branch name or None for marketplace, details, final status, rating, comment)
ORDERS = [
    (0, None, "2 duvets and 4 pillow covers — wash and fold", OrderStatus.PENDING, None, None),
    (0, "Dhahran Campus", "5 shirts and 3 trousers — wash, iron, hang", OrderStatus.CLEANING, None, None),
    (0, None, "Abaya and 2 thobes — dry clean", OrderStatus.DELIVERING, None, None),
    (0, "Al Khobar Corniche", "Weekly wash: 6 kg mixed", OrderStatus.COMPLETED, 5, "Picked up on time and everything came back crisp."),
    (0, "Al Rakah", "Curtains (2 panels) — gentle wash", OrderStatus.COMPLETED, None, None),
    (1, "Al Khobar Corniche", "Suit and 2 ties — dry clean", OrderStatus.COMPLETED, 4, "Great pressing, delivery was a little late."),
    (2, "Al Khobar Corniche", "Bedding set — wash and fold", OrderStatus.COMPLETED, 5, None),
    (3, "Dhahran Campus", "Lab coats x3 — wash and iron", OrderStatus.COMPLETED, 4, "Reliable, will use again."),
    (4, "Al Rakah", "Kids' school uniforms x5", OrderStatus.COMPLETED, 3, "Clean, but one shirt wasn't ironed."),
    (5, "Doha District", "Sports kit — quick wash", OrderStatus.COMPLETED, 5, "Same-day turnaround!"),
    (1, None, "Winter jackets x2 — dry clean", OrderStatus.ACCEPTED, None, None),
    (2, "Dammam Al Faisaliyah", "Tablecloths for an event x4", OrderStatus.READY, None, None),
    (3, None, "Rug, 2x3 m — deep clean", OrderStatus.PENDING, None, None),
    (4, None, "Shirts x8 — wash and iron", OrderStatus.CANCELLED, None, None),
]

PICKUPS = [
    ("Building 57, KFUPM, Dhahran", 26.3100, 50.1440),
    ("Al Yarmouk, Al Khobar", 26.2900, 50.2050),
    ("Al Shatea, Dammam", 26.4400, 50.1000),
    ("Doha Al Shamaliyah, Dhahran", 26.3000, 50.1300),
]


def user(db: Session, name: str, role: UserRole, **fields) -> User:
    email = f"{name.split()[0].lower()}@{DOMAIN}"
    account = User(name=name, email=email, password_hash=hash_password(PASSWORD), role=role, **fields)
    db.add(account)
    db.flush()
    return account


def accept_as_eligible_branch(db, order_id, candidates, managers):
    """Accept as the first candidate branch the real eligibility rules allow."""
    for branch in candidates:
        manager = db.get(User, managers[branch.id].id)
        try:
            return manager, order_service.accept_order(order_id, manager, db).status
        except NotFoundError:  # pickup outside this branch's service area
            continue
    raise RuntimeError(f"No demo branch can accept order {order_id}")


def seed(db: Session) -> None:
    user(db, "Admin Demo", UserRole.ADMIN)
    branches: dict[str, LaundryBranch] = {}
    managers: dict[int, User] = {}

    # Companies go through the real application -> approval flow.
    owners = [user(db, name, UserRole.LAUNDRY) for name in ("Hassan Owner", "Reem Owner", "Fahad Owner")]
    db.commit()
    for owner, company in zip(owners, [*COMPANIES, PENDING_COMPANY]):
        request = laundry_service.create_laundry_request(LaundryCreate(company_name=company), owner, db)
        if company == PENDING_COMPANY:
            continue  # left for the admin to review in the UI
        laundry = laundry_service.approve_laundry_request(request.id, db)
        for name, address, lat, lng, radius in COMPANIES[company]:
            branch = laundry_service.create_laundry_branch(
                BranchCreate(branch_name=name, branch_address=address, phone=f"+966 13 800 {1000 + len(branches)}",
                             latitude=lat, longitude=lng, service_radius_km=radius),
                laundry,
                db,
            )
            branches[name] = branch
            managers[branch.id] = user(db, MANAGERS[len(managers)], UserRole.MANAGER, laundry_branch_id=branch.id)

    customers = [user(db, name, UserRole.CUSTOMER) for name in CUSTOMERS]
    db.commit()

    for n, (who, branch_name, details, final, rating, comment) in enumerate(ORDERS):
        customer = db.get(User, customers[who].id)
        address, lat, lng = PICKUPS[n % len(PICKUPS)]
        target = branches.get(branch_name)
        order = order_service.create_order(
            OrderCreate(details=details, pickup_address=address, pickup_latitude=lat, pickup_longitude=lng,
                        branch_id=target.id if target else None),
            customer,
            db,
        )
        if final == OrderStatus.PENDING:
            continue
        if final == OrderStatus.CANCELLED:
            order_service.cancel_order(order.id, customer, db)
            continue

        manager, status = accept_as_eligible_branch(db, order.id, [target] if target else branches.values(), managers)
        while status != final:
            status = order_service.advance_order_status(order.id, next_progress_status(status), manager, db).status
        if rating:
            create_review(order.id, ReviewCreate(rating=rating, comment=comment), db.get(User, customer.id), db)


def main() -> None:
    dev_url = make_url(settings.database_url)
    url = dev_url.set(database=f"{dev_url.database}_demo".lower())
    admin = create_engine(dev_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
        connection.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin.dispose()

    engine = create_engine(url)
    config = Config("alembic.ini")
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    with Session(engine) as db:
        seed(db)
    engine.dispose()

    print(f"Demo database ready: {url.database}")
    print(f"Run the API against it with DATABASE_URL={url.render_as_string(hide_password=True)}")
    print(f"Demo accounts (password '{PASSWORD}'):")
    print(f"  customer  sara@{DOMAIN}     manager  dana@{DOMAIN} (Dhahran Campus)")
    print(f"  owner     hassan@{DOMAIN}   admin    admin@{DOMAIN}")


if __name__ == "__main__":
    main()
