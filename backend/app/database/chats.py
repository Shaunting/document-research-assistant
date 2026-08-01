from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
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


def _parse_message_row(row: dict) -> MessageSummary:
    return MessageSummary(
        id=uuid.UUID(row["id"]),
        role=row["role"],
        content=row["content"],
        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
        message_json=row.get("message_json"),
    )


async def list_threads(client: AsyncClient, user_id: uuid.UUID) -> list[ThreadSummary]:
    response = await (
        client.table("chat_threads")
        .select("id,title,created_at,updated_at")
        .eq("user_id", str(user_id))
        .order("updated_at", desc=True)
        .execute()
    )
    rows = response.data or []
    return [_parse_thread_row(row) for row in rows]


async def create_thread(
    client: AsyncClient, user_id: uuid.UUID, title: str | None
) -> ThreadSummary:
    response = await (
        client.table("chat_threads")
        .insert({"user_id": str(user_id), "title": title})
        .execute()
    )
    row = response.data[0]
    return _parse_thread_row(row)


async def list_messages(
    client: AsyncClient, thread_id: uuid.UUID
) -> list[MessageSummary]:
    response = await (
        client.table("chat_messages")
        .select("id,role,content,message_json,created_at")
        .eq("thread_id", str(thread_id))
        .order("created_at", desc=False)
        .execute()
    )
    rows = response.data or []
    return [_parse_message_row(row) for row in rows]


async def insert_message(
    client: AsyncClient,
    thread_id: uuid.UUID,
    role: str,
    content: str,
    message_json: dict[str, Any] | None = None,
) -> MessageSummary:
    response = await (
        client.table("chat_messages")
        .insert(
            {
                "thread_id": str(thread_id),
                "role": role,
                "content": content,
                "message_json": message_json,
            }
        )
        .execute()
    )
    row = response.data[0]
    return _parse_message_row(row)


async def touch_thread(
    client: AsyncClient, thread_id: uuid.UUID, *, title: str | None = None
) -> None:
    payload: dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if title is not None:
        payload["title"] = title
    await (
        client.table("chat_threads")
        .update(payload)
        .eq("id", str(thread_id))
        .execute()
    )


def derive_thread_title(text: str, *, limit: int = 50) -> str:
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[:limit].rstrip() + "…"
