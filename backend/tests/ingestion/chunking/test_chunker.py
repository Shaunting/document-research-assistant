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
