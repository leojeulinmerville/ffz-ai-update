from alembic import op
import sqlalchemy as sa


revision = "3e7c0d8fd8b3"
down_revision = "9e83c3ff422b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("favorite_team", sa.String(), nullable=True))


def downgrade():
    op.drop_column("users", "favorite_team")
