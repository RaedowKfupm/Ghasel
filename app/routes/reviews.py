from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import Database, Page, require_roles
from app.core.enums import UserRole
from app.models.Users import User
from app.schemas.review import ReviewCreate, ReviewResponse
from app.services import reviews as review_service

router = APIRouter(tags=["Reviews"])

Customer = Annotated[User, Depends(require_roles(UserRole.CUSTOMER))]


@router.post("/orders/{order_id}/review", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def review_order(order_id: int, review_data: ReviewCreate, customer: Customer, db: Database):
    return review_service.create_review(order_id, review_data, customer, db)


@router.get("/branches/{branch_id}/reviews", response_model=list[ReviewResponse])
def list_branch_reviews(branch_id: int, pagination: Page, db: Database):
    return review_service.list_branch_reviews(branch_id, pagination, db)
