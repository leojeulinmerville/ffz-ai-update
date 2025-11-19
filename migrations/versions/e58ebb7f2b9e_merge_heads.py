"""merge heads

Revision ID: e58ebb7f2b9e
Revises: 6b8e1f2a2a4d, d744a5c50cdd
Create Date: 2025-11-12 12:13:49.835166

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e58ebb7f2b9e'
down_revision: Union[str, None] = ('6b8e1f2a2a4d', 'd744a5c50cdd')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
