"""Add owner_id to reports and collections (cross-tenant tenancy).

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "reports",
        sa.Column("owner_id", sa.String(length=36), nullable=True),
    )
    op.create_index("ix_reports_owner_id", "reports", ["owner_id"])

    op.add_column(
        "collections",
        sa.Column("owner_id", sa.String(length=36), nullable=True),
    )
    op.create_index("ix_collections_owner_id", "collections", ["owner_id"])

    # Backfill: claim all existing rows for the earliest registered user
    # (in practice the single operator of this deployment). Cross-db safe —
    # we read the id in Python and bind it back as a string.
    conn = op.get_bind()
    first_user = conn.execute(
        sa.text("SELECT id FROM users ORDER BY created_at ASC LIMIT 1")
    ).scalar()
    if first_user is not None:
        owner = str(first_user)
        conn.execute(sa.text("UPDATE reports SET owner_id = :oid"), {"oid": owner})
        conn.execute(sa.text("UPDATE collections SET owner_id = :oid"), {"oid": owner})


def downgrade() -> None:
    op.drop_index("ix_collections_owner_id", table_name="collections")
    op.drop_column("collections", "owner_id")
    op.drop_index("ix_reports_owner_id", table_name="reports")
    op.drop_column("reports", "owner_id")
