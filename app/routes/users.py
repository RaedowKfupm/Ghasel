from fastapi import APIRouter

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get("/")
async def get_users():
    pass

@router.get("/{user_id}")
async def get_user(user_id: int):
    pass