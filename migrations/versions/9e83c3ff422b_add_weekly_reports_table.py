from alembic import op
import sqlalchemy as sa


revision = "9e83c3ff422b"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "weekly_reports",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("user_id", sa.String, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("language", sa.String, nullable=False),
        sa.Column("payload", sa.Text, nullable=False),
        sa.Column(
            "delivery_status",
            sa.String,
            server_default="generated",
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_weekly_reports_user_created_at",
        "weekly_reports",
        ["user_id", "created_at"],
    )


def downgrade():
    op.drop_index("ix_weekly_reports_user_created_at", table_name="weekly_reports")
    op.drop_table("weekly_reports")
