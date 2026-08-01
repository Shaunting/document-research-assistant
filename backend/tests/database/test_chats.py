import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.auth.dependencies import CurrentUser
from app.database import chats as chats_module
from app.database.chats import ThreadSummary, resolve_thread_for_user


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


def _thread_row(thread_id: uuid.UUID, user_id: uuid.UUID) -> dict:
    now = datetime(2026, 6, 30, tzinfo=timezone.utc).isoformat()
    return {
        "id": str(thread_id),
        "user_id": str(user_id),
        "title": None,
        "created_at": now,
        "updated_at": now,
    }


def _as_execute(data: dict | list | None) -> AsyncMock:
    # maybe_single() responses carry .data as a dict; supabase-py returns None
    # (no response object) when zero rows match. Plain select/insert queries
    # carry .data as a list.
    if data is None:
        return AsyncMock(return_value=None)
    response = MagicMock()
    response.data = data
    return AsyncMock(return_value=response)


@pytest.mark.asyncio
async def test_resolve_thread_returns_thread_for_owner():
    thread_id = uuid.uuid4()
    user_id = uuid.uuid4()
    user_client = MagicMock()
    user_table = MagicMock()
    user_client.table.return_value = user_table
    user_table.select.return_value.eq.return_value.maybe_single.return_value.execute = _as_execute(
        _thread_row(thread_id, user_id)
    )

    result = await resolve_thread_for_user(
        user_client=user_client,
        admin_client=MagicMock(),
        thread_id=thread_id,
        user_id=user_id,
    )

    assert result.id == thread_id
    assert result.title is None


@pytest.mark.asyncio
async def test_resolve_thread_raises_404_when_missing():
    thread_id = uuid.uuid4()
    user_id = uuid.uuid4()
    user_client = MagicMock()
    user_table = MagicMock()
    user_client.table.return_value = user_table
    user_table.select.return_value.eq.return_value.maybe_single.return_value.execute = _as_execute(None)

    admin_client = MagicMock()
    admin_table = MagicMock()
    admin_client.table.return_value = admin_table
    admin_table.select.return_value.eq.return_value.maybe_single.return_value.execute = _as_execute(None)

    with pytest.raises(HTTPException) as exc:
        await resolve_thread_for_user(
            user_client=user_client,
            admin_client=admin_client,
            thread_id=thread_id,
            user_id=user_id,
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_resolve_thread_raises_403_for_other_users_thread():
    thread_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    other_id = uuid.uuid4()
    user_client = MagicMock()
    user_table = MagicMock()
    user_client.table.return_value = user_table
    user_table.select.return_value.eq.return_value.maybe_single.return_value.execute = _as_execute(None)

    admin_client = MagicMock()
    admin_table = MagicMock()
    admin_client.table.return_value = admin_table
    admin_table.select.return_value.eq.return_value.maybe_single.return_value.execute = _as_execute(
        _thread_row(thread_id, owner_id)
    )

    with pytest.raises(HTTPException) as exc:
        await resolve_thread_for_user(
            user_client=user_client,
            admin_client=admin_client,
            thread_id=thread_id,
            user_id=other_id,
        )
    assert exc.value.status_code == 403
    assert exc.value.detail == "Not allowed to access this thread"
