from sticky.sticker_generator.main import StickerGenerator
from sticky.sticker_generator.types import StickerPayload

generator = StickerGenerator()

GENERATIONS_PATH = "generations"

__all__ = ["GENERATIONS_PATH", "StickerGenerator", "StickerPayload", "generator"]
