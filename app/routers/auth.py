from datetime import datetime, timedelta, timezone
import os
from typing import Annotated
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, HTTPException, Body, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from pydantic import ValidationError
from db.database import ORMBase, async_session_factory
from dotenv import load_dotenv
from schemas.schemas import AccessToken, TokenData, UserDTO, UserLoginDTO

load_dotenv()

jwt_key = os.getenv("SECRET_KEY")
jwt_expire_delta = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
jwt_alghorithm = os.getenv("ALGHORITHM")

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

ph = PasswordHasher()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

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

async def get_user(identifier: str) -> UserDTO | None:
    """Retrieve a user by identifier from the database."""
    async with async_session_factory() as session:
        params = {
            "email": identifier
        }
        user = await ORMBase.get_user_by(session=session, **params)
        
        return user
    
async def authenticate_user(login_form: UserLoginDTO) -> UserDTO | bool:
    """Authenticate a user by verifying the identifier and password."""
    user = await get_user(login_form.email)
    if not user:
        return False
    if not verify_password(user.password, login_form.password):
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
        request: Request,
        token: Annotated[str, Depends(oauth2_scheme)]
) -> UserDTO:
    """Get the current user from the JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    if token is None:
        token = request.cookies.get("access_token")

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, jwt_key, algorithms=[jwt_alghorithm])
        identifier = payload.get("sub")
        if identifier is None:
            raise credentials_exception
        
        token_data = TokenData(identifier=identifier)
    except jwt.InvalidTokenError:
        raise credentials_exception
    user = await get_user(identifier=token_data.identifier)
    if not user:
        raise credentials_exception
    return user


@router.post('/token')
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> AccessToken:
    
    try:
        login_form = UserLoginDTO(
            email=form_data.username,
            password=form_data.password
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.errors()
        )
    
    user = await authenticate_user(login_form=login_form)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect identifier or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=jwt_expire_delta)
    access_token = create_access_token(
        data={"sub":user.email},
        expires_delta=access_token_expires
    )

    return AccessToken(
        access_token=access_token,
        token_type="bearer"
    )

@router.post("/login-cookie", status_code=status.HTTP_204_NO_CONTENT)
async def login_with_cookie(
    response: Response,
    form_data: UserLoginDTO = Body()
) -> None:
    user = await authenticate_user(login_form=form_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect identifier or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=jwt_expire_delta)
    access_token = create_access_token(
        data={"sub":user.name},
        expires_delta=access_token_expires
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=access_token_expires * 60,
        secure=True,
        path="/",
        samesite="lax",
        httponly=True
    )

    return 

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie(key="access_token", path="/")
    return 

@router.get("/users/me", response_model=UserDTO)
async def read_users_me(
    current_user: Annotated[UserDTO, Depends(get_current_user)]
) -> UserDTO:
    return current_user