import asyncio
import io
from enum import StrEnum
from typing import NamedTuple

import aiohttp
import structlog
from gchanges import GiftChanges
from PIL import Image, ImageDraw
from pydantic import BaseModel

from sticky.logging import Logger

log: Logger = structlog.get_logger()


class GiftImageSettings(NamedTuple):
    size: int

    @property
    def box_size(self) -> tuple[int, int]:
        return self.size, self.size


class StickerTemplates(StrEnum):
    neutral = "neutral"
    positive = "positive"
    negative = "negative"

    @property
    def path(self) -> str:
        filename = {
            StickerTemplates.neutral: "bg_neutral.png",
            StickerTemplates.positive: "bg_positive.png",
            StickerTemplates.negative: "bg_negative.png",
        }[self]
        return f"templates/{filename}"


class StickerSettings(BaseModel):
    template: StickerTemplates


class ImageGenerator:
    def __init__(self) -> None:
        self.changes = GiftChanges()

    def run(self) -> None:
        """Starts async loop or smth"""
        asyncio.run(self.start())

    async def start(self) -> None:
        names = await self.changes.get_names()

        await self.generate_for_gift(name="Signet Ring", gift_id="5936085638515261992")

        # for name, id in names.items():
        #     await self.generate_for_gift(name, id)

    async def generate_for_gift(self, name: str, gift_id: str) -> None:
        log.debug("Generating sticker for gift", name=name, id=gift_id)

        settings = StickerSettings(template=StickerTemplates.positive)

        canvas_image = Image.open(settings.template.path)
        await self._put_gift_image_on_sticker(gift_id=gift_id, canvas_image=canvas_image)

        draw = ImageDraw.Draw(canvas_image)

        canvas_image.show()

    async def _put_gift_image_on_sticker(
        self, gift_id, canvas_image: Image.Image
    ) -> Image.Image:
        session = aiohttp.ClientSession()
        gim_settings = GiftImageSettings(size=1024)

        async with session:
            response = await session.get(
                url=f"https://api.changes.tg/original/{gift_id}.png?size={gim_settings.size}"
            )
            image_bytes = await response.read()

            gift_image = Image.open(io.BytesIO(image_bytes))
            gift_image = gift_image.resize(size=(228, 228))

        canvas_image.paste(
            im=gift_image, box=(142, 66), mask=gift_image
        )  # 142 x, 66 y (upper); 142 x, 218 y (down);
        return canvas_image


generator = ImageGenerator()
