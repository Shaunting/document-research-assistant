import uuid
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.chunks import replace_document_chunks
from app.database.engine import get_engine
from app.database.models.document_chunks import ChunkType as OrmChunkType
from app.database.models.document_chunks import DocumentChunk
from app.database.models.source_documents import SourceDocument
from app.ingestion.chunking.chunker import chunk_document
from app.ingestion.chunking.schemas import Chunk
from app.ingestion.parsing.schemas import ChunkType, ParsedDocument

pytestmark = pytest.mark.integration

FIXTURE_PATH = sorted(
    (Path(__file__).parents[3] / "data" / "papers" / "parsed").glob("*.json")
)[0]


@pytest.fixture
def db_session():
    engine = get_engine()
    session = Session(bind=engine)
    yield session
    session.rollback()
    session.close()
    engine.dispose()


def _new_source_document(**overrides) -> SourceDocument:
    defaults = dict(
        title="Test Paper",
        authors=["Ada Lovelace"],
        year=2026,
        filename=f"test-{uuid.uuid4().hex}.pdf",
        source_path="data/papers/test.pdf",
        content_markdown="# Test",
        content_hash=uuid.uuid4().hex,
    )
    defaults.update(overrides)
    return SourceDocument(**defaults)


def _sample_chunk(index: int, text: str = "body") -> Chunk:
    return Chunk(
        chunk_index=index,
        text=text,
        token_count=1,
        page_start=1,
        page_end=1,
        section_path="Methods",
        chunk_type=ChunkType.TEXT,
        metadata={"chunking_config_version": "v1"},
    )


def test_replace_document_chunks_inserts_fresh_rows(db_session):
    doc = _new_source_document()
    db_session.add(doc)
    db_session.commit()

    replace_document_chunks(db_session, doc.id, [_sample_chunk(0), _sample_chunk(1)])

    rows = db_session.scalars(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    ).all()
    assert len(rows) == 2
    assert {r.chunk_index for r in rows} == {0, 1}

    db_session.delete(doc)
    db_session.commit()


def test_replace_document_chunks_deletes_old_rows_first(db_session):
    doc = _new_source_document()
    db_session.add(doc)
    db_session.commit()

    replace_document_chunks(db_session, doc.id, [_sample_chunk(0, text="old")])
    replace_document_chunks(db_session, doc.id, [_sample_chunk(0, text="new")])

    rows = db_session.scalars(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    ).all()
    assert len(rows) == 1
    assert rows[0].text == "new"

    db_session.delete(doc)
    db_session.commit()


def test_replace_document_chunks_rolls_back_on_failure(db_session):
    doc = _new_source_document()
    db_session.add(doc)
    db_session.commit()

    replace_document_chunks(db_session, doc.id, [_sample_chunk(0, text="original")])

    # Duplicate chunk_index violates the unique constraint, forcing the insert half to fail.
    with pytest.raises(Exception):
        replace_document_chunks(
            db_session, doc.id, [_sample_chunk(0, text="a"), _sample_chunk(0, text="b")]
        )
    db_session.rollback()

    rows = db_session.scalars(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    ).all()
    assert len(rows) == 1
    assert rows[0].text == "original"

    db_session.delete(doc)
    db_session.commit()


def test_persisted_chunk_type_matches_orm_enum(db_session):
    doc = _new_source_document()
    db_session.add(doc)
    db_session.commit()

    replace_document_chunks(db_session, doc.id, [_sample_chunk(0)])

    row = db_session.scalars(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    ).one()
    assert row.chunk_type == OrmChunkType.TEXT

    db_session.delete(doc)
    db_session.commit()


def test_real_chunk_document_output_round_trips_through_replace_document_chunks(db_session):
    # Closes the seam between chunk_document() and replace_document_chunks():
    # both are tested in isolation elsewhere, but nothing exercises real
    # chunker output flowing through persistence, so a future Chunk field
    # addition, an oversized section_path, or enum-value drift wouldn't be
    # caught by either test file alone.
    parsed = ParsedDocument.model_validate_json(FIXTURE_PATH.read_text())
    chunks = chunk_document(parsed)
    doc = _new_source_document()
    db_session.add(doc)
    db_session.commit()

    replace_document_chunks(db_session, doc.id, chunks)

    rows = db_session.scalars(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == doc.id)
        .order_by(DocumentChunk.chunk_index)
    ).all()
    assert len(rows) == len(chunks)
    assert rows[0].text == chunks[0].text
    assert rows[0].token_count == chunks[0].token_count
    assert rows[0].chunk_type == OrmChunkType(chunks[0].chunk_type.value)
    assert rows[-1].text == chunks[-1].text
    assert rows[-1].token_count == chunks[-1].token_count
    assert rows[-1].chunk_type == OrmChunkType(chunks[-1].chunk_type.value)

    db_session.delete(doc)
    db_session.commit()
