"""Add preferences JSON column to users table

Revision ID: 2b4c1e9d7a3f
Revises: 782274bc742a
Create Date: 2026-07-14 21:55:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2b4c1e9d7a3f"
down_revision: str | None = "782274bc742a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add preferences JSONB column to users table."""
    # Use raw SQL to handle SQLite vs PostgreSQL gracefully
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.add_column(
            "users",
            sa.Column(
                "preferences",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text(
                    "'{\"chunking_strategy\": \"heading_aware\", "
                    "\"llm_provider\": \"ollama\", "
                    "\"retrieval_strategy\": \"hybrid\", "
                    "\"embedding_provider\": \"sentence_transformer\"}'::jsonb"
                ),
            ),
        )
    else:
        op.add_column(
            "users",
            sa.Column(
                "preferences",
                sa.Text(),
                nullable=False,
                server_default=sa.text(
                    "'{\"chunking_strategy\": \"heading_aware\", "
                    "\"llm_provider\": \"ollama\", "
                    "\"retrieval_strategy\": \"hybrid\", "
                    "\"embedding_provider\": \"sentence_transformer\"}'"
                ),
            ),
        )


def downgrade() -> None:
    """Drop preferences column."""
    op.drop_column("users", "preferences")
