from fastapi import APIRouter

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)