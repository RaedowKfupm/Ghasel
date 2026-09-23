from fastapi import APIRouter
from app.schemas.auth import ResponseUser, UserRegister, UserLogin, ResponseUser
from fastapi import Depends
from app.db.session import Session, get_db
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register", status_code=201, response_model=ResponseUser)
async def register_user(info: UserRegister, db: Session =Depends(get_db)):
    return register_user(info, db)



@router.post("/login", response_model=ResponseUser, status_code=200)
async def login_user( info: UserLogin, db: Session =Depends(get_db)):
    return login_user(info, db)
    
