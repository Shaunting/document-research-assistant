from enum import Enum

from pydantic import BaseModel


class ChunkType(str, Enum):
    TEXT = "text"
    TABLE = "table"


class Block(BaseModel):
    text: str
    block_type: ChunkType
    page_start: int
    page_end: int
    section_path: str


class ParsedDocument(BaseModel):
    markdown: str
    page_count: int
    blocks: list[Block]
