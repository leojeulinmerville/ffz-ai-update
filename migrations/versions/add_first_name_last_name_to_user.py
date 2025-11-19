"""add first_name last_name to user

Revision ID: a1b2c3d4e5f6
Revises: e58ebb7f2b9e
Create Date: 2025-11-19 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'e58ebb7f2b9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('first_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')

