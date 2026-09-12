from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sticky.kit.database.models import RecordModel

if TYPE_CHECKING:
    from sticky.models.gifts import Gift


class GiftFloor(RecordModel):
    __tablename__ = "gift_floors"

    floor: Mapped[float]

    gift_id: Mapped[UUID] = mapped_column(ForeignKey("gifts.id"))
    gift: Mapped[Gift] = relationship("Gift")
