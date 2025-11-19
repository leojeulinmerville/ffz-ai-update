"""Add delivery metadata to weekly_reports.

Revision ID: b8f4e5d2a8a7
Revises: 9e83c3ff422b
Create Date: 2025-11-06 19:36:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b8f4e5d2a8a7"
down_revision = "9e83c3ff422b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("weekly_reports", sa.Column("delivery_channel", sa.String(), nullable=True))
    op.add_column("weekly_reports", sa.Column("delivered_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("weekly_reports", "delivered_at")
    op.drop_column("weekly_reports", "delivery_channel")
