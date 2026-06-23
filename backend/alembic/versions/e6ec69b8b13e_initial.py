"""initial

Revision ID: e6ec69b8b13e
Revises:
Create Date: 2026-06-21 21:35:49.524394

"""
from typing import Sequence, Union

import pgvector.sqlalchemy.vector
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e6ec69b8b13e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table('source_documents',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('ticker', sa.String(), nullable=False),
    sa.Column('company', sa.String(), nullable=False),
    sa.Column('filing_type', sa.String(), nullable=False),
    sa.Column('filing_date', sa.Date(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('accession_number', sa.String(), nullable=False),
    sa.Column('source_url', sa.String(), nullable=False),
    sa.Column('content_markdown', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('chat_threads',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('document_chunks',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('document_id', sa.UUID(), nullable=False),
    sa.Column('chunk_index', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('token_count', sa.Integer(), nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=1536), nullable=True),
    sa.Column('search_vector', postgresql.TSVECTOR(), sa.Computed("to_tsvector('english', text)", persisted=True), nullable=True),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['source_documents.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('chat_messages',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('thread_id', sa.UUID(), nullable=False),
    sa.Column('role', sa.String(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('message_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['thread_id'], ['chat_threads.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('message_citations',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('message_id', sa.UUID(), nullable=False),
    sa.Column('chunk_id', sa.UUID(), nullable=False),
    sa.Column('quote', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['chunk_id'], ['document_chunks.id'], ),
    sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # HNSW index for vector similarity search
    op.execute("""
        CREATE INDEX document_chunks_embedding_idx
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
    """)

    # GIN index for full-text search
    op.execute("""
        CREATE INDEX document_chunks_search_vector_idx
        ON document_chunks
        USING gin (search_vector)
    """)

    # GIN index for metadata JSON queries
    op.execute("""
        CREATE INDEX document_chunks_metadata_idx
        ON document_chunks
        USING gin (metadata)
    """)

    # RLS — users see only their own chat data
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE chat_threads ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE message_citations ENABLE ROW LEVEL SECURITY")

    op.execute("""
        CREATE POLICY users_own_profile ON users
        FOR ALL USING (id = auth.uid())
    """)
    op.execute("""
        CREATE POLICY users_own_threads ON chat_threads
        FOR ALL USING (user_id = auth.uid())
    """)
    op.execute("""
        CREATE POLICY users_own_messages ON chat_messages
        FOR ALL USING (
            thread_id IN (SELECT id FROM chat_threads WHERE user_id = auth.uid())
        )
    """)
    op.execute("""
        CREATE POLICY users_own_citations ON message_citations
        FOR ALL USING (
            message_id IN (
                SELECT cm.id FROM chat_messages cm
                JOIN chat_threads ct ON cm.thread_id = ct.id
                WHERE ct.user_id = auth.uid()
            )
        )
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS users_own_citations ON message_citations")
    op.execute("DROP POLICY IF EXISTS users_own_messages ON chat_messages")
    op.execute("DROP POLICY IF EXISTS users_own_threads ON chat_threads")
    op.execute("DROP POLICY IF EXISTS users_own_profile ON users")

    op.drop_table('message_citations')
    op.drop_table('chat_messages')
    op.drop_table('document_chunks')
    op.drop_table('chat_threads')
    op.drop_table('users')
    op.drop_table('source_documents')
