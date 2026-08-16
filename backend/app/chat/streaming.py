from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator

STUB_ASSISTANT_TEXT = "Stub response: retrieval is not wired yet."

UI_MESSAGE_STREAM_HEADERS = {
    "Cache-Control": "no-cache",
    "x-vercel-ai-ui-message-stream": "v1",
}


def _sse(payload: dict | str) -> str:
    if isinstance(payload, str):
        body = payload
    else:
        body = json.dumps(payload, separators=(",", ":"))
    return f"data: {body}\n\n"


async def stub_ui_message_stream(
    *,
    message_id: str | None = None,
    text_block_id: str | None = None,
) -> AsyncIterator[str]:
    msg_id = message_id or str(uuid.uuid4())
    block_id = text_block_id or str(uuid.uuid4())

    yield _sse({"type": "start", "messageId": msg_id})
    yield _sse({"type": "text-start", "id": block_id})
    yield _sse({"type": "text-delta", "id": block_id, "delta": STUB_ASSISTANT_TEXT})
    yield _sse({"type": "text-end", "id": block_id})
    yield _sse({"type": "finish"})
    yield _sse("[DONE]")
