"""add server default uuid generation for chat tables

Revision ID: 21186b4cfb49
Revises: f3a8c2d91e04
Create Date: 2026-08-02 13:26:02.303821

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21186b4cfb49'
down_revision: Union[str, Sequence[str], None] = 'f3a8c2d91e04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'chat_threads', 'id',
        server_default=sa.text('gen_random_uuid()'),
    )
    op.alter_column(
        'chat_messages', 'id',
        server_default=sa.text('gen_random_uuid()'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('chat_messages', 'id', server_default=None)
    op.alter_column('chat_threads', 'id', server_default=None)
