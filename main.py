from fastapi import FastAPI
from app.routers import (
    call_manager_routers,
    review_routers,
    call_record_routers,
)
from app.services import signaling
from app.dependencies.db import engine, Base
from fastapi.middleware.cors import CORSMiddleware


Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(review_routers.router)
app.include_router(call_manager_routers.router)
app.include_router(signaling.router)
# app.include_router(call_record_routers.router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
