import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from supabase_auth.errors import AuthApiError
from supabase_auth.types import User, UserResponse

from app.auth.dependencies import verify_access_token
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_me_without_authorization_returns_401(client: TestClient):
    response = client.get("/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authorization credentials"


def test_me_with_invalid_bearer_scheme_returns_401(client: TestClient):
    response = client.get("/me", headers={"Authorization": "Token abc"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authorization credentials"


def test_me_with_invalid_token_returns_401(client: TestClient):
    with patch(
        "app.auth.dependencies.create_user_client",
        new_callable=AsyncMock,
    ) as mock_create:
        mock_client = AsyncMock()
        mock_client.auth.get_user.side_effect = AuthApiError("Invalid JWT", 403, None)
        mock_create.return_value = mock_client

        response = client.get("/me", headers={"Authorization": "Bearer bad-token"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"
    mock_client.auth.get_user.assert_awaited_once_with(jwt="bad-token")


def test_me_with_valid_token_returns_user(client: TestClient):
    user_id = uuid.uuid4()
    with patch(
        "app.auth.dependencies.create_user_client",
        new_callable=AsyncMock,
    ) as mock_create:
        mock_client = AsyncMock()
        mock_client.auth.get_user.return_value = UserResponse(
            user=User(
                id=str(user_id),
                app_metadata={},
                user_metadata={},
                aud="authenticated",
                email="analyst@driftwood.test",
                created_at="2026-01-01T00:00:00Z",
            )
        )
        mock_create.return_value = mock_client

        response = client.get("/me", headers={"Authorization": "Bearer good-token"})

    assert response.status_code == 200
    assert response.json() == {
        "id": str(user_id),
        "email": "analyst@driftwood.test",
    }


def test_verify_access_token_rejects_user_without_email():
    with patch(
        "app.auth.dependencies.create_user_client",
        new_callable=AsyncMock,
    ) as mock_create:
        mock_client = AsyncMock()
        mock_client.auth.get_user.return_value = UserResponse(
            user=User(
                id=str(uuid.uuid4()),
                app_metadata={},
                user_metadata={},
                aud="authenticated",
                email=None,
                created_at="2026-01-01T00:00:00Z",
            )
        )
        mock_create.return_value = mock_client

        with pytest.raises(HTTPException) as exc_info:
            import asyncio

            asyncio.run(verify_access_token("token"))

    assert exc_info.value.status_code == 401
