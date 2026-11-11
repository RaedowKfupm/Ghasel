from enum import Enum


class UserRole(str, Enum):
    CUSTOMER = "customer"
    LAUNDRY = "laundry"
    ADMIN = "admin"
    MANAGER = "manager"


class OrderStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LaundryRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
