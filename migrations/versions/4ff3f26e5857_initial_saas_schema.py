"""Initial SaaS schema

Revision ID: 4ff3f26e5857
Revises: 
Create Date: 2025-11-27 14:21:47.262532

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '4ff3f26e5857'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create all tables
    op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('favorite_team', sa.String(), nullable=True),
        sa.Column('phone_number', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stripe_customer_id', sa.String(), nullable=True),
        sa.Column('subscription_status', sa.String(), nullable=True),
        sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tone', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table('subscriptions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('league', sa.String(), nullable=False),
        sa.Column('team', sa.String(), nullable=True),
        sa.Column('frequency', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscriptions_user_id'), 'subscriptions', ['user_id'], unique=False)

    op.create_table('matches',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('league_code', sa.String(), nullable=False),
        sa.Column('home_team', sa.String(), nullable=False),
        sa.Column('away_team', sa.String(), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('score_home', sa.Integer(), nullable=True),
        sa.Column('score_away', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_matches_league_code'), 'matches', ['league_code'], unique=False)
    op.create_index(op.f('ix_matches_home_team'), 'matches', ['home_team'], unique=False)
    op.create_index(op.f('ix_matches_away_team'), 'matches', ['away_team'], unique=False)

    op.create_table('match_facts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('match_id', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('stats', sa.JSON(), nullable=True),
        sa.Column('key_events', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_match_facts_match_id'), 'match_facts', ['match_id'], unique=False)

    op.create_table('reports',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_user_id'), 'reports', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_reports_user_id'), table_name='reports')
    op.drop_table('reports')
    op.drop_index(op.f('ix_match_facts_match_id'), table_name='match_facts')
    op.drop_table('match_facts')
    op.drop_index(op.f('ix_matches_away_team'), table_name='matches')
    op.drop_index(op.f('ix_matches_home_team'), table_name='matches')
    op.drop_index(op.f('ix_matches_league_code'), table_name='matches')
    op.drop_table('matches')
    op.drop_index(op.f('ix_subscriptions_user_id'), table_name='subscriptions')
    op.drop_table('subscriptions')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
