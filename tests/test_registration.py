import logging
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import pytest

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
@pytest.mark.registration_success
async def test_user_registration_success(client: AsyncClient, db_session: AsyncSession, test_user_data):
    test_user_data["password_confirmation"] = test_user_data["password"]
    test_user_data["birth_date"] = "1990-01-01"
    response = await client.post(
        url="/registration/register", 
        json=test_user_data
    )

    logger.debug(f"Received response: status={response.status_code}, body={response.json()}")
    assert response.status_code == 201
    assert response.json()["email"] == test_user_data["email"]
    #user_exists = await ORMBase.user_exists(name=test_user_data["name"], email=test_user_data["email"], session=db_session)
    #assert user_exists

@pytest.mark.asyncio
@pytest.mark.registration_password_missmatch
async def test_user_registration_password_mismatch(client: AsyncClient, db_session: AsyncSession, test_user_data):
    test_user_data["password_confirmation"] = "DifferentPassword123"
    test_user_data["birth_date"] = "1990-01-01"
    response = await client.post(
        url="/registration/register", 
        json=test_user_data
    )

    logger.debug(f"Received response: status={response.status_code}, body={response.json()}")
    assert response.status_code == 400
    #user_exists = await ORMBase.user_exists(name=test_user_data["name"], email=test_user_data["email"], session=db_session)
    #assert not user_exists