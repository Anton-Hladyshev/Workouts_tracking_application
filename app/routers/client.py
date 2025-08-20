from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from db.database import ClientService
from models.enums import Role
from schemas.schemas import SubscriptionDTO, TrainingDTO, UserDTO
from app.routers.auth import get_current_user

router = APIRouter(
    prefix="/client",
    tags=["Client"]
)

def get_current_client(user: UserDTO = Depends(get_current_user)) -> UserDTO:
    if user.role != Role.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. You are not a coach.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user

@router.get("/users/me/client", response_model=UserDTO)
async def read_current_client(
    current_user: Annotated[UserDTO, Depends(get_current_client)]
) -> UserDTO:
    service = ClientService(current_user)
    return service.get_user()

@router.get("/users/me/client/subscriptions/", response_model=List[TrainingDTO])
async def read_own_subscriptions(
    current_user: Annotated[UserDTO, Depends(get_current_client)]
) -> List[TrainingDTO]:
    service = ClientService(current_user)
    subs = await service.show_my_trainings()
    if len(subs) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You have no subscriptions",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return subs

@router.get("/users/me/client/available_trainings/", response_model=List[TrainingDTO])
async def read_own_available_trainings(
    current_user: Annotated[UserDTO, Depends(get_current_client)] ) -> List[TrainingDTO]:
    service = ClientService(current_user)
    available_trainings = await service.show_available_trainings()
    if len(available_trainings) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You have no available trainings",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return available_trainings

@router.post("/users/me/client/available_trainings/subscribe/", response_model=SubscriptionDTO)
async def subscribe_to_trainig(
    training_id: int,
    current_user: Annotated[UserDTO, Depends(get_current_client)]
    ):
    service = ClientService(current_user)
    try:
        new_subscription = await service.subscribe_to_training(
            training_id=training_id
        )

        return new_subscription
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No available trainings with this ID",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
@router.delete("/users/me/client/subscriptions/unsubscribe", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe_from_training(
    training_id: int,
    current_user: Annotated[UserDTO, Depends(get_current_client)]
):
    service = ClientService(current_user)
    try:
        await service.unsubscribe_from_training(training_id=training_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"A subscription on a training with id={training_id} was not found in your subscriptions."
        )