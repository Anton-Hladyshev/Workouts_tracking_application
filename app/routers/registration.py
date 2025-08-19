from fastapi import APIRouter, status
from schemas.schemas import UserAddDTO, UserRegisterDTO
from db.database import RegistrationService


router = APIRouter(
    prefix="/registration",
    tags=["Registration"]
)

@router.post("/register", response_model=UserAddDTO, status_code=status.HTTP_201_CREATED)
async def register_new_user(
    user_data: UserRegisterDTO
):
    service = RegistrationService(user_data)
    new_user = await service.add_new_user()

    return new_user