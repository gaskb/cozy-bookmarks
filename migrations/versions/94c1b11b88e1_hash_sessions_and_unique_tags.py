"""hash_sessions_and_unique_tags

Revision ID: 94c1b11b88e1
Revises: 982a173e4b1c
Create Date: 2026-09-27 04:23:14.409851

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '94c1b11b88e1'
down_revision: str | None = '982a173e4b1c'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # 1. Update sessions table: replace plain-text sessions with hashed token storage
    op.drop_table('sessions')
    op.create_table(
        'sessions',
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('token_hash'),
    )
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)

    # 2. Deduplicate tags if any duplicates exist prior to applying constraint
    op.execute("""
        DELETE FROM tags WHERE id NOT IN (
            SELECT MIN(id) FROM tags GROUP BY user_id, name
        )
    """)

    # 3. Add unique constraint on tags (user_id, name)
    with op.batch_alter_table('tags') as batch_op:
        batch_op.create_unique_constraint('uq_tags_user_id_name', ['user_id', 'name'])


def downgrade() -> None:
    with op.batch_alter_table('tags') as batch_op:
        batch_op.drop_constraint('uq_tags_user_id_name', type_='unique')

    op.drop_table('sessions')
    op.create_table(
        'sessions',
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('token'),
    )
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)
