from typing import Any

from pydantic import BaseModel

from app.ingestion.parsing.schemas import ChunkType


class ChunkingConfig(BaseModel):
    version: str = "v1"
    target_tokens: int = 512
    max_tokens: int = 800
    tokenizer: str = "cl100k_base"  # matches text-embedding-3-small


class Chunk(BaseModel):
    chunk_index: int
    text: str
    token_count: int
    page_start: int
    page_end: int
    section_path: str
    chunk_type: ChunkType
    metadata: dict[str, Any] | None = None
