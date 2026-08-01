"""Create eval_runs table

Revision ID: 9d0e1f2a3b4c
Revises: 8c1e2f3a4b5c
Create Date: 2026-07-31 09:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "9d0e1f2a3b4c"
down_revision: str | None = "8c1e2f3a4b5c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create eval_runs table."""
    op.create_table(
        "eval_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("judge_provider", sa.String(32), nullable=False),
        sa.Column("judge_model", sa.String(64), nullable=False),
        sa.Column("llm_model", sa.String(64), nullable=True),
        sa.Column("embedding_model", sa.String(64), nullable=True),
        sa.Column("retrieval_top_k", sa.Integer(), nullable=True),
        sa.Column("mmr_lambda", sa.Float(), nullable=True),
        sa.Column("prompt_version", sa.String(32), nullable=True),
        sa.Column("overall", sa.Float(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("results", sa.JSON(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            index=True,
        ),
    )


def downgrade() -> None:
    """Drop eval_runs table."""
    op.drop_table("eval_runs")
