from datetime import datetime, timedelta, timezone, date as date_, time as time_
from typing import Annotated, List

from fastapi import Body, Depends, FastAPI, HTTPException, status, Query, Request
from fastapi.responses import JSONResponse
from models.enums import Auditory, Discipline, Gender, Role, TrainingType
from schemas.schemas import SubscriptionDTO, TrainingOnInputDTO, TrainingAddDTO, TrainingDTO, TrainingOnInputToUpdateDTO, TrainingSearchDTO, UserDTO
from schemas.exceptions import InvalidPermissionsError, TimeValidationError, BusinessRulesValidationError
from db.database import ClientService, CoachService, async_session_factory
from dotenv import load_dotenv
from app.routers.auth import get_current_user, router as auth_router
from app.routers.client import router as client_router
from app.routers.coach import router as coach_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(client_router)
app.include_router(coach_router)

"""Exceptions"""
@app.exception_handler(TimeValidationError)
async def time_validation_exception_handler(request: Request, exc: TimeValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.message
        }
    )

@app.exception_handler(InvalidPermissionsError)
async def permissions_validation_exception_handler(request: Request, exc: TimeValidationError):
    return JSONResponse(
        status_code=403,
        content={
            "detail": exc.message
        }
    )


@app.exception_handler(BusinessRulesValidationError)
async def business_logic_validation_exception_handler(request: Request, exc: BusinessRulesValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.message
        }
    )