from enum import StrEnum
from typing import NamedTuple

from pydantic import BaseModel


class FontPaths(StrEnum):
    """Font paths enums"""

    sans_semibold = "assets/fonts/OpenSans-SemiBold.ttf"
    sans_extrabold = "assets/fonts/OpenSans-ExtraBold.ttf"


class GiftImageSettings(NamedTuple):
    """Settings for the gift image (size only for now)"""

    size: int

    @property
    def box_size(self) -> tuple[int, int]:
        return self.size, self.size


class StickerTypes(StrEnum):
    """
    Available sticker types

    Neutral -> if price percent change is 0%
    Positive -> if price percent change is bigger than 0%
    Negative -> if price percent change is lower than 0%
    """

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
    def percent_fill(self) -> str:
        """
        Returns a fill color for percent text

        (green if positive, red if negative, gray if neutral)
        """

        return {
            StickerTypes.neutral: "#bfbfbf",
            StickerTypes.positive: "#78ff2a",
            StickerTypes.negative: "#ff4545",
        }[self]

    @property
    def price_fill_from(self):
        return self.get_price_fill()[0]

    @property
    def price_fill_to(self):
        return self.get_price_fill()[1]

    def get_price_fill(self) -> tuple[str, str]:
        """
        Returns a fill color for main price text

        (green if positive, red if negative, other if neutral)
        """

        return {
            StickerTypes.neutral: ("#ffffff", "#b4e4ff"),
            StickerTypes.positive: ("#37ff62", "#92ffa9"),
            StickerTypes.negative: ("#ff3737", "#f87e7e"),
        }[self]


class StickerPayload(BaseModel):
    """
    Basically all of the info about sticker

    percent - Price change in percent
    *gift_id - Telegram gift ID
    *price - Current price in GRAM
    *usd_price - Current price in USD
    *stars_price - Current price in stars
    sticker_type -> type of the sticker based on percent
    """

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
