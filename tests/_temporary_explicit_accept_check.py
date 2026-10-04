from datetime import datetime
from pathlib import Path
import sys

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.models
from app.core.enums import UserRole
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.LaundryProfiles import LaundryBranch, LaundryProfile
from app.models.Users import User

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
TestSession = sessionmaker(bind=engine)
db = TestSession()
db.add_all([
    User(id=1, name="Customer", email="customer@example.com", password_hash="x", role=UserRole.CUSTOMER),
    User(id=2, name="Operator One", email="one@example.com", password_hash="x", role=UserRole.MANAGER, laundry_branch_id=1),
    User(id=3, name="Operator Two", email="two@example.com", password_hash="x", role=UserRole.MANAGER, laundry_branch_id=2),
])
db.add(LaundryProfile(id=1, created_at=datetime.utcnow()))
db.add_all([
    LaundryBranch(id=1, laundry_id=1, branch_name="One", branch_address="A", phone="1", created_at=datetime.utcnow()),
    LaundryBranch(id=2, laundry_id=1, branch_name="Two", branch_address="B", phone="2", created_at=datetime.utcnow()),
])
db.commit()
db.close()
app.dependency_overrides[get_db] = lambda: TestSession()
client = TestClient(app)
token = lambda user_id: create_access_token({"sub": str(user_id)})
headers = lambda user_id: {"Authorization": f"Bearer {token(user_id)}"}

open_order = client.post("/orders/", headers=headers(1), json={"details": "Open"}).json()
direct_order = client.post("/orders/", headers=headers(1), json={"branch_id": 1, "details": "Direct"}).json()
print("open claim winner/loser:", client.post(f"/orders/{open_order['id']}/accept", headers=headers(2)).status_code, client.post(f"/orders/{open_order['id']}/accept", headers=headers(3)).status_code)
print("direct accept owner/other branch:", client.post(f"/orders/{direct_order['id']}/accept", headers=headers(2)).status_code, client.post(f"/orders/{direct_order['id']}/accept", headers=headers(3)).status_code)
print("later status updates:", client.patch(f"/orders/{open_order['id']}/status", headers=headers(2), json={"status": "delivering"}).status_code, client.patch(f"/orders/{open_order['id']}/status", headers=headers(2), json={"status": "completed"}).status_code)
print("accepted via PATCH schema:", client.patch(f"/orders/{direct_order['id']}/status", headers=headers(2), json={"status": "accepted"}).status_code)
app.dependency_overrides.clear()
