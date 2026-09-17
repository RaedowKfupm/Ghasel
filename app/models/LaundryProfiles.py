from sqlalchemy import DateTime
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class LaundryProfile(Base):
    __tablename__ = 'Laundry'
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    number_of_orders = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=False)

class LaundryBranch(Base):
    __tablename__ = 'Branches'
    id = Column(Integer, primary_key=True, index=True)
    laundry_id = Column(Integer, ForeignKey('Laundry.id'), nullable=False)
    branch_name = Column(String)
    branch_address = Column(String, nullable=False)
    manager_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    phone = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    

    