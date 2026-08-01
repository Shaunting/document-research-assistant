import json

import pytest

from app.chat.streaming import STUB_ASSISTANT_TEXT, stub_ui_message_stream


@pytest.mark.asyncio
async def test_stub_stream_emits_ai_sdk_events_and_done():
    chunks = [chunk async for chunk in stub_ui_message_stream()]
    assert chunks[-1] == "data: [DONE]\n\n"

    payloads = []
    for chunk in chunks[:-1]:
        assert chunk.startswith("data: ")
        payloads.append(json.loads(chunk.removeprefix("data: ").strip()))

    assert payloads[0]["type"] == "start"
    assert "messageId" in payloads[0]
    assert payloads[1]["type"] == "text-start"
    text_id = payloads[1]["id"]
    delta = next(p for p in payloads if p["type"] == "text-delta")
    assert delta["id"] == text_id
    assert delta["delta"] == STUB_ASSISTANT_TEXT
    assert payloads[-1]["type"] == "finish"
