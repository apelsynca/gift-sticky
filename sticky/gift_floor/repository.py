from sticky.kit.repository.main import BaseRepository
from sticky.models import GiftFloor


class GiftFloorRepository(BaseRepository[GiftFloor]):
    model = GiftFloor
