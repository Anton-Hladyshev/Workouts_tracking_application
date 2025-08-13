from datetime import datetime, timedelta, timezone
from typing import Annotated, List

import jwt
from fastapi import Depends, FastAPI, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from models.enums import Role
from schemas.schemas import SubscriptionDTO, TrainingDTO, UserDTO
from schemas.exceptions import ForbiddenActionError
from pydantic import BaseModel
from db.database import ORMBase, ClientService, CoachService, async_session_factory
from dotenv import load_dotenv
import os

load_dotenv()

jwt_key = os.getenv("SECRET_KEY")
jwt_expire_delta = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
jwt_alghorithm = os.getenv("ALGHORITHM")

ph = PasswordHasher()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()

class AccessToken(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None


def verify_password(hashed_password: str, plain_password: str) -> bool:
    """Verify if the provided password matches the hashed password."""
    is_correct = True
    try:
        ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        is_correct = False
    return is_correct

def get_password_hash(password: str) -> str:
    """Hash the provided password using Argon2."""
    return ph.hash(password)

async def get_user(username: str) -> UserDTO | None:
    """Retrieve a user by username from the database."""
    async with async_session_factory() as session:
        params = {
            "name": username
        }
        user = await ORMBase.get_user_by(ession=session, **params)
        
        return user
    
async def authenticate_user(username: str, password: str) -> UserDTO | bool:
    """Authenticate a user by verifying the username and password."""
    user = await get_user(username)
    if not user:
        return False
    if not verify_password(user.password, password):
        return False
    return user
    
def create_access_token(
    data: dict, expires_delta: timedelta | None = None
                        ) -> str:
    """Create a JWT access token with an expiration time."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(payload=to_encode, key=jwt_key, algorithm=jwt_alghorithm)
    return encoded_jwt

async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)]
) -> UserDTO:
    """Get the current user from the JWT token."""
    creditials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(token, jwt_key, algorithms=[jwt_alghorithm])
        username = payload.get("sub")
        if username is None:
            raise creditials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise creditials_exception
    user = await get_user(username=token_data.username)
    if not user:
        raise creditials_exception
    return user


@app.post('/token')
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> AccessToken:
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=jwt_expire_delta)
    access_token = create_access_token(
        data={"sub":user.name},
        expires_delta=access_token_expires
    )

    return AccessToken(
        access_token=access_token,
        token_type="bearer"
    )

def get_curent_coach(user: UserDTO = Depends(get_current_user)) -> UserDTO:
    if user.role != Role.COACH:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. You are not a coach.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user

def get_current_client(user: UserDTO = Depends(get_current_user)) -> UserDTO:
    if user.role != Role.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. You are not a coach.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user

@app.get("/users/me", response_model=UserDTO)
async def read_users_me(
    current_user: Annotated[UserDTO, Depends(get_current_user)]
) -> UserDTO:
    return current_user

@app.get("/users/me/coach", response_model=UserDTO)
async def read_current_coach(
    current_user: Annotated[UserDTO, Depends(get_curent_coach)]
) -> UserDTO:
    service = CoachService(current_user)
    return service.get_user()

@app.delete("/users/me/coach/training/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_training(
    training_id: int,
    current_user: Annotated[UserDTO, Depends(get_curent_coach)]) -> None:
    try:
        service = CoachService(current_user)
        await service.delete_training(
            training_id=training_id
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is not any training with this ID.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except ForbiddenActionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"}
        )

@app.get("/users/me/client", response_model=UserDTO)
async def read_current_client(
    current_user: Annotated[UserDTO, Depends(get_current_client)]
) -> UserDTO:
    service = ClientService(current_user)
    return service.get_user()

@app.get("/users/me/client/subscriptions/", response_model=List[TrainingDTO])
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

@app.get("/users/me/client/available_trainings/", response_model=List[TrainingDTO])
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

@app.post("/users/me/client/subscribe/", response_model=SubscriptionDTO)
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
    

#@app.get("/users/me/items/")
#async def read_own_items(
#    current_user: Annotated[UserInDb, Depends(get_current_active_user)]
#) -> dict[str, str]:
#    return {
#        "item": "This is your item",
#        "owner": current_user.username
#    }