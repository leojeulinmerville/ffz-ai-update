from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("email", sa.String, nullable=False, unique=True, index=True),
        sa.Column("password_hash", sa.String, nullable=False),
        sa.Column("language", sa.String, server_default="en"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("(CURRENT_TIMESTAMP)")),
    )
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("user_id", sa.String, sa.ForeignKey("users.id")),
        sa.Column("league", sa.String, nullable=False),
        sa.Column("team", sa.String),
        sa.Column("frequency", sa.String, server_default="weekly"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("1")),
    )

def downgrade():
    op.drop_table("subscriptions")
    op.drop_table("users")
