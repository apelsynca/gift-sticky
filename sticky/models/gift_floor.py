from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sticky.kit.database.models import RecordModel

if TYPE_CHECKING:
    from sticky.models.gifts import Gift


class GiftFloor(RecordModel):
    __tablename__ = "gift_floors"
    __table_args__ = (
        Index("ix_gift_floors_gift_id_created_at", "gift_id", "created_at"),
    )

    floor: Mapped[float]

    gift_id: Mapped[UUID] = mapped_column(ForeignKey("gifts.id", ondelete="cascade"))
    gift: Mapped[Gift] = relationship("Gift")
