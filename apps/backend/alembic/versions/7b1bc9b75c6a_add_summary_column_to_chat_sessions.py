"""Add summary column to chat_sessions

Revision ID: 7b1bc9b75c6a
Revises: 4d1e8f2a6c3b
Create Date: 2026-07-29 22:07:38.460052
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "7b1bc9b75c6a"
down_revision: str | None = "4d1e8f2a6c3b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade: add summary column to chat_sessions."""
    op.add_column("chat_sessions", sa.Column("summary", sa.VARCHAR, nullable=True))


def downgrade() -> None:
    """Downgrade: remove summary column from chat_sessions."""
    op.drop_column("chat_sessions", "summary")
