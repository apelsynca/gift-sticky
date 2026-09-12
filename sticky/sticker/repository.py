from sticky.kit.repository.main import BaseRepository
from sticky.models import Sticker


class StickerRepository(BaseRepository[Sticker]):
    model = Sticker
