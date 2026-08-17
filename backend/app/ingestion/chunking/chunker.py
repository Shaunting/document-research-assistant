from itertools import groupby

import tiktoken

from app.ingestion.chunking.schemas import Chunk, ChunkingConfig
from app.ingestion.parsing.schemas import Block, ChunkType, ParsedDocument


def _count_tokens(text: str, config: ChunkingConfig) -> int:
    encoding = tiktoken.get_encoding(config.tokenizer)
    return len(encoding.encode(text))


def _group_by_section(blocks: list[Block]) -> list[list[Block]]:
    return [list(group) for _key, group in groupby(blocks, key=lambda b: b.section_path)]


def _pack_text_run(blocks: list[Block], config: ChunkingConfig) -> list[list[Block]]:
    groups: list[list[Block]] = []
    current: list[Block] = []
    current_tokens = 0

    for block in blocks:
        block_tokens = _count_tokens(block.text, config)
        if current and current_tokens + block_tokens > config.max_tokens:
            groups.append(current)
            current = []
            current_tokens = 0
        current.append(block)
        current_tokens += block_tokens
        if current_tokens >= config.target_tokens:
            groups.append(current)
            current = []
            current_tokens = 0

    if current:
        groups.append(current)
    return groups


def _blocks_to_chunk(blocks: list[Block], config: ChunkingConfig) -> Chunk:
    text = "\n\n".join(b.text for b in blocks)
    section_path = blocks[0].section_path
    page_start = min(b.page_start for b in blocks)
    page_end = max(b.page_end for b in blocks)
    return Chunk(
        chunk_index=0,  # reassigned in chunk_document()
        text=text,
        token_count=_count_tokens(text, config),
        page_start=page_start,
        page_end=page_end,
        section_path=section_path,
        chunk_type=ChunkType.TEXT,
        metadata={"chunking_config_version": config.version},
    )


def chunk_document(parsed: ParsedDocument, config: ChunkingConfig = ChunkingConfig()) -> list[Chunk]:
    if not parsed.blocks:
        raise ValueError("cannot chunk a document with no blocks")

    chunks: list[Chunk] = []
    for run in _group_by_section(parsed.blocks):
        text_blocks: list[Block] = []
        for block in run:
            if block.block_type == ChunkType.TABLE:
                if text_blocks:
                    for group in _pack_text_run(text_blocks, config):
                        chunks.append(_blocks_to_chunk(group, config))
                    text_blocks = []
                chunks.append(
                    Chunk(
                        chunk_index=0,
                        text=block.text,
                        token_count=_count_tokens(block.text, config),
                        page_start=block.page_start,
                        page_end=block.page_end,
                        section_path=block.section_path,
                        chunk_type=ChunkType.TABLE,
                        metadata={"chunking_config_version": config.version},
                    )
                )
            else:
                text_blocks.append(block)
        if text_blocks:
            for group in _pack_text_run(text_blocks, config):
                chunks.append(_blocks_to_chunk(group, config))

    for index, chunk in enumerate(chunks):
        chunk.chunk_index = index

    return chunks
