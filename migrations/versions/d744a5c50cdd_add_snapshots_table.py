"""Create snapshots table

Revision ID: d744a5c50cdd
Revises: c5a9e62a4da2
Create Date: 2025-11-07 12:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "d744a5c50cdd"
down_revision = "c5a9e62a4da2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "snapshots" in inspector.get_table_names():
        return

    op.create_table(
        "snapshots",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("user_id", sa.String, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("league_code", sa.String, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("facts_count", sa.Integer, server_default="0", nullable=False),
        sa.Column("sources_used", sa.JSON, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("payload", sa.JSON, nullable=False),
    )
    op.create_index("ix_snapshots_user_id", "snapshots", ["user_id"])
    op.create_index("ix_snapshots_league_code", "snapshots", ["league_code"])
    op.create_index("ix_snapshots_created_at", "snapshots", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_snapshots_created_at", table_name="snapshots")
    op.drop_index("ix_snapshots_league_code", table_name="snapshots")
    op.drop_index("ix_snapshots_user_id", table_name="snapshots")
    op.drop_table("snapshots")
