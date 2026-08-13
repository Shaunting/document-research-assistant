# backend/tests/ingest/test_parser.py
"""Integration/smoke tests for normalize().

These are deliberately not isolated unit tests: constructing a valid
DoclingDocument by hand is impractically complex (it's a full
tree-structured Pydantic model with cross-references), so instead we run a
real Docling conversion against a fixture PDF once per module and assert on
properties of the resulting ParsedDocument. Marked `integration` so they're
excluded from the default (fast) test run.
"""

from pathlib import Path

import pytest
from docling.document_converter import DocumentConverter

from app.ingest.parser import normalize
from app.ingest.schemas import ChunkType

FIXTURE_PDF = Path(__file__).parents[3] / "data" / "papers" / "auto_score.pdf"


@pytest.fixture(scope="module")
def parsed_fixture():
    result = DocumentConverter().convert(str(FIXTURE_PDF))
    return normalize(result.document)


@pytest.mark.integration
def test_normalize_produces_page_count_matching_pdf(parsed_fixture):
    assert parsed_fixture.page_count == 19


@pytest.mark.integration
def test_normalize_includes_document_markdown(parsed_fixture):
    assert "AutoScore" in parsed_fixture.markdown


@pytest.mark.integration
def test_normalize_produces_only_text_and_table_blocks(parsed_fixture):
    block_types = {b.block_type for b in parsed_fixture.blocks}
    assert block_types <= {ChunkType.TEXT, ChunkType.TABLE}


@pytest.mark.integration
def test_normalize_builds_section_path_from_headings(parsed_fixture):
    abstract_blocks = [b for b in parsed_fixture.blocks if b.section_path == "Abstract"]
    assert len(abstract_blocks) >= 1
    assert "Background" in abstract_blocks[0].text


@pytest.mark.integration
def test_normalize_table_block_includes_caption_and_markdown_table(parsed_fixture):
    table_blocks = [b for b in parsed_fixture.blocks if b.block_type == ChunkType.TABLE]
    assert len(table_blocks) == 6
    described_cohort = [b for b in table_blocks if "Description of the study cohort" in b.text]
    assert len(described_cohort) == 1
    assert "|" in described_cohort[0].text


@pytest.mark.integration
def test_normalize_merges_picture_caption_into_surrounding_text(parsed_fixture):
    matches = [b for b in parsed_fixture.blocks if "Flowchart of the AutoScore framework" in b.text]
    assert len(matches) == 1
    assert matches[0].block_type == ChunkType.TEXT


@pytest.mark.integration
def test_normalize_page_range_is_within_document_bounds(parsed_fixture):
    for block in parsed_fixture.blocks:
        assert 1 <= block.page_start <= block.page_end <= 19
