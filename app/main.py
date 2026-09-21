from fastapi import FastAPI
from app.routes import auth, laundry, orders, users

app = FastAPI(
    title="Ghasel API",
    version="1.0.0"
)
app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(users.router)
app.include_router(laundry.router)

