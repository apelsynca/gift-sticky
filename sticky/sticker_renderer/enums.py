from enum import StrEnum


class FontPaths(StrEnum):
    """Font paths enums"""

    sans_semibold = "assets/fonts/OpenSans-SemiBold.ttf"
    sans_extrabold = "assets/fonts/OpenSans-ExtraBold.ttf"


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
    def gram_icon_path(self) -> str:
        filename = {
            StickerTypes.neutral: "gram_neutral.svg",
            StickerTypes.positive: "gram_positive.svg",
            StickerTypes.negative: "gram_negative.svg",
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
