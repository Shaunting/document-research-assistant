"""chunk schema reconciliation

Revision ID: 8f3d2c7b9e41
Revises: 21186b4cfb49
Create Date: 2026-08-17 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8f3d2c7b9e41'
down_revision: Union[str, Sequence[str], None] = '21186b4cfb49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE chunk_type AS ENUM ('text', 'table')")

    op.add_column("source_documents", sa.Column("page_count", sa.Integer(), nullable=True))
    op.alter_column(
        "source_documents", "content_hash", existing_type=sa.String(), nullable=False
    )
    op.create_unique_constraint(
        "source_documents_content_hash_key", "source_documents", ["content_hash"]
    )

    op.add_column("document_chunks", sa.Column("page_start", sa.Integer(), nullable=False))
    op.add_column("document_chunks", sa.Column("page_end", sa.Integer(), nullable=False))
    op.add_column("document_chunks", sa.Column("section_path", sa.Text(), nullable=True))
    op.add_column(
        "document_chunks",
        sa.Column(
            "chunk_type",
            postgresql.ENUM("text", "table", name="chunk_type", create_type=False),
            nullable=False,
            server_default="text",
        ),
    )
    op.create_check_constraint(
        "document_chunks_page_range_valid", "document_chunks", "page_end >= page_start"
    )
    op.create_unique_constraint(
        "document_chunks_document_index_unique",
        "document_chunks",
        ["document_id", "chunk_index"],
    )

    op.drop_constraint(
        "document_chunks_document_id_fkey", "document_chunks", type_="foreignkey"
    )
    op.create_foreign_key(
        "document_chunks_document_id_fkey",
        "document_chunks",
        "source_documents",
        ["document_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "message_citations_chunk_id_fkey", "message_citations", type_="foreignkey"
    )
    op.create_foreign_key(
        "message_citations_chunk_id_fkey",
        "message_citations",
        "document_chunks",
        ["chunk_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "message_citations_chunk_id_fkey", "message_citations", type_="foreignkey"
    )
    op.create_foreign_key(
        "message_citations_chunk_id_fkey",
        "message_citations",
        "document_chunks",
        ["chunk_id"],
        ["id"],
    )

    op.drop_constraint(
        "document_chunks_document_id_fkey", "document_chunks", type_="foreignkey"
    )
    op.create_foreign_key(
        "document_chunks_document_id_fkey",
        "document_chunks",
        "source_documents",
        ["document_id"],
        ["id"],
    )

    op.drop_constraint(
        "document_chunks_document_index_unique", "document_chunks", type_="unique"
    )
    op.drop_constraint("document_chunks_page_range_valid", "document_chunks", type_="check")
    op.drop_column("document_chunks", "chunk_type")
    op.drop_column("document_chunks", "section_path")
    op.drop_column("document_chunks", "page_end")
    op.drop_column("document_chunks", "page_start")

    op.drop_constraint("source_documents_content_hash_key", "source_documents", type_="unique")
    op.alter_column(
        "source_documents", "content_hash", existing_type=sa.String(), nullable=True
    )
    op.drop_column("source_documents", "page_count")

    op.execute("DROP TYPE chunk_type")
