from sqlalchemy.orm import Mapped, mapped_column

from sticky.kit.database.models import Model


class StickerPack(Model):
    __tablename__ = "sticker_pack"

    name: Mapped[str] = mapped_column(primary_key=True)
