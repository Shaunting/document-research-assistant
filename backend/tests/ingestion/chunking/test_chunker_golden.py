from itertools import groupby
from pathlib import Path

import pytest

from app.ingestion.chunking.chunker import chunk_document
from app.ingestion.chunking.schemas import ChunkingConfig
from app.ingestion.parsing.schemas import ChunkType, ParsedDocument

FIXTURES_DIR = Path(__file__).parents[4] / "data" / "papers" / "parsed"
FIXTURE_PATHS = sorted(FIXTURES_DIR.glob("*.json"))


@pytest.fixture(params=FIXTURE_PATHS, ids=[p.stem[:8] for p in FIXTURE_PATHS])
def parsed_document(request) -> ParsedDocument:
    return ParsedDocument.model_validate_json(request.param.read_text())


def test_chunk_sizes_stay_within_bounds(parsed_document):
    config = ChunkingConfig()
    chunks = chunk_document(parsed_document, config)
    for chunk in chunks:
        if chunk.chunk_type == ChunkType.TEXT:
            assert chunk.token_count <= config.max_tokens
        # Table chunks may legitimately exceed max_tokens (never split).


def test_chunk_section_sequence_matches_block_section_sequence(parsed_document):
    chunks = chunk_document(parsed_document)
    block_section_sequence = [
        key for key, _ in groupby(b.section_path for b in parsed_document.blocks)
    ]
    chunk_section_sequence = [key for key, _ in groupby(c.section_path for c in chunks)]
    assert chunk_section_sequence == block_section_sequence


def _table_content(chunk) -> str:
    prefix = f"{chunk.section_path}\n\n"
    if chunk.section_path and chunk.text.startswith(prefix):
        return chunk.text.removeprefix(prefix)
    return chunk.text


def test_table_chunks_are_never_merged_or_split(parsed_document):
    original_table_texts = [
        b.text for b in parsed_document.blocks if b.block_type == ChunkType.TABLE
    ]
    chunks = chunk_document(parsed_document)
    table_chunks = [c for c in chunks if c.chunk_type == ChunkType.TABLE]
    assert [_table_content(c) for c in table_chunks] == original_table_texts
    for chunk, original in zip(table_chunks, original_table_texts, strict=True):
        if chunk.section_path:
            assert chunk.text == f"{chunk.section_path}\n\n{original}"
        else:
            assert chunk.text == original


def test_chunk_index_is_sequential(parsed_document):
    chunks = chunk_document(parsed_document)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_every_chunk_has_a_valid_page_range(parsed_document):
    chunks = chunk_document(parsed_document)
    for chunk in chunks:
        assert 1 <= chunk.page_start <= chunk.page_end <= parsed_document.page_count


def test_produces_a_reasonable_number_of_chunks(parsed_document):
    chunks = chunk_document(parsed_document)
    # A ~40-page paper normalizes to ~80-100 blocks pre-chunking (per parsing.md);
    # packing into ~512-token windows should land in the same order of magnitude.
    assert 0 < len(chunks) <= len(parsed_document.blocks) * 2
