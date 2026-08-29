"""add position column to bookmarks

Revision ID: 8856ee9a9f1d
Revises: 067e5e4a8d7c
Create Date: 2026-08-30 00:30:12.657105

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '8856ee9a9f1d'
down_revision: str | None = '067e5e4a8d7c'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

POSITION_GAP = 1000.0


def upgrade() -> None:
    op.add_column(
        'bookmarks',
        sa.Column('position', sa.Float(), nullable=False, server_default='0'),
    )

    # Backfill existing rows so manual ordering starts out matching today's
    # created_at DESC display order - without this, everyone's bookmarks
    # would all start at position 0 and sort arbitrarily on first load.
    conn = op.get_bind()
    user_ids = conn.execute(sa.text("SELECT DISTINCT user_id FROM bookmarks")).scalars().all()
    for user_id in user_ids:
        bookmark_ids = (
            conn.execute(
                sa.text("SELECT id FROM bookmarks WHERE user_id = :uid ORDER BY created_at ASC"),
                {"uid": user_id},
            )
            .scalars()
            .all()
        )
        for index, bookmark_id in enumerate(bookmark_ids):
            conn.execute(
                sa.text("UPDATE bookmarks SET position = :pos WHERE id = :id"),
                {"pos": (index + 1) * POSITION_GAP, "id": bookmark_id},
            )


def downgrade() -> None:
    op.drop_column('bookmarks', 'position')
