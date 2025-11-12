"""add phone number to users

Revision ID: 6b8e1f2a2a4d
Revises: 95dea077f473
Create Date: 2025-11-06 21:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "6b8e1f2a2a4d"
down_revision = "95dea077f473"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone_number", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "phone_number")
