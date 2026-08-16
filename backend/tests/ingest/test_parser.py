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
from unittest.mock import patch

import pytest
from docling.document_converter import DocumentConverter
from docling_core.types.doc.document import DoclingDocument

from app.ingest.parser import normalize, parse_pdf
from app.ingest.schemas import ChunkType

FIXTURE_PDF = Path(__file__).parents[3] / "data" / "papers" / "auto_score.pdf"
FIXTURE_DOCLING_JSON = Path(__file__).parent / "fixtures" / "auto_score_docling.json"


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
    described_cohort = [
        b for b in table_blocks if "Description of the study cohort" in b.text
    ]
    assert len(described_cohort) == 1
    assert "|" in described_cohort[0].text


@pytest.mark.integration
def test_normalize_merges_picture_caption_into_surrounding_text(parsed_fixture):
    matches = [
        b
        for b in parsed_fixture.blocks
        if "Flowchart of the AutoScore framework" in b.text
    ]
    assert len(matches) == 1
    assert matches[0].block_type == ChunkType.TEXT
    assert matches[0].text.count("Flowchart of the AutoScore framework") == 1


@pytest.mark.integration
def test_normalize_does_not_leak_table_caption_into_text_block(parsed_fixture):
    text_blocks = [b for b in parsed_fixture.blocks if b.block_type == ChunkType.TEXT]
    assert all(
        "Table 1. Description of the study cohort" not in b.text for b in text_blocks
    )


def test_normalize_does_not_duplicate_picture_captions():
    """Regression test for caption duplication bugs, run against a
    pre-serialized DoclingDocument fixture so it stays in the fast suite
    (no live Docling conversion, no model loading).
    """
    doc = DoclingDocument.model_validate_json(FIXTURE_DOCLING_JSON.read_text())
    parsed = normalize(doc)

    matches = [
        b for b in parsed.blocks if "Flowchart of the AutoScore framework" in b.text
    ]
    assert len(matches) == 1
    assert matches[0].text.count("Flowchart of the AutoScore framework") == 1

    text_blocks = [b for b in parsed.blocks if b.block_type == ChunkType.TEXT]
    assert all(
        "Table 1. Description of the study cohort" not in b.text for b in text_blocks
    )


@pytest.mark.integration
def test_normalize_page_range_is_within_document_bounds(parsed_fixture):
    for block in parsed_fixture.blocks:
        assert 1 <= block.page_start <= block.page_end <= 19


@pytest.mark.integration
def test_parse_pdf_writes_and_reuses_cache(tmp_path: Path):
    cache_dir = tmp_path / "parsed"

    first = parse_pdf(FIXTURE_PDF, cache_dir=cache_dir)
    content_hash_files = list(cache_dir.glob("*.json"))
    assert len(content_hash_files) == 1

    with patch("app.ingest.parser.DocumentConverter") as mock_converter:
        second = parse_pdf(FIXTURE_PDF, cache_dir=cache_dir)

    mock_converter.assert_not_called()
    assert second == first


@pytest.mark.integration
def test_parse_pdf_does_not_cache_on_conversion_failure(tmp_path: Path):
    cache_dir = tmp_path / "parsed"
    bad_pdf = tmp_path / "not_a_real.pdf"
    bad_pdf.write_bytes(b"not a pdf")

    with pytest.raises(Exception):
        parse_pdf(bad_pdf, cache_dir=cache_dir)

    if cache_dir.exists():
        assert list(cache_dir.glob("*.json")) == []
