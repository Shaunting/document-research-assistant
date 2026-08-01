"""research paper source_documents

Revision ID: f3a8c2d91e04
Revises: e6ec69b8b13e
Create Date: 2026-06-30 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f3a8c2d91e04"
down_revision: Union[str, Sequence[str], None] = "e6ec69b8b13e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("source_documents", "ticker")
    op.drop_column("source_documents", "company")
    op.drop_column("source_documents", "filing_type")
    op.drop_column("source_documents", "filing_date")
    op.drop_column("source_documents", "accession_number")
    op.drop_column("source_documents", "source_url")

    op.add_column("source_documents", sa.Column("title", sa.Text(), nullable=False))
    op.add_column(
        "source_documents",
        sa.Column("authors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.add_column("source_documents", sa.Column("filename", sa.String(), nullable=False))
    op.add_column("source_documents", sa.Column("source_path", sa.Text(), nullable=False))
    op.add_column("source_documents", sa.Column("content_hash", sa.String(), nullable=True))
    op.add_column(
        "source_documents",
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.create_unique_constraint(
        "source_documents_filename_key", "source_documents", ["filename"]
    )


def downgrade() -> None:
    op.drop_constraint("source_documents_filename_key", "source_documents", type_="unique")

    op.drop_column("source_documents", "tags")
    op.drop_column("source_documents", "content_hash")
    op.drop_column("source_documents", "source_path")
    op.drop_column("source_documents", "filename")
    op.drop_column("source_documents", "authors")
    op.drop_column("source_documents", "title")

    op.add_column("source_documents", sa.Column("source_url", sa.String(), nullable=False))
    op.add_column(
        "source_documents", sa.Column("accession_number", sa.String(), nullable=False)
    )
    op.add_column("source_documents", sa.Column("filing_date", sa.Date(), nullable=False))
    op.add_column("source_documents", sa.Column("filing_type", sa.String(), nullable=False))
    op.add_column("source_documents", sa.Column("company", sa.String(), nullable=False))
    op.add_column("source_documents", sa.Column("ticker", sa.String(), nullable=False))
