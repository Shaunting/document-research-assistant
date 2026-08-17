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


def test_no_chunk_spans_two_sections(parsed_document):
    chunks = chunk_document(parsed_document)
    block_section_paths = {b.section_path for b in parsed_document.blocks}
    chunk_section_paths = {c.section_path for c in chunks}
    assert chunk_section_paths <= block_section_paths


def test_table_chunks_are_never_merged_or_split(parsed_document):
    original_table_texts = {
        b.text for b in parsed_document.blocks if b.block_type == ChunkType.TABLE
    }
    chunks = chunk_document(parsed_document)
    chunk_table_texts = {c.text for c in chunks if c.chunk_type == ChunkType.TABLE}
    assert chunk_table_texts == original_table_texts


def test_chunk_index_is_sequential(parsed_document):
    chunks = chunk_document(parsed_document)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_every_chunk_has_a_valid_page_range(parsed_document):
    chunks = chunk_document(parsed_document)
    for chunk in chunks:
        assert 1 <= chunk.page_start <= chunk.page_end <= parsed_document.page_count


def test_produces_a_reasonable_number_of_chunks(parsed_document):
    chunks = chunk_document(parsed_document)
    # A ~40-page paper normalizes to ~80-100 blocks pre-chunking (per ingest.md);
    # packing into ~512-token windows should land in the same order of magnitude.
    assert 0 < len(chunks) <= len(parsed_document.blocks) * 2
