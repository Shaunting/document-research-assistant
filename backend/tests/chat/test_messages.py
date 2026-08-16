import uuid

import pytest

from app.chat.messages import extract_last_user_turn
from app.chat.schemas import StreamChatRequest


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
