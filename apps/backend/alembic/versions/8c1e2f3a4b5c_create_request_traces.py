"""Create request_traces table

Revision ID: 8c1e2f3a4b5c
Revises: 7b1bc9b75c6a
Create Date: 2026-07-31 09:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "8c1e2f3a4b5c"
down_revision: str | None = "7b1bc9b75c6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create request_traces table."""
    op.create_table(
        "request_traces",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("request_id", sa.String(32), nullable=False, index=True),
        sa.Column("user_id", sa.String(36), nullable=True, index=True),
        sa.Column("session_id", sa.String(36), nullable=True, index=True),
        sa.Column("prompt_version", sa.String(32), nullable=True, index=True),
        sa.Column("prompt_hash", sa.String(32), nullable=True),
        sa.Column("model", sa.String(64), nullable=True),
        sa.Column("provider", sa.String(32), nullable=True),
        sa.Column("cache_hit", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("stages", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("counts", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            index=True,
        ),
    )


def downgrade() -> None:
    """Drop request_traces table."""
    op.drop_table("request_traces")
