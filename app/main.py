from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401  (register every model before the first query)
from app.core.exceptions import register_exception_handlers
from app.routes import auth, branches, laundry, orders, reviews, users

app = FastAPI(title="Ghasel API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)

for module in (auth, users, laundry, branches, orders, reviews):
    app.include_router(module.router)
