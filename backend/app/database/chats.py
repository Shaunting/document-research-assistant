from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from supabase import AsyncClient

from app.auth.dependencies import CurrentUser
from app.database.supabase import create_service_role_client


@dataclass(frozen=True, slots=True)
class ThreadSummary:
    id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class MessageSummary:
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime
    message_json: dict[str, Any] | None


async def ensure_user_exists(user: CurrentUser) -> None:
    admin = await create_service_role_client()
    await (
        admin.table("users")
        .upsert({"id": str(user.id), "email": user.email}, on_conflict="id")
        .execute()
    )


def _parse_thread_row(row: dict) -> ThreadSummary:
    return ThreadSummary(
        id=uuid.UUID(row["id"]),
        title=row.get("title"),
        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
        updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")),
    )


async def _fetch_thread_row(client: AsyncClient, thread_id: uuid.UUID) -> dict | None:
    response = await (
        client.table("chat_threads")
        .select("id,user_id,title,created_at,updated_at")
        .eq("id", str(thread_id))
        .maybe_single()
        .execute()
    )
    if response is None or response.data is None:
        return None
    return response.data


async def resolve_thread_for_user(
    *,
    user_client: AsyncClient,
    admin_client: AsyncClient,
    thread_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ThreadSummary:
    row = await _fetch_thread_row(user_client, thread_id)
    if row is not None:
        return _parse_thread_row(row)

    admin_row = await _fetch_thread_row(admin_client, thread_id)
    if admin_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not allowed to access this thread",
    )
