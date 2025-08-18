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

app = FastAPI()

app.include_router(auth_router)
app.include_router(client_router)

def get_curent_coach(user: UserDTO = Depends(get_current_user)) -> UserDTO:
    if user.role != Role.COACH:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. You are not a coach.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


@app.get("/users/me/coach", response_model=UserDTO)
async def read_current_coach(
    current_user: Annotated[UserDTO, Depends(get_curent_coach)]
) -> UserDTO:
    service = CoachService(current_user)
    return service.get_user()

@app.get("/users/me/coach/training/get", status_code=status.HTTP_200_OK, response_model=List[TrainingDTO])
async def get_trainings_by_parameters(
    current_user: Annotated[UserDTO, Depends(get_curent_coach)],
    title: str | None = None,
    description: str | None = None,
    date_start_search: str | None = date_(2025, 1, 1),
    date_end_search: str | None = date_(2025, 12, 31),
    time_start_search: str | None = time_(0, 0, 0),
    time_end_search: str | None = time_(23, 59, 59),
    type_: TrainingType | None = None,
    individual_for_id: int | None = None,
    discipline: Discipline | None = None,
    target_auditory: Auditory | None = None,
    target_gender: Gender | None = None
) -> List[TrainingDTO]:
    service = CoachService(current_user)
    training_dto = TrainingSearchDTO(
        title=title,
        description=description,
        date_start_search=date_start_search,
        date_end_search=date_end_search,
        time_start_search=time_start_search,
        time_end_search=time_end_search,
        type=type_,
        individual_for_id=individual_for_id,
        discipline=discipline,
        target_gender=target_gender,
        target_auditory=target_auditory
    )
    
    result = await service.get_trainings(training_dto)
    return result


@app.post("/users/me/coach/training/create", status_code=status.HTTP_201_CREATED)
async def create_training(
    current_user: Annotated[UserDTO, Depends(get_curent_coach)],
    training_data: TrainingOnInputDTO = Body()
    ):
    service = CoachService(current_user)
    training_dict = training_data.model_dump()
    date_time_start = datetime.strptime(f"{training_dict["date"]} {training_dict["time_start"]}", "%Y-%m-%d %H:%M:%S")
    date_time_end = datetime.strptime(f"{training_dict["date"]} {training_dict["time_end"]}", "%Y-%m-%d %H:%M:%S")

    training_dto = TrainingAddDTO(
        title=training_dict.get("title"),
        description=training_dict.get("title"),
        time_start=date_time_start,
        time_end=date_time_end,
        type=TrainingType(training_dict.get("type")),
        discipline=Discipline(training_dict.get("discipline")),
        coach_id=current_user.id,
        individual_for_id=training_dict.get("individual_for_id"),
        target_auditory=training_dict.get("target_auditory"),
        target_gender=training_dict.get("target_gender")
    )
    new_training = await service.create_training(training_data=training_dto)
    return {
        "code": 201,
        "status": "created",
        "detail": {
            "created_at": str(datetime.now()),
            "content": new_training
        }
    }

@app.delete("/users/me/coach/training/delete/{training_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_training(
    training_id: int,
    current_user: Annotated[UserDTO, Depends(get_curent_coach)]) -> None:
    try:
        service = CoachService(current_user)
        await service.delete_training(
            training_id=training_id
        )
        return {
            "code": 204,
            "status": "deleted",
            "id": training_id
        }
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is not any training with this ID.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
@app.patch("/users/me/coach/training/update/{training_id}", status_code=status.HTTP_200_OK)
async def update_training(
    current_user: Annotated[UserDTO, Depends(get_curent_coach)],
    training_id: int,
    update_data: TrainingOnInputToUpdateDTO = Body()
        ):
    service = CoachService(current_user)

    updated_training = await service.update_training(
        training_id=training_id,
        **update_data.model_dump(exclude_unset=True)
    )

    return {
        "code": 200,
        "status": "updated",
        "detail": {
            "updated_at": str(datetime.now()),
            "content": updated_training
        }
    }

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