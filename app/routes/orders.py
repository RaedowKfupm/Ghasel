from fastapi import APIRouter

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)

@router.post("/")
async def create_order():
    pass

@router.get("/{order_id}")
async def get_order(order_id: int):
    pass

@router.get("/")
async def list_orders():
    pass

@router.patch("/{order_id}/status")
async def update_order_status(order_id: int):
    pass
