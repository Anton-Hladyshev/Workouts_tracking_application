from fastapi import FastAPI
from app.routers.auth import router as auth_router
from app.routers.client import router as client_router
from app.routers.coach import router as coach_router
from app.routers.registration import router as registration_router
from app.exceptions_handlers import setup_exception_handlers

app = FastAPI()

app.include_router(registration_router)
app.include_router(auth_router)
app.include_router(client_router)
app.include_router(coach_router)

setup_exception_handlers(app)