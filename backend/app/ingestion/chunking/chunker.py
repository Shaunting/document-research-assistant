from itertools import groupby

import tiktoken

from app.ingestion.chunking.schemas import Chunk, ChunkingConfig
from app.ingestion.parsing.schemas import Block, ChunkType, ParsedDocument


def _count_tokens(text: str, config: ChunkingConfig) -> int:
    encoding = tiktoken.get_encoding(config.tokenizer)
    return len(encoding.encode(text))


def _group_by_section(blocks: list[Block]) -> list[list[Block]]:
    return [list(group) for _key, group in groupby(blocks, key=lambda b: b.section_path)]


def chunk_document(parsed: ParsedDocument, config: ChunkingConfig = ChunkingConfig()) -> list[Chunk]:
    raise NotImplementedError
