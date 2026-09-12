from sticky.kit.repository.main import BaseRepository
from sticky.models import Gift


class GiftRepository(BaseRepository[Gift]):
    model = Gift
