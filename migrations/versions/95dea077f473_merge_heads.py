"""merge heads

Revision ID: 95dea077f473
Revises: 3e7c0d8fd8b3, b8f4e5d2a8a7
Create Date: 2025-11-06 20:12:39
"""

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401


revision = "95dea077f473"
down_revision = ("3e7c0d8fd8b3", "b8f4e5d2a8a7")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
