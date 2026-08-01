from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

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
