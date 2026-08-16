# backend/app/api/chat.py
from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from supabase import AsyncClient

from app.auth.dependencies import CurrentUser, get_current_user, get_user_supabase_client
from app.chat.messages import extract_last_user_turn
from app.chat.schemas import StreamChatRequest
from app.chat.streaming import STUB_ASSISTANT_TEXT, UI_MESSAGE_STREAM_HEADERS, stub_ui_message_stream
from app.database.chats import (
    MessageSummary,
    ThreadSummary,
    create_thread,
    derive_thread_title,
    ensure_user_exists,
    insert_message,
    list_messages,
    list_threads,
    resolve_thread_for_user,
    touch_thread,
)
from app.database.supabase import create_service_role_client

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class CreateThreadRequest(BaseModel):
    title: str | None = None


def thread_to_json(thread: ThreadSummary) -> dict:
    return {
        "id": str(thread.id),
        "title": thread.title,
        "createdAt": thread.created_at.isoformat(),
        "updatedAt": thread.updated_at.isoformat(),
    }


def message_to_json(message: MessageSummary) -> dict:
    return {
        "id": str(message.id),
        "role": message.role,
        "content": message.content,
        "createdAt": message.created_at.isoformat(),
        "messageJson": message.message_json,
    }


@router.get("/threads")
async def list_threads_route(
    current_user: CurrentUser = Depends(get_current_user),
    user_client: AsyncClient = Depends(get_user_supabase_client),
) -> list[dict]:
    await ensure_user_exists(current_user)
    threads = await list_threads(user_client, current_user.id)
    return [thread_to_json(thread) for thread in threads]


@router.post("/threads", status_code=status.HTTP_201_CREATED)
async def create_thread_route(
    body: CreateThreadRequest,
    current_user: CurrentUser = Depends(get_current_user),
    user_client: AsyncClient = Depends(get_user_supabase_client),
) -> dict:
    await ensure_user_exists(current_user)
    thread = await create_thread(user_client, current_user.id, body.title)
    return thread_to_json(thread)


@router.get("/threads/{thread_id}/messages")
async def list_messages_route(
    thread_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    user_client: AsyncClient = Depends(get_user_supabase_client),
) -> list[dict]:
    admin_client = await create_service_role_client()
    await resolve_thread_for_user(
        user_client=user_client,
        admin_client=admin_client,
        thread_id=thread_id,
        user_id=current_user.id,
    )
    messages = await list_messages(user_client, thread_id)
    return [message_to_json(message) for message in messages]


@router.post("/stream")
async def stream_route(
    body: StreamChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
    user_client: AsyncClient = Depends(get_user_supabase_client),
) -> StreamingResponse:
    try:
        user_text, user_message = extract_last_user_turn(body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    admin_client = await create_service_role_client()
    await ensure_user_exists(current_user)
    resolved_thread = await resolve_thread_for_user(
        user_client=user_client,
        admin_client=admin_client,
        thread_id=body.thread_id,
        user_id=current_user.id,
    )

    assistant_json = {
        "parts": [{"type": "text", "text": STUB_ASSISTANT_TEXT}],
    }
    user_json = user_message.model_dump(mode="json")
    title_update = (
        derive_thread_title(user_text) if resolved_thread.title is None else None
    )

    async def generate():
        completed = False
        try:
            async for chunk in stub_ui_message_stream():
                yield chunk
            completed = True
        finally:
            if completed:
                try:
                    await insert_message(
                        user_client,
                        body.thread_id,
                        "user",
                        user_text,
                        message_json=user_json,
                    )
                    await insert_message(
                        user_client,
                        body.thread_id,
                        "assistant",
                        STUB_ASSISTANT_TEXT,
                        message_json=assistant_json,
                    )
                    await touch_thread(user_client, body.thread_id, title=title_update)
                except Exception as exc:
                    logger.error(
                        "chat_turn_persistence_failed",
                        thread_id=str(body.thread_id),
                        error=str(exc),
                    )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers=UI_MESSAGE_STREAM_HEADERS,
    )
