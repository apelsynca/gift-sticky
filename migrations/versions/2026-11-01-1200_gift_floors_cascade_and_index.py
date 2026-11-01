"""gift_floors cascade and index

Revision ID: 7c2e9d41b6a3
Revises: f1461aeb9dbe
Create Date: 2026-11-01 12:00:00.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7c2e9d41b6a3"
down_revision: str | Sequence[str] | None = "f1461aeb9dbe"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("gift_floors_gift_id_fkey", "gift_floors", type_="foreignkey")
    op.create_foreign_key(
        "gift_floors_gift_id_fkey",
        "gift_floors",
        "gifts",
        ["gift_id"],
        ["id"],
        ondelete="cascade",
    )
    op.create_index(
        "ix_gift_floors_gift_id_created_at",
        "gift_floors",
        ["gift_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_gift_floors_gift_id_created_at", table_name="gift_floors")
    op.drop_constraint("gift_floors_gift_id_fkey", "gift_floors", type_="foreignkey")
    op.create_foreign_key(
        "gift_floors_gift_id_fkey", "gift_floors", "gifts", ["gift_id"], ["id"]
    )
