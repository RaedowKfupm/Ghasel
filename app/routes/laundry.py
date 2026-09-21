from fastapi import APIRouter

router = APIRouter(
    prefix="/laundries",
    tags=["Laundries"]
)
@router.post("/")
async def create_laundry():
    pass
@router.post("/{laundry_id}/branches")
async def create_laundry_branch(laundry_id: int):
    pass

@router.get("/{laundry_id}")
async def get_laundry(laundry_id: int):
    pass

@router.get("/{laundry_id}/branches")
async def get_laundry_branches (laundry_id: int):
    pass


@router.get("/?nearby=True")
async def get_nearby_laundries():
    pass

