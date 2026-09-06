import re
from itertools import groupby

import tiktoken

from app.ingestion.chunking.schemas import Chunk, ChunkingConfig
from app.ingestion.parsing.schemas import Block, ChunkType, ParsedDocument


def chunk_document(parsed: ParsedDocument, config: ChunkingConfig = ChunkingConfig()) -> list[Chunk]:
    if not parsed.blocks:
        raise ValueError("cannot chunk a document with no blocks")

    chunks: list[Chunk] = []
    for run in _group_by_section(parsed.blocks):
        section_path = run[0].section_path
        # Every chunk in this run gets section_path prepended as a breadcrumb
        # in _blocks_to_chunk, after packing/splitting decisions are made.
        # Reserve that breadcrumb's token cost from the cap used for those
        # decisions so the post-breadcrumb chunk never exceeds max_tokens.
        pack_config = _budget_for_breadcrumb(section_path, config)

        text_blocks: list[Block] = []
        for block in run:
            if block.block_type == ChunkType.TABLE:
                _flush_text_blocks(chunks, text_blocks, pack_config, config)
                text_blocks = []
                chunks.append(_blocks_to_chunk([block], config, chunk_type=ChunkType.TABLE))
            else:
                text_blocks.extend(_split_oversized_block(block, pack_config))
        _flush_text_blocks(chunks, text_blocks, pack_config, config)

    for index, chunk in enumerate(chunks):
        chunk.chunk_index = index

    return chunks


def _flush_text_blocks(
    chunks: list[Chunk],
    text_blocks: list[Block],
    pack_config: ChunkingConfig,
    config: ChunkingConfig,
) -> None:
    for group in _pack_text_run(text_blocks, pack_config):
        chunks.append(_blocks_to_chunk(group, config))


def _count_tokens(text: str, config: ChunkingConfig) -> int:
    encoding = tiktoken.get_encoding(config.tokenizer)
    return len(encoding.encode(text))


def _group_by_section(blocks: list[Block]) -> list[list[Block]]:
    return [list(group) for _key, group in groupby(blocks, key=lambda b: b.section_path)]


def _split_by_sentence(text: str) -> list[str]:
    # Best-effort split: paragraph splitting first, then sentence-boundary
    # splitting as the only fallback. If no sentence boundary is found either,
    # this returns the text unchanged, so a boundary-less oversized paragraph
    # can still produce a chunk over max_tokens -- there is no further
    # recursive (e.g. hard token-window) fallback beyond this.
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return sentences if len(sentences) > 1 else [text]


def _split_oversized_block(block: Block, config: ChunkingConfig) -> list[Block]:
    if _count_tokens(block.text, config) <= config.max_tokens:
        return [block]

    paragraphs = [p for p in block.text.split("\n\n") if p.strip()]
    if len(paragraphs) > 1:
        # Split on paragraph breaks; any single paragraph that's *still*
        # oversized on its own falls back to sentence-boundary splitting
        # just for that paragraph, not the whole block.
        pieces: list[str] = []
        for paragraph in paragraphs:
            if _count_tokens(paragraph, config) <= config.max_tokens:
                pieces.append(paragraph)
            else:
                pieces.extend(_split_by_sentence(paragraph))
    else:
        # Single oversized paragraph: fall back to sentence-boundary splitting directly.
        pieces = _split_by_sentence(block.text)

    return [
        Block(
            text=piece,
            block_type=block.block_type,
            page_start=block.page_start,
            page_end=block.page_end,
            section_path=block.section_path,
        )
        for piece in pieces
        if piece.strip()
    ]


def _breadcrumb_tokens(section_path: str, config: ChunkingConfig) -> int:
    if not section_path:
        return 0
    return _count_tokens(f"{section_path}\n\n", config)


def _budget_for_breadcrumb(section_path: str, config: ChunkingConfig) -> ChunkingConfig:
    """Return a config whose max_tokens is reduced by the breadcrumb's token
    cost, so packing/splitting decisions leave enough headroom that adding
    the breadcrumb afterward (in _blocks_to_chunk) never pushes the final
    chunk text over the real config.max_tokens."""
    reserved = _breadcrumb_tokens(section_path, config)
    if reserved <= 0:
        return config
    return config.model_copy(update={"max_tokens": max(config.max_tokens - reserved, 1)})


def _pack_text_run(blocks: list[Block], config: ChunkingConfig) -> list[list[Block]]:
    # _blocks_to_chunk joins a group's block texts with "\n\n", which costs
    # extra tokens per boundary that a naive sum of per-block token counts
    # doesn't account for. Charge that separator cost here too -- the same
    # reasoning _budget_for_breadcrumb applies to the breadcrumb -- so the
    # group sizes we decide on here still fit once actually joined.
    sep_tokens = _count_tokens("\n\n", config)
    groups: list[list[Block]] = []
    current: list[Block] = []
    current_tokens = 0

    for block in blocks:
        block_tokens = _count_tokens(block.text, config)
        # Joining this block onto a non-empty group costs an extra separator;
        # starting a fresh group costs nothing extra.
        added_tokens = block_tokens + sep_tokens if current else block_tokens
        if current and current_tokens + added_tokens > config.max_tokens:
            groups.append(current)
            current = []
            current_tokens = 0
            added_tokens = block_tokens  # first block of the new group: no separator
        current.append(block)
        current_tokens += added_tokens
        if current_tokens >= config.target_tokens:
            groups.append(current)
            current = []
            current_tokens = 0

    if current:
        groups.append(current)
    return groups


def _blocks_to_chunk(
    blocks: list[Block],
    config: ChunkingConfig,
    chunk_type: ChunkType = ChunkType.TEXT,
) -> Chunk:
    content = "\n\n".join(b.text for b in blocks)
    section_path = blocks[0].section_path
    text = f"{section_path}\n\n{content}" if section_path else content
    page_start = min(b.page_start for b in blocks)
    page_end = max(b.page_end for b in blocks)
    return Chunk(
        chunk_index=0,  # reassigned in chunk_document()
        text=text,
        token_count=_count_tokens(text, config),
        page_start=page_start,
        page_end=page_end,
        section_path=section_path,
        chunk_type=chunk_type,
        metadata={"chunking_config_version": config.version},
    )
