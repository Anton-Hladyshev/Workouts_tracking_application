from datetime import datetime
from typing import Annotated, List
from fastapi import APIRouter, Body, Depends, HTTPException, status
from db.database import CoachService
from models.enums import Auditory, Discipline, Gender, Role, TrainingType
from schemas.schemas import TrainingAddDTO, TrainingDTO, TrainingOnInputDTO, TrainingOnInputToUpdateDTO, TrainingSearchDTO, UserDTO
from app.routers.auth import get_current_user
from datetime import datetime, date as date_, time as time_

router = APIRouter(
    prefix="/coach",
    tags=["Coach"]
)

def get_curent_coach(user: UserDTO = Depends(get_current_user)) -> UserDTO:
    if user.role != Role.COACH:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. You are not a coach.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user

@router.get("/users/me/coach", response_model=UserDTO)
async def read_current_coach(
    current_user: Annotated[UserDTO, Depends(get_curent_coach)]
) -> UserDTO:
    service = CoachService(current_user)
    return service.get_user()

@router.get("/users/me/coach/trainings/get", status_code=status.HTTP_200_OK, response_model=List[TrainingDTO])
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

@router.get('/users/me/coach/trainings/get_students_on_training/{training_id}', status_code=status.HTTP_200_OK, response_model=List[UserDTO])
async def get_students_on_training(
    training_id: int,
    current_user: Annotated[UserDTO, Depends(get_curent_coach)]
) -> List[UserDTO]:
    service = CoachService(current_user)
    try:
        students = await service.get_students_of_training(training_id=training_id)
        if len(students) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There are no students on this training.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return students
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is not any training with this ID.",
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.post("/users/me/coach/trainings/create", status_code=status.HTTP_201_CREATED)
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
        description=training_dict.get("description"),
        time_start=date_time_start,
        time_end=date_time_end,
        type=TrainingType(training_dict.get("type")),
        discipline=Discipline(training_dict.get("discipline")),
        coach_id=current_user.id,
        individual_for_id=training_dict.get("individual_for_id"),
        target_auditory=training_dict.get("target_auditory"),
        target_gender=training_dict.get("target_gender"),
        target_usertype=training_dict.get("target_usertype")
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

@router.delete("/users/me/coach/trainings/delete/{training_id}", status_code=status.HTTP_204_NO_CONTENT)
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
    
@router.patch("/users/me/coach/trainings/update/{training_id}", status_code=status.HTTP_200_OK)
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