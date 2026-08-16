import uuid
from datetime import datetime, timezone
from unittest.mock import ANY, AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.database.chats import ThreadSummary
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _thread_summary() -> ThreadSummary:
    now = datetime(2026, 6, 30, tzinfo=timezone.utc)
    return ThreadSummary(
        id=uuid.uuid4(),
        title=None,
        created_at=now,
        updated_at=now,
    )


def test_list_threads_requires_auth(client: TestClient):
    response = client.get("/chat/threads")
    assert response.status_code == 401


def test_create_thread_returns_201(client: TestClient):
    thread = _thread_summary()
    with (
        patch("app.api.chat.ensure_user_exists", new_callable=AsyncMock),
        patch("app.api.chat.create_thread", new_callable=AsyncMock, return_value=thread),
        patch("app.auth.dependencies.create_user_client", new_callable=AsyncMock),
        patch("app.auth.dependencies.verify_access_token", new_callable=AsyncMock),
    ):
        response = client.post(
            "/chat/threads",
            headers={"Authorization": "Bearer good-token"},
            json={},
        )
    assert response.status_code == 201
    assert response.json()["id"] == str(thread.id)


def test_list_messages_returns_403(client: TestClient):
    thread_id = uuid.uuid4()
    with (
        patch(
            "app.api.chat.resolve_thread_for_user",
            new_callable=AsyncMock,
            side_effect=HTTPException(status_code=403, detail="Not allowed to access this thread"),
        ),
        patch("app.api.chat.create_service_role_client", new_callable=AsyncMock),
        patch("app.auth.dependencies.create_user_client", new_callable=AsyncMock),
        patch("app.auth.dependencies.verify_access_token", new_callable=AsyncMock),
    ):
        response = client.get(
            f"/chat/threads/{thread_id}/messages",
            headers={"Authorization": "Bearer good-token"},
        )
    assert response.status_code == 403


def test_list_messages_returns_404(client: TestClient):
    thread_id = uuid.uuid4()
    with (
        patch(
            "app.api.chat.resolve_thread_for_user",
            new_callable=AsyncMock,
            side_effect=HTTPException(status_code=404, detail="Thread not found"),
        ),
        patch("app.api.chat.create_service_role_client", new_callable=AsyncMock),
        patch("app.auth.dependencies.create_user_client", new_callable=AsyncMock),
        patch("app.auth.dependencies.verify_access_token", new_callable=AsyncMock),
    ):
        response = client.get(
            f"/chat/threads/{thread_id}/messages",
            headers={"Authorization": "Bearer good-token"},
        )
    assert response.status_code == 404


def test_stream_returns_event_stream(client: TestClient):
    thread_id = uuid.uuid4()
    with (
        patch("app.api.chat.ensure_user_exists", new_callable=AsyncMock),
        patch(
            "app.api.chat.resolve_thread_for_user",
            new_callable=AsyncMock,
            return_value=_thread_summary(),
        ),
        patch("app.api.chat.insert_message", new_callable=AsyncMock),
        patch("app.api.chat.touch_thread", new_callable=AsyncMock),
        patch("app.api.chat.create_service_role_client", new_callable=AsyncMock),
        patch("app.auth.dependencies.create_user_client", new_callable=AsyncMock),
        patch("app.auth.dependencies.verify_access_token", new_callable=AsyncMock),
    ):
        response = client.post(
            "/chat/stream",
            headers={"Authorization": "Bearer good-token"},
            json={
                "threadId": str(thread_id),
                "messages": [
                    {"role": "user", "parts": [{"type": "text", "text": "Hi"}]},
                ],
            },
        )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["x-vercel-ai-ui-message-stream"] == "v1"
    assert "data: [DONE]" in response.text


def test_stream_persists_after_completion(client: TestClient):
    thread_id = uuid.uuid4()
    mock_insert = AsyncMock()
    mock_touch = AsyncMock()
    with (
        patch("app.api.chat.ensure_user_exists", new_callable=AsyncMock),
        patch(
            "app.api.chat.resolve_thread_for_user",
            new_callable=AsyncMock,
            return_value=_thread_summary(),
        ),
        patch("app.api.chat.insert_message", mock_insert),
        patch("app.api.chat.touch_thread", mock_touch),
        patch("app.api.chat.create_service_role_client", new_callable=AsyncMock),
        patch("app.auth.dependencies.create_user_client", new_callable=AsyncMock),
        patch("app.auth.dependencies.verify_access_token", new_callable=AsyncMock),
    ):
        client.post(
            "/chat/stream",
            headers={"Authorization": "Bearer good-token"},
            json={
                "threadId": str(thread_id),
                "messages": [
                    {"role": "user", "parts": [{"type": "text", "text": "Hi"}]},
                ],
            },
        )
    assert mock_insert.await_count == 2
    mock_touch.assert_awaited_once()


def test_stream_does_not_persist_on_disconnect(client: TestClient):
    thread_id = uuid.uuid4()
    mock_insert = AsyncMock()
    mock_touch = AsyncMock()

    async def _broken_stream(*args, **kwargs):
        yield "data: {\"type\": \"start\"}\n\n"
        raise RuntimeError("simulated disconnect")

    with (
        patch("app.api.chat.ensure_user_exists", new_callable=AsyncMock),
        patch(
            "app.api.chat.resolve_thread_for_user",
            new_callable=AsyncMock,
            return_value=_thread_summary(),
        ),
        patch("app.api.chat.stub_ui_message_stream", _broken_stream),
        patch("app.api.chat.insert_message", mock_insert),
        patch("app.api.chat.touch_thread", mock_touch),
        patch("app.api.chat.create_service_role_client", new_callable=AsyncMock),
        patch("app.auth.dependencies.create_user_client", new_callable=AsyncMock),
        patch("app.auth.dependencies.verify_access_token", new_callable=AsyncMock),
    ):
        with pytest.raises(RuntimeError, match="simulated disconnect"):
            client.post(
                "/chat/stream",
                headers={"Authorization": "Bearer good-token"},
                json={
                    "threadId": str(thread_id),
                    "messages": [
                        {"role": "user", "parts": [{"type": "text", "text": "Hi"}]},
                    ],
                },
            )

    assert mock_insert.await_count == 0
    mock_touch.assert_not_awaited()


def test_stream_derives_title_when_thread_title_is_null(client: TestClient):
    thread_id = uuid.uuid4()
    mock_touch = AsyncMock()
    with (
        patch("app.api.chat.ensure_user_exists", new_callable=AsyncMock),
        patch(
            "app.api.chat.resolve_thread_for_user",
            new_callable=AsyncMock,
            return_value=_thread_summary(),  # title=None
        ),
        patch("app.api.chat.insert_message", new_callable=AsyncMock),
        patch("app.api.chat.touch_thread", mock_touch),
        patch("app.api.chat.create_service_role_client", new_callable=AsyncMock),
        patch("app.auth.dependencies.create_user_client", new_callable=AsyncMock),
        patch("app.auth.dependencies.verify_access_token", new_callable=AsyncMock),
    ):
        client.post(
            "/chat/stream",
            headers={"Authorization": "Bearer good-token"},
            json={
                "threadId": str(thread_id),
                "messages": [
                    {"role": "user", "parts": [{"type": "text", "text": "What is RRF?"}]},
                ],
            },
        )
    mock_touch.assert_awaited_once_with(ANY, thread_id, title="What is RRF?")


def test_stream_does_not_overwrite_existing_title(client: TestClient):
    thread_id = uuid.uuid4()
    existing = ThreadSummary(
        id=thread_id,
        title="Existing title",
        created_at=datetime(2026, 6, 30, tzinfo=timezone.utc),
        updated_at=datetime(2026, 6, 30, tzinfo=timezone.utc),
    )
    mock_touch = AsyncMock()
    with (
        patch("app.api.chat.ensure_user_exists", new_callable=AsyncMock),
        patch(
            "app.api.chat.resolve_thread_for_user",
            new_callable=AsyncMock,
            return_value=existing,
        ),
        patch("app.api.chat.insert_message", new_callable=AsyncMock),
        patch("app.api.chat.touch_thread", mock_touch),
        patch("app.api.chat.create_service_role_client", new_callable=AsyncMock),
        patch("app.auth.dependencies.create_user_client", new_callable=AsyncMock),
        patch("app.auth.dependencies.verify_access_token", new_callable=AsyncMock),
    ):
        client.post(
            "/chat/stream",
            headers={"Authorization": "Bearer good-token"},
            json={
                "threadId": str(thread_id),
                "messages": [
                    {"role": "user", "parts": [{"type": "text", "text": "Hi again"}]},
                ],
            },
        )
    mock_touch.assert_awaited_once_with(ANY, thread_id, title=None)
