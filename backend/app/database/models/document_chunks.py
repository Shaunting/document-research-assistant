import uuid
from enum import Enum
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    Computed,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base, TimestampMixin


class ChunkType(str, Enum):
    TEXT = "text"
    TABLE = "table"


class DocumentChunk(TimestampMixin, Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "chunk_index", name="document_chunks_document_index_unique"
        ),
        CheckConstraint(
            "page_end >= page_start", name="document_chunks_page_range_valid"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    page_start: Mapped[int] = mapped_column(Integer, nullable=False)
    page_end: Mapped[int] = mapped_column(Integer, nullable=False)
    section_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_type: Mapped[ChunkType] = mapped_column(
        SAEnum(
            ChunkType,
            name="chunk_type",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
        default=ChunkType.TEXT,
        server_default=ChunkType.TEXT.value,
    )
    embedding: Mapped[Any] = mapped_column(Vector(1536), nullable=True)
    search_vector: Mapped[Any] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', text)", persisted=True),
        nullable=True,
    )
    metadata_: Mapped[Any] = mapped_column("metadata", JSONB, nullable=True)
