"""add_enrichment_status_to_bookmarks

Revision ID: 9614a7be42f9
Revises: 94c1b11b88e1
Create Date: 2026-09-27 04:32:50.974066

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '9614a7be42f9'
down_revision: str | None = '94c1b11b88e1'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('bookmarks') as batch_op:
        batch_op.add_column(
            sa.Column(
                'enrichment_status',
                sa.String(length=20),
                server_default='completed',
                nullable=False,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table('bookmarks') as batch_op:
        batch_op.drop_column('enrichment_status')
