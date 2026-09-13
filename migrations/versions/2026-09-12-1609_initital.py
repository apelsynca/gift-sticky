"""initital

Revision ID: 2a3ee47a5d1f
Revises:
Create Date: 2026-09-12 16:09:14.522029

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2a3ee47a5d1f"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "gifts",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("telegram_id", sa.String(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index(op.f("ix_gifts_created_at"), "gifts", ["created_at"], unique=False)
    op.create_table(
        "sticker_pack",
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("name"),
    )
    op.create_table(
        "gift_floors",
        sa.Column("floor", sa.Float(), nullable=False),
        sa.Column("gift_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["gift_id"],
            ["gifts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_gift_floors_created_at"), "gift_floors", ["created_at"], unique=False
    )
    op.create_table(
        "stickers",
        sa.Column("gift_id", sa.Uuid(), nullable=False),
        sa.Column("file", sa.String(), nullable=False),
        sa.Column("emojis", sa.String(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["gift_id"], ["gifts.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("gift_id"),
    )
    op.create_index(
        op.f("ix_stickers_created_at"), "stickers", ["created_at"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_stickers_created_at"), table_name="stickers")
    op.drop_table("stickers")
    op.drop_index(op.f("ix_gift_floors_created_at"), table_name="gift_floors")
    op.drop_table("gift_floors")
    op.drop_table("sticker_pack")
    op.drop_index(op.f("ix_gifts_created_at"), table_name="gifts")
    op.drop_table("gifts")
