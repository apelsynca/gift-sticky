import io
import os
from typing import Literal

import cairosvg
import structlog
from PIL import Image, ImageDraw

from sticky.kit.utils import utc_now
from sticky.logging import Logger
from sticky.sticker_renderer.enums import FontPaths
from sticky.sticker_renderer.template_loader import StickerTemplateLoader
from sticky.sticker_renderer.types import GiftImageSettings, StickerPayload
from sticky.sticker_renderer.utils import (
    download_image_by_url,
    make_linear_gradient,
    round_string_for_render,
)

log: Logger = structlog.get_logger()

GENERATIONS_PATH = "generations"


class StickerRenderer:
    """
    Class for generating a sticker

    @generate - Generates sticker by payload
    """

    GRAM_SVG_SIZE = 69
    GRAY_COLOR = "#c5c5c5"
    STAR_WIDTH = 32

    def __init__(
        self, *, sticker_download_size: Literal[1024, 512, 256, 128] = 256
    ) -> None:
        self.gim_settings = GiftImageSettings(size=sticker_download_size)

        self.template_loader = StickerTemplateLoader()

    async def render_and_save_to_file(self, payload: StickerPayload, path: str) -> None:
        """Method to generate a sticker from payload and save"""
        log.debug("Generating sticker for gift", id=payload.gift_id)

        result_image = await self.template_loader.get_template(
            sticker_type=payload.sticker_type
        )

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
            result_image,
            self._get_bottom_text_overlay(),
        )

        result_image = Image.alpha_composite(
            result_image, self._get_percent_text_overlay(payload=payload)
        )

        # A failed write must not leave a truncated file that gets published afterwards
        temporary_path = f"{path}.tmp"
        result_image.save(temporary_path, format="PNG")
        os.replace(temporary_path, path)

    async def _put_gift_image_on_sticker(
        self, gift_id, canvas_image: Image.Image
    ) -> Image.Image:
        gift_image = await download_image_by_url(
            url=f"https://api.changes.tg/original/{gift_id}.png?size={self.gim_settings.size}"
        )
        gift_image = gift_image.resize(size=(228, 228))

        canvas_image.paste(
            im=gift_image, box=(142, 66), mask=gift_image
        )  # 142 x, 66 y (upper); 142 x, 218 y (down);
        return canvas_image

    def _get_price_text_overlay(self, payload: StickerPayload) -> Image.Image:
        text = round_string_for_render(payload.price)
        text_overlay = self._get_text_overlay()

        draw = ImageDraw.Draw(text_overlay)
        font = ImageDraw.ImageFont.truetype(FontPaths.sans_extrabold, size=64)

        t_left, t_top, t_right, t_bottom = font.getbbox(text=text)
        text_width = _get_text_width_from_bbox((t_left, t_top, t_right, t_bottom))

        left_pos = round(
            256 - text_width / 2 - self.GRAM_SVG_SIZE / 2 - 4
        )  # 4px is half of 8px gap
        text_left_pos = left_pos + self.GRAM_SVG_SIZE + 8

        text_bbox = (round(t_right - t_left), round(t_bottom - t_top + 3))
        text_mask_overlay = Image.new("RGBA", size=text_bbox)

        # the white text
        before_draw = ImageDraw.Draw(text_mask_overlay)
        before_draw.text(
            (0, round(t_bottom - t_top) / -2 + 3),
            text=text,
            font=font,
            fill="#ffffff",
            align="center",
        )

        gradient_overlay = make_linear_gradient(
            size=text_bbox,
            from_color=payload.sticker_type.price_fill_from,
            to_color=payload.sticker_type.price_fill_to,
            direction="vertical",
        )

        # crop gradient bg using text as mask (which makes me a gradient filled text)
        text_overlay.paste(gradient_overlay, (text_left_pos, 314 - 2), text_mask_overlay)

        gram_png_bytes = cairosvg.svg2png(url=payload.sticker_type.gram_icon_path)
        assert gram_png_bytes is not None

        gram_svg_image = Image.open(io.BytesIO(gram_png_bytes))
        gram_svg_image = gram_svg_image.resize([self.GRAM_SVG_SIZE, self.GRAM_SVG_SIZE])
        text_overlay.paste(gram_svg_image, (left_pos, 303), gram_svg_image)

        return text_overlay

    def _get_secondary_price_text_overlay(self, payload: StickerPayload) -> Image.Image:
        """
        Put secondary price text overlay

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

        leftmost_pos = round(256 - content_width / 2)

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
            star_svg_image, (round(star_content_left_pos), 390), star_svg_image
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

        text = f"{payload.get_percent_sign()}{round(abs(payload.percent * 100))}%"

        text_width = _get_text_width_from_bbox(font.getbbox(text=text))

        draw.text(
            (frame_width / 2 - text_width / 2, 0),
            text=text,
            font=font,
            align="center",
            fill=payload.sticker_type.percent_fill,
        )

        text_frame = text_frame.rotate(-45, expand=True)
        text_overlay.paste(text_frame, (265, -64), text_frame)

        return text_overlay

    def _get_text_overlay(self) -> Image.Image:
        return Image.new("RGBA", (512, 512), (255, 255, 255, 0))

    def get_render_path(self, telegram_id: str) -> str:
        return f"{GENERATIONS_PATH}/{telegram_id}.png"


def _get_text_width_from_bbox(bbox: tuple[float, float, float, float]) -> float:
    return bbox[2] - bbox[0]
