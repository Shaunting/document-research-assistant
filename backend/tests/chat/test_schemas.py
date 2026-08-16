import uuid

import pytest
from pydantic import ValidationError

from app.chat.schemas import StreamChatRequest


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


def test_stream_chat_request_requires_thread_id():
    with pytest.raises(ValidationError):
        StreamChatRequest.model_validate({"messages": []})
