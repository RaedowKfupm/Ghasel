from app.models.Users import User
from app.models.CustomerProfiles import CustomerProfile
from app.models.LaundryProfiles import LaundryProfile, LaundryBranch, LaundryRequest
from app.models.Orders import Orders
from app.db.base import Base
from app.db.session import engine

Base.metadata.create_all(bind=engine)
print("Tables created successfully.")