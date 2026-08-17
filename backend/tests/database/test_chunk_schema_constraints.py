import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.database.models.document_chunks import ChunkType, DocumentChunk
from app.database.models.source_documents import SourceDocument

pytestmark = pytest.mark.integration


def _engine():
    db_url = settings.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(db_url)


@pytest.fixture
def db_session():
    engine = _engine()
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


def test_chunk_type_defaults_to_text(db_session):
    doc = _new_source_document()
    db_session.add(doc)
    db_session.commit()

    chunk = DocumentChunk(
        document_id=doc.id,
        chunk_index=0,
        text="hello",
        token_count=1,
        page_start=1,
        page_end=1,
    )
    db_session.add(chunk)
    db_session.commit()
    db_session.refresh(chunk)

    assert chunk.chunk_type == ChunkType.TEXT

    db_session.delete(doc)
    db_session.commit()


def test_chunk_requires_page_start_and_page_end(db_session):
    doc = _new_source_document()
    db_session.add(doc)
    db_session.commit()

    db_session.add(
        DocumentChunk(document_id=doc.id, chunk_index=0, text="hello", token_count=1)
    )
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()
    db_session.delete(doc)
    db_session.commit()


def test_duplicate_chunk_index_for_same_document_is_rejected(db_session):
    doc = _new_source_document()
    db_session.add(doc)
    db_session.commit()

    db_session.add(
        DocumentChunk(
            document_id=doc.id, chunk_index=0, text="a", token_count=1,
            page_start=1, page_end=1,
        )
    )
    db_session.commit()

    db_session.add(
        DocumentChunk(
            document_id=doc.id, chunk_index=0, text="b", token_count=1,
            page_start=1, page_end=1,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()
    db_session.delete(doc)
    db_session.commit()


def test_deleting_source_document_cascades_to_chunks(db_session):
    doc = _new_source_document()
    db_session.add(doc)
    db_session.commit()

    chunk = DocumentChunk(
        document_id=doc.id, chunk_index=0, text="a", token_count=1,
        page_start=1, page_end=1,
    )
    db_session.add(chunk)
    db_session.commit()
    chunk_id = chunk.id

    db_session.delete(doc)
    db_session.commit()

    assert db_session.get(DocumentChunk, chunk_id) is None


def test_duplicate_content_hash_is_rejected(db_session):
    shared_hash = uuid.uuid4().hex
    doc1 = _new_source_document(content_hash=shared_hash)
    db_session.add(doc1)
    db_session.commit()

    db_session.add(_new_source_document(content_hash=shared_hash))
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()
    db_session.delete(doc1)
    db_session.commit()
