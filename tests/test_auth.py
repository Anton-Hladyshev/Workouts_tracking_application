from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_auth_user():
    response = client.post(
        "/auth/token",
        data={
            "username": "alice.johnson@example.com",
            "password": "SimplePass123"
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.json()