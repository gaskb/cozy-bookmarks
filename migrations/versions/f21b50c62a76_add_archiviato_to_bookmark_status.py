"""add_archiviato_to_bookmark_status

Revision ID: f21b50c62a76
Revises: 66a8d43b8113
Create Date: 2026-09-22 09:16:56.510421

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'f21b50c62a76'
down_revision: str | None = '66a8d43b8113'
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("bookmarks") as batch_op:
        batch_op.alter_column(
            "status",
            type_=sa.Enum("da_organizzare", "organizzato", "archiviato", name="bookmarkstatus"),
            existing_type=sa.Enum("da_organizzare", "organizzato", name="bookmarkstatus"),
            nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("bookmarks") as batch_op:
        batch_op.alter_column(
            "status",
            type_=sa.Enum("da_organizzare", "organizzato", name="bookmarkstatus"),
            existing_type=sa.Enum("da_organizzare", "organizzato", "archiviato", name="bookmarkstatus"),
            nullable=False,
        )

