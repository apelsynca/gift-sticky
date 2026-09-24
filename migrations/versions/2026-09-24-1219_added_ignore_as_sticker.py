"""added ignore_as_sticker

Revision ID: f1461aeb9dbe
Revises: 2a3ee47a5d1f
Create Date: 2026-09-24 12:19:26.760854

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1461aeb9dbe"
down_revision: str | Sequence[str] | None = "2a3ee47a5d1f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "gifts",
        sa.Column(
            "ignore_as_sticker", sa.Boolean(), nullable=False, server_default="FALSE"
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("gifts", "ignore_as_sticker")
