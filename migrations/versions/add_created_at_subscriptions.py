"""Add created_at to subscriptions and align timestamp columns.

Revision ID: c5a9e62a4da2
Revises: 95dea077f473
Create Date: 2025-11-07 11:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "c5a9e62a4da2"
down_revision = "95dea077f473"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("subscriptions")}

    if "created_at" not in columns:
        op.add_column(
            "subscriptions",
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )
        op.execute(sa.text("UPDATE subscriptions SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))

    if bind.dialect.name != "sqlite":
        if "created_at" not in columns:
            op.alter_column(
                "subscriptions",
                "created_at",
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            )

        op.alter_column(
            "users",
            "created_at",
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            existing_server_default=sa.text("(CURRENT_TIMESTAMP)"),
        )

        op.alter_column(
            "weekly_reports",
            "created_at",
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),
        )
        op.alter_column(
            "weekly_reports",
            "delivered_at",
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=True,
        )


def downgrade() -> None:
    op.drop_column("subscriptions", "created_at")

    op.alter_column(
        "users",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        server_default=sa.text("(CURRENT_TIMESTAMP)"),
    )
    op.alter_column(
        "weekly_reports",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )
    op.alter_column(
        "weekly_reports",
        "delivered_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=True,
    )
