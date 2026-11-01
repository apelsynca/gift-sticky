from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from sticky.kit.database.models import RecordModel

if TYPE_CHECKING:
    from sticky.models.stickers import Sticker


class Gift(RecordModel):
    __tablename__ = "gifts"

    name: Mapped[str]
    telegram_id: Mapped[str] = mapped_column(unique=True)

    sticker: Mapped[Sticker | None] = relationship(
        "Sticker",
        back_populates="gift",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    ignore_as_sticker: Mapped[bool] = mapped_column(default=False)
