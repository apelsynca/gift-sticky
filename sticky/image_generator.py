import asyncio
import io
from enum import StrEnum
from typing import Literal, NamedTuple

import aiohttp
import cairosvg
import structlog
from gchanges import GiftChanges
from PIL import Image, ImageDraw
from pydantic import BaseModel

from sticky.kit.utils import utc_now
from sticky.logging import Logger

log: Logger = structlog.get_logger()


class FontPaths(StrEnum):
    sans_semibold = "assets/fonts/OpenSans-SemiBold.ttf"
    sans_extrabold = "assets/fonts/OpenSans-ExtraBold.ttf"


class GiftImageSettings(NamedTuple):
    size: int

    @property
    def box_size(self) -> tuple[int, int]:
        return self.size, self.size


class StickerTypes(StrEnum):
    neutral = "neutral"
    positive = "positive"
    negative = "negative"

    @property
    def template_path(self) -> str:
        filename = {
            StickerTypes.neutral: "template_neutral.png",
            StickerTypes.positive: "template_positive.png",
            StickerTypes.negative: "template_negative.png",
        }[self]
        return f"assets/{filename}"

    @property
    def fill_color(self) -> str:
        return {
            StickerTypes.neutral: "#BFBFBF",
            StickerTypes.positive: "#78FF2A",
            StickerTypes.negative: "#FF4545",
        }[self]


class StickerPayload(BaseModel):
    percent: float = 0
    gift_id: str
    price: float
    usd_price: float
    stars_price: int

    @property
    def sticker_type(self) -> StickerTypes:
        if self.percent == 0:
            return StickerTypes.neutral
        return StickerTypes.positive if self.percent > 0 else StickerTypes.negative

    def get_percent_sign(self) -> str:
        return "+" if self.percent > 0 else "-" if self.percent < 0 else ""


class ImageGenerator:
    GRAM_SVG_SIZE = 69
    GRAY_COLOR = "#c5c5c5"
    STAR_WIDTH = 32

    def __init__(
        self, *, sticker_download_size: Literal[1024, 512, 256, 128] = 512
    ) -> None:
        self.changes = GiftChanges()
        self.gim_settings = GiftImageSettings(size=sticker_download_size)

    def run(self) -> None:
        """Starts async loop or smth"""
        asyncio.run(self.start())

    async def start(self) -> None:
        names = await self.changes.get_names()

        for _, id in list(names.items())[:1]:
            payload = StickerPayload(
                gift_id=id,
                price=12.2,
                usd_price=12.3,
                stars_price=515,
                percent=1.25,
            )
            await self.generate_for_gift(payload=payload)

            payload.percent = -2.215
            await self.generate_for_gift(payload=payload)

            payload.percent = 0
            await self.generate_for_gift(payload=payload)

    async def generate_for_gift(self, payload: StickerPayload) -> None:
        log.debug("Generating sticker for gift", id=payload.gift_id)

        result_image = Image.open(payload.sticker_type.template_path)
        await self._put_gift_image_on_sticker(
            gift_id=payload.gift_id, canvas_image=result_image
        )

        result_image = Image.alpha_composite(
            result_image, self._get_price_text_overlay(payload=payload)
        )

        result_image = Image.alpha_composite(
            result_image, self._get_secondary_price_text_overlay(payload=payload)
        )

        result_image = Image.alpha_composite(
            result_image, self._get_bottom_text_overlay()
        )

        result_image = Image.alpha_composite(
            result_image, self._get_percent_text_overlay(payload=payload)
        )

        result_image.show()

    async def _put_gift_image_on_sticker(
        self, gift_id, canvas_image: Image.Image
    ) -> Image.Image:
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                url=f"https://api.changes.tg/original/{gift_id}.png?size={self.gim_settings.size}"
            )
            response.raise_for_status()
            image_bytes = await response.read()

            gift_image = Image.open(io.BytesIO(image_bytes))
            gift_image = gift_image.resize(size=(228, 228))

        canvas_image.paste(
            im=gift_image, box=(142, 66), mask=gift_image
        )  # 142 x, 66 y (upper); 142 x, 218 y (down);
        return canvas_image

    def _get_price_text_overlay(self, payload: StickerPayload) -> Image.Image:
        text = str(round(payload.price, 2))
        text_overlay = self._get_text_overlay()

        draw = ImageDraw.Draw(text_overlay)
        font = ImageDraw.ImageFont.truetype(FontPaths.sans_extrabold, size=64)

        text_width = _get_text_width_from_bbox(font.getbbox(text=text))

        left_pos = int(
            256 - text_width / 2 - self.GRAM_SVG_SIZE / 2 - 4
        )  # 4px is half of 8px gap
        text_left_pos = left_pos + self.GRAM_SVG_SIZE + 8

        draw.text((text_left_pos, 294), text=text, font=font, fill="#fff", align="center")

        gram_png_bytes = cairosvg.svg2png(url="assets/gram.svg")
        assert gram_png_bytes

        gram_svg_image = Image.open(io.BytesIO(gram_png_bytes))
        gram_svg_image = gram_svg_image.resize([self.GRAM_SVG_SIZE, self.GRAM_SVG_SIZE])
        text_overlay.paste(gram_svg_image, (left_pos, 303), gram_svg_image)

        return text_overlay

    def _get_secondary_price_text_overlay(self, payload: StickerPayload) -> Image.Image:
        """
        X - dollar + usd text width
        32 - star width
        10 - gap between star text and star icon
        Y - stars text width
        24 - gap between two
        """
        text_overlay = self._get_text_overlay()
        usd_text = f"$ {round(payload.usd_price, 2)}"

        draw = ImageDraw.Draw(text_overlay)
        font = ImageDraw.ImageFont.truetype(FontPaths.sans_semibold, size=36)

        usd_text_width = _get_text_width_from_bbox(font.getbbox(text=usd_text))
        star_content_width = (
            _get_text_width_from_bbox(font.getbbox(text=str(payload.stars_price)))
            + 10  # gap
            + self.STAR_WIDTH
        )
        content_width = usd_text_width + 24 + star_content_width

        leftmost_pos = int(256 - content_width / 2)

        draw.text(
            (leftmost_pos, 381),
            text=usd_text,
            fill=self.GRAY_COLOR,
            font=font,
            align="left",
        )

        star_png_bytes = cairosvg.svg2png(url="assets/telegram_star.svg")
        assert star_png_bytes

        star_svg_image = Image.open(io.BytesIO(star_png_bytes))
        star_svg_image = star_svg_image.resize([self.STAR_WIDTH, self.STAR_WIDTH - 1])

        star_content_left_pos = leftmost_pos + usd_text_width + 24
        text_overlay.paste(
            star_svg_image, (int(star_content_left_pos), 390), star_svg_image
        )

        draw.text(
            (star_content_left_pos + self.STAR_WIDTH + 10, 381),
            text=str(payload.stars_price),
            fill=self.GRAY_COLOR,
            font=font,
            align="right",
        )

        return text_overlay

    def _get_bottom_text_overlay(self) -> Image.Image:
        text_overlay = self._get_text_overlay()

        draw = ImageDraw.Draw(text_overlay)
        font = ImageDraw.ImageFont.truetype(FontPaths.sans_semibold, size=24)

        bottom_timestamp = utc_now().strftime("%d.%m.%Y %H:%M (UTC)")

        text_width = _get_text_width_from_bbox(font.getbbox(text=bottom_timestamp))
        left_pos = 256 - text_width / 2

        draw.text(
            (left_pos, 434), bottom_timestamp, font=font, fill="#999999", align="center"
        )

        return text_overlay

    def _get_percent_text_overlay(self, payload: StickerPayload) -> Image.Image:
        text_overlay = self._get_text_overlay()

        frame_width = 384
        text_frame = Image.new("RGBA", (frame_width, 50), (0, 0, 0, 0))

        draw = ImageDraw.Draw(text_frame)
        font = ImageDraw.ImageFont.truetype(FontPaths.sans_semibold, size=24)

        text = f"{payload.get_percent_sign()}{round(abs(payload.percent), 2)}%"

        text_width = _get_text_width_from_bbox(font.getbbox(text=text))

        draw.text(
            (frame_width / 2 - text_width / 2, 0),
            text=text,
            font=font,
            align="center",
            fill=payload.sticker_type.fill_color,
        )

        text_frame = text_frame.rotate(-45, expand=True)
        text_overlay.paste(text_frame, (265, -64), text_frame)

        return text_overlay

    def _get_text_overlay(self) -> Image.Image:
        return Image.new("RGBA", (512, 512), (255, 255, 255, 0))


def _get_text_width_from_bbox(bbox: tuple[float, float, float, float]) -> float:
    return bbox[2] - bbox[0]


generator = ImageGenerator()
