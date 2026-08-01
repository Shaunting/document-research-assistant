from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UIMessagePayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    role: str
    parts: list[dict[str, Any]]
    id: str | None = None


class StreamChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    thread_id: uuid.UUID = Field(alias="threadId")
    messages: list[UIMessagePayload]
