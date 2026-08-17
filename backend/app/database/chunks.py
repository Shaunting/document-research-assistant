import uuid

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.database.models.document_chunks import ChunkType as OrmChunkType
from app.database.models.document_chunks import DocumentChunk
from app.ingestion.chunking.schemas import Chunk


def _to_orm(document_id: uuid.UUID, chunk: Chunk) -> DocumentChunk:
    return DocumentChunk(
        document_id=document_id,
        chunk_index=chunk.chunk_index,
        text=chunk.text,
        token_count=chunk.token_count,
        page_start=chunk.page_start,
        page_end=chunk.page_end,
        section_path=chunk.section_path,
        chunk_type=OrmChunkType(chunk.chunk_type.value),
        metadata_=chunk.metadata,
    )


def replace_document_chunks(
    session: Session, document_id: uuid.UUID, chunks: list[Chunk]
) -> None:
    """Delete all existing chunks for `document_id` and insert `chunks` in their place, atomically.

    Note: passing an empty `chunks` list deletes all existing chunks for
    `document_id` without inserting replacements -- call sites should guard
    against this if that's not intended (`chunk_document()` itself raises on
    empty input, but this function is independently callable and does not).
    """
    # Note: we deliberately avoid `with session.begin():` here. SQLAlchemy's
    # Session autobegins a transaction on first use (e.g. simply resolving an
    # expired attribute like `document_id` before this function is even
    # called), so `session.begin()` can raise "A transaction is already begun
    # on this Session." We instead rely on that autobegun transaction (or
    # start one implicitly via the first `execute()` below) and drive it to
    # completion ourselves: delete + insert are flushed together by
    # `commit()`, so they succeed or fail as one atomic unit, and any failure
    # rolls back both before re-raising.
    try:
        session.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        session.add_all(_to_orm(document_id, chunk) for chunk in chunks)
        session.commit()
    except Exception:
        session.rollback()
        raise
