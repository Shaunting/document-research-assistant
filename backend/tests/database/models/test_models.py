from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import DeclarativeBase


def test_base_is_declarative_base():
    from app.database.models.base import Base
    assert issubclass(Base, DeclarativeBase)


def test_timestamp_mixin_declares_timestamp_columns():
    from app.database.models.base import TimestampMixin
    annotations = TimestampMixin.__annotations__
    assert "created_at" in annotations
    assert "updated_at" in annotations


def test_user_table_name():
    from app.database.models.users import User
    assert User.__tablename__ == "users"


def test_user_columns():
    from app.database.models.users import User
    cols = {c.key for c in sa_inspect(User).mapper.column_attrs}
    assert cols == {"id", "email", "created_at", "updated_at"}


def test_user_id_has_no_client_default():
    from app.database.models.users import User
    assert User.__table__.c["id"].default is None


def test_source_document_table_name():
    from app.database.models.source_documents import SourceDocument
    assert SourceDocument.__tablename__ == "source_documents"


def test_source_document_columns():
    from app.database.models.source_documents import SourceDocument
    cols = {c.key for c in sa_inspect(SourceDocument).mapper.column_attrs}
    expected = {
        "id", "ticker", "company", "filing_type", "filing_date",
        "year", "accession_number", "source_url", "content_markdown",
        "created_at", "updated_at",
    }
    assert cols == expected


def test_source_document_id_has_default():
    from app.database.models.source_documents import SourceDocument
    assert SourceDocument.__table__.c["id"].default is not None


def test_document_chunk_table_name():
    from app.database.models.document_chunks import DocumentChunk
    assert DocumentChunk.__tablename__ == "document_chunks"


def test_document_chunk_embedding_is_vector_1536():
    from app.database.models.document_chunks import DocumentChunk
    from pgvector.sqlalchemy import Vector
    col = DocumentChunk.__table__.c["embedding"]
    assert isinstance(col.type, Vector)
    assert col.type.dim == 1536


def test_document_chunk_search_vector_is_computed():
    from app.database.models.document_chunks import DocumentChunk
    assert DocumentChunk.__table__.c["search_vector"].computed is not None


def test_document_chunk_metadata_db_column_name():
    from app.database.models.document_chunks import DocumentChunk
    assert "metadata" in DocumentChunk.__table__.c


def test_document_chunk_fk_to_source_documents():
    from app.database.models.document_chunks import DocumentChunk
    fk_tables = {
        fk.column.table.name
        for fk in DocumentChunk.__table__.c["document_id"].foreign_keys
    }
    assert "source_documents" in fk_tables


def test_chat_thread_table_name():
    from app.database.models.chat_threads import ChatThread
    assert ChatThread.__tablename__ == "chat_threads"


def test_chat_thread_title_is_nullable():
    from app.database.models.chat_threads import ChatThread
    assert ChatThread.__table__.c["title"].nullable is True


def test_chat_thread_fk_to_users():
    from app.database.models.chat_threads import ChatThread
    fk_tables = {
        fk.column.table.name
        for fk in ChatThread.__table__.c["user_id"].foreign_keys
    }
    assert "users" in fk_tables


def test_chat_message_table_name():
    from app.database.models.chat_messages import ChatMessage
    assert ChatMessage.__tablename__ == "chat_messages"


def test_chat_message_columns():
    from app.database.models.chat_messages import ChatMessage
    cols = {c.key for c in sa_inspect(ChatMessage).mapper.column_attrs}
    assert cols == {"id", "thread_id", "role", "content", "message_json", "created_at", "updated_at"}


def test_chat_message_message_json_is_nullable():
    from app.database.models.chat_messages import ChatMessage
    assert ChatMessage.__table__.c["message_json"].nullable is True


def test_chat_message_fk_to_chat_threads():
    from app.database.models.chat_messages import ChatMessage
    fk_tables = {
        fk.column.table.name
        for fk in ChatMessage.__table__.c["thread_id"].foreign_keys
    }
    assert "chat_threads" in fk_tables


def test_message_citation_table_name():
    from app.database.models.message_citations import MessageCitation
    assert MessageCitation.__tablename__ == "message_citations"


def test_message_citation_fk_to_chat_messages():
    from app.database.models.message_citations import MessageCitation
    fk_tables = {
        fk.column.table.name
        for fk in MessageCitation.__table__.c["message_id"].foreign_keys
    }
    assert "chat_messages" in fk_tables


def test_message_citation_fk_to_document_chunks():
    from app.database.models.message_citations import MessageCitation
    fk_tables = {
        fk.column.table.name
        for fk in MessageCitation.__table__.c["chunk_id"].foreign_keys
    }
    assert "document_chunks" in fk_tables


def test_package_exports_all_models():
    from app.database.models import (
        ChatMessage, ChatThread, DocumentChunk,
        MessageCitation, SourceDocument, User,
    )
    for cls in (User, SourceDocument, DocumentChunk, ChatThread, ChatMessage, MessageCitation):
        assert hasattr(cls, "__tablename__")


def test_all_models_registered_on_base():
    from app.database.models import Base
    table_names = set(Base.metadata.tables.keys())
    expected = {
        "users", "source_documents", "document_chunks",
        "chat_threads", "chat_messages", "message_citations",
    }
    assert expected.issubset(table_names)
