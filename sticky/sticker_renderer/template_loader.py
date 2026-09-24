import structlog
from PIL import Image

from sticky.config import settings
from sticky.logging import Logger
from sticky.sticker_renderer.enums import StickerTypes
from sticky.sticker_renderer.utils import download_image_by_url, is_url

log: Logger = structlog.get_logger()


class StickerTemplateLoader:
    def __init__(self) -> None:
        self._templates_loaded = False

        self._neutral_template: Image.Image | None = None
        self._positive_template: Image.Image | None = None
        self._negative_template: Image.Image | None = None

    async def get_template(self, sticker_type: StickerTypes) -> Image.Image:
        """Gets a template based by sticker_type"""
        neutral, positive, negative = await self.get_templates()

        return {
            StickerTypes.neutral: neutral,
            StickerTypes.positive: positive,
            StickerTypes.negative: negative,
        }[sticker_type]

    async def get_templates(self) -> tuple[Image.Image, Image.Image, Image.Image]:
        if self._templates_loaded is False:
            await self.load_templates()

        if (
            self._neutral_template is None
            or self._positive_template is None
            or self._negative_template is None
        ):
            raise RuntimeError(
                "One of the templates are None, "
                "make sure `load_templates` method is called somewhere"
            )

        return (
            self._neutral_template.copy(),
            self._positive_template.copy(),
            self._negative_template.copy(),
        )

    async def load_templates(self) -> None:
        neutral_template_path = (
            settings.STICKER_NEUTRAL_TEMPLATE_PATH
            if settings.STICKER_NEUTRAL_TEMPLATE_PATH
            else StickerTypes.neutral.template_path
        )

        positive_template_path = (
            settings.STICKER_POSITIVE_TEMPLATE_PATH
            if settings.STICKER_POSITIVE_TEMPLATE_PATH
            else StickerTypes.positive.template_path
        )

        negative_template_path = (
            settings.STICKER_NEGATIVE_TEMPLATE_PATH
            if settings.STICKER_NEGATIVE_TEMPLATE_PATH
            else StickerTypes.negative.template_path
        )

        log.info(
            "Loading sticker templates",
            neutral_template_path=neutral_template_path,
            positive_template_path=positive_template_path,
            negative_template_path=negative_template_path,
        )

        if is_url(neutral_template_path):
            self._neutral_template = await download_image_by_url(neutral_template_path)
        else:
            self._neutral_template = Image.open(neutral_template_path)

        if is_url(positive_template_path):
            self._positive_template = await download_image_by_url(positive_template_path)
        else:
            self._positive_template = Image.open(positive_template_path)

        if is_url(negative_template_path):
            self._negative_template = await download_image_by_url(negative_template_path)
        else:
            self._negative_template = Image.open(negative_template_path)

        self._templates_loaded = True
