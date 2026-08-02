from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth.dependencies import get_user_supabase_client


@pytest.mark.asyncio
async def test_get_user_supabase_client_requires_bearer():
    with pytest.raises(HTTPException) as exc:
        await get_user_supabase_client(None)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_user_supabase_client_returns_user_scoped_client():
    mock_client = AsyncMock()
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="jwt-token")

    with patch(
        "app.auth.dependencies.create_user_client",
        new_callable=AsyncMock,
        return_value=mock_client,
    ) as mock_create:
        client = await get_user_supabase_client(credentials)

    assert client is mock_client
    mock_create.assert_awaited_once_with("jwt-token")
