from sticky.sticker_renderer.main import StickerRenderer
from sticky.sticker_renderer.types import StickerPayload

renderer = StickerRenderer()

GENERATIONS_PATH = "generations"

__all__ = ["GENERATIONS_PATH", "StickerPayload", "StickerRenderer", "renderer"]
