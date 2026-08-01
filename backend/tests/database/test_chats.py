import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.auth.dependencies import CurrentUser
from app.database import chats as chats_module


@pytest.mark.asyncio
async def test_ensure_user_exists_upserts_users_row():
    user = CurrentUser(id=uuid.uuid4(), email="test@example.com")
    mock_admin = MagicMock()
    mock_table = MagicMock()
    mock_upsert_result = MagicMock()
    mock_admin.table.return_value = mock_table
    mock_table.upsert.return_value = mock_upsert_result
    mock_upsert_result.execute = AsyncMock(return_value=object())

    with patch(
        "app.database.chats.create_service_role_client",
        new_callable=AsyncMock,
        return_value=mock_admin,
    ):
        await chats_module.ensure_user_exists(user)

    mock_admin.table.assert_called_once_with("users")
    mock_table.upsert.assert_called_once_with(
        {"id": str(user.id), "email": user.email},
        on_conflict="id",
    )
    mock_upsert_result.execute.assert_awaited_once()
