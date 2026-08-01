import uuid

import pytest
from pydantic import ValidationError

from app.chat.messages import StreamChatRequest, extract_last_user_turn


def test_stream_chat_request_parses_thread_id_alias():
    thread_id = uuid.uuid4()
    req = StreamChatRequest.model_validate(
        {
            "threadId": str(thread_id),
            "messages": [
                {
                    "role": "user",
                    "parts": [{"type": "text", "text": "Hello"}],
                }
            ],
        }
    )
    assert req.thread_id == thread_id


def test_extract_last_user_turn_returns_text_and_message():
    req = StreamChatRequest.model_validate(
        {
            "threadId": str(uuid.uuid4()),
            "messages": [
                {
                    "id": "u1",
                    "role": "user",
                    "parts": [{"type": "text", "text": "First"}],
                },
                {
                    "id": "u2",
                    "role": "assistant",
                    "parts": [{"type": "text", "text": "Hi"}],
                },
                {
                    "id": "u3",
                    "role": "user",
                    "parts": [{"type": "text", "text": "Second question"}],
                },
            ],
        }
    )
    text, message = extract_last_user_turn(req)
    assert text == "Second question"
    assert message.id == "u3"


def test_extract_last_user_turn_rejects_empty_messages():
    req = StreamChatRequest.model_validate(
        {"threadId": str(uuid.uuid4()), "messages": []}
    )
    with pytest.raises(ValueError, match="no user message"):
        extract_last_user_turn(req)


def test_extract_last_user_turn_rejects_no_user_message():
    req = StreamChatRequest.model_validate(
        {
            "threadId": str(uuid.uuid4()),
            "messages": [
                {
                    "role": "assistant",
                    "parts": [{"type": "text", "text": "Hi"}],
                }
            ],
        }
    )
    with pytest.raises(ValueError, match="no user message"):
        extract_last_user_turn(req)


def test_stream_chat_request_requires_thread_id():
    with pytest.raises(ValidationError):
        StreamChatRequest.model_validate({"messages": []})
