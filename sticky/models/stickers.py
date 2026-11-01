from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sticky.kit.database.models import RecordModel

if TYPE_CHECKING:
    from sticky.models.gifts import Gift


class Sticker(RecordModel):
    __tablename__ = "stickers"

    gift_id: Mapped[UUID] = mapped_column(
        ForeignKey("gifts.id", ondelete="cascade"), unique=True
    )
    gift: Mapped[Gift] = relationship("Gift", back_populates="sticker")

    file: Mapped[str]  # can be a URL to file or file_id -? unsure check
    emojis: Mapped[str] = mapped_column(String)  # whitespace-separated emojis
