from httpx import AsyncClient
import pytest

@pytest.mark.asyncio
async def test_auth_user_bad_password(client: AsyncClient):
    response = await client.post(
        "/auth/token",
        data={
            "username": "alice.johnson@example.com",
            "password": "whvgwhwhwh"
        }
    )
    assert response.status_code == 401
    assert "access_token" not in response.json()

@pytest.mark.asyncio
async def test_auth_user_success(client: AsyncClient):
    response = await client.post(
        "/auth/token",
        data={
            "username": "alice.johnson@example.com",
            "password": "SimplePass123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_auth_user_bad_email(client: AsyncClient):
    response = await client.post(
        "/auth/token",
        data={
            "username": "cgwvghwhjvwghfhwjdw",
            "password": "SimplePass123"
        }
    )
    assert response.status_code == 422
    assert "access_token" not in response.json()

@pytest.mark.asyncio
async def test_auth_user_empty_data(client: AsyncClient):
    response = await client.post(
        "/auth/token",
        data={
            "username": "",
            "password": ""
        }
    )
    assert response.status_code == 422
    assert "access_token" not in response.json()

@pytest.mark.asyncio
async def test_auth_user_no_data(client: AsyncClient):
    response = await client.post(
        "/auth/token",
        data={}
    )
    assert response.status_code == 422
    assert "access_token" not in response.json()