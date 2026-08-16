from pathlib import Path

from app.ingest.cache import hash_file, load_cached, write_cache
from app.ingest.schemas import Block, ChunkType, ParsedDocument


def _sample_doc() -> ParsedDocument:
    return ParsedDocument(
        markdown="# Title",
        page_count=1,
        blocks=[
            Block(
                text="Body",
                block_type=ChunkType.TEXT,
                page_start=1,
                page_end=1,
                section_path="",
            )
        ],
    )


def test_hash_file_is_deterministic_and_content_sensitive(tmp_path: Path):
    file_a = tmp_path / "a.pdf"
    file_a.write_bytes(b"same bytes")
    file_b = tmp_path / "b.pdf"
    file_b.write_bytes(b"same bytes")
    file_c = tmp_path / "c.pdf"
    file_c.write_bytes(b"different bytes")

    assert hash_file(file_a) == hash_file(file_b)
    assert hash_file(file_a) != hash_file(file_c)


def test_load_cached_returns_none_when_missing(tmp_path: Path):
    assert load_cached("deadbeef", cache_dir=tmp_path) is None


def test_write_then_load_round_trips(tmp_path: Path):
    doc = _sample_doc()
    write_cache("deadbeef", doc, cache_dir=tmp_path)

    loaded = load_cached("deadbeef", cache_dir=tmp_path)

    assert loaded == doc


def test_write_cache_creates_cache_dir_if_missing(tmp_path: Path):
    cache_dir = tmp_path / "nested" / "parsed"
    write_cache("deadbeef", _sample_doc(), cache_dir=cache_dir)

    assert (cache_dir / "deadbeef.json").exists()
