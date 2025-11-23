"""add is_verified

Revision ID: 1234567890ab
Revises: e58ebb7f2b9e
Create Date: 2024-05-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1234567890ab'
down_revision = 'e58ebb7f2b9e'
branch_labels = None
depends_on = None


def upgrade():
    # We use a try-except block or just add it. 
    # Since we are manually stamping, this code is for NEW envs.
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_verified', sa.Boolean(), nullable=True, default=False))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_verified')
