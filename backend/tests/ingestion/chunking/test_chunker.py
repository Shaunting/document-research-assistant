import pytest

from app.ingestion.chunking.chunker import _count_tokens, _group_by_section, chunk_document
from app.ingestion.chunking.schemas import ChunkingConfig
from app.ingestion.parsing.schemas import Block, ChunkType, ParsedDocument


def _text_block(text: str, section_path: str = "Intro", page: int = 1) -> Block:
    return Block(
        text=text,
        block_type=ChunkType.TEXT,
        page_start=page,
        page_end=page,
        section_path=section_path,
    )


def _table_block(text: str, section_path: str = "Results", page: int = 1) -> Block:
    return Block(
        text=text,
        block_type=ChunkType.TABLE,
        page_start=page,
        page_end=page,
        section_path=section_path,
    )


def test_count_tokens_matches_cl100k_base():
    config = ChunkingConfig()
    assert _count_tokens("hello world", config) == 2


def test_group_by_section_splits_on_section_change():
    blocks = [
        _text_block("a", section_path="Abstract"),
        _text_block("b", section_path="Abstract"),
        _text_block("c", section_path="Methods"),
    ]
    runs = _group_by_section(blocks)
    assert len(runs) == 2
    assert [b.text for b in runs[0]] == ["a", "b"]
    assert [b.text for b in runs[1]] == ["c"]


def test_group_by_section_treats_empty_string_as_its_own_run():
    blocks = [
        _text_block("preamble", section_path=""),
        _text_block("a", section_path="Abstract"),
    ]
    runs = _group_by_section(blocks)
    assert len(runs) == 2
    assert runs[0][0].section_path == ""


def test_table_block_becomes_its_own_chunk():
    parsed = ParsedDocument(
        markdown="",
        page_count=1,
        blocks=[_table_block("| a | b |\n| - | - |", section_path="Results", page=4)],
    )
    chunks = chunk_document(parsed)
    assert len(chunks) == 1
    assert chunks[0].chunk_type == ChunkType.TABLE
    assert chunks[0].page_start == 4
    assert chunks[0].page_end == 4


def test_table_never_merges_with_surrounding_text():
    parsed = ParsedDocument(
        markdown="",
        page_count=1,
        blocks=[
            _text_block("before", section_path="Results", page=4),
            _table_block("| a | b |", section_path="Results", page=4),
            _text_block("after", section_path="Results", page=4),
        ],
    )
    chunks = chunk_document(parsed)
    types = [c.chunk_type for c in chunks]
    assert ChunkType.TABLE in types
    table_chunk = next(c for c in chunks if c.chunk_type == ChunkType.TABLE)
    assert "before" not in table_chunk.text
    assert "after" not in table_chunk.text


def test_small_text_blocks_in_same_section_pack_into_one_chunk():
    parsed = ParsedDocument(
        markdown="",
        page_count=1,
        blocks=[
            _text_block("one.", section_path="Abstract", page=1),
            _text_block("two.", section_path="Abstract", page=1),
        ],
    )
    chunks = chunk_document(parsed)
    assert len(chunks) == 1
    assert "one." in chunks[0].text
    assert "two." in chunks[0].text


def test_chunk_never_spans_two_sections():
    parsed = ParsedDocument(
        markdown="",
        page_count=1,
        blocks=[
            _text_block("abstract text", section_path="Abstract", page=1),
            _text_block("intro text", section_path="Introduction", page=1),
        ],
    )
    chunks = chunk_document(parsed)
    sections = {c.section_path for c in chunks}
    assert sections == {"Abstract", "Introduction"}
    assert len(chunks) == 2


def test_long_section_packs_into_multiple_chunks():
    config = ChunkingConfig(target_tokens=5, max_tokens=8)
    # NOTE: fixture calibrated against the real cl100k_base tokenizer (not the
    # brief's original "word{i} " * 6, which already tokenizes to 13 tokens per
    # block -- above max_tokens on its own). A single "word{i} " repeat is 3
    # tokens (comfortably under target_tokens=5), so pairs of blocks accumulate
    # before a group is pushed, and the joined+breadcrumbed chunk text lands at
    # exactly 8 tokens (<= max_tokens=8), giving 2 packed chunks from 4 blocks.
    blocks = [_text_block(f"word{i} ", section_path="Methods", page=1) for i in range(4)]
    parsed = ParsedDocument(markdown="", page_count=1, blocks=blocks)
    chunks = chunk_document(parsed, config)
    assert len(chunks) > 1
    assert all(c.section_path == "Methods" for c in chunks)
    for c in chunks:
        assert c.token_count <= config.max_tokens
