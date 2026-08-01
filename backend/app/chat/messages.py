from __future__ import annotations

from typing import Any

from app.chat.schemas import StreamChatRequest, UIMessagePayload


def _text_from_parts(parts: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for part in parts:
        if part.get("type") == "text" and isinstance(part.get("text"), str):
            chunks.append(part["text"])
    return "".join(chunks)


def extract_last_user_turn(request: StreamChatRequest) -> tuple[str, UIMessagePayload]:
    if not request.messages:
        raise ValueError("no user message")

    for message in reversed(request.messages):
        if message.role != "user":
            continue
        text = _text_from_parts(message.parts).strip()
        if not text:
            continue
        return text, message

    raise ValueError("no user message")
