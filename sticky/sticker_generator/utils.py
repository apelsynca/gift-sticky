from typing import Literal

from PIL import Image, ImageColor


def make_linear_gradient(
    size: tuple[int, int],
    from_color: str,
    to_color: str,
    direction: Literal["horizontal", "vertical"] = "horizontal",
) -> Image.Image:
    """
    Create a linear gradient image.
    size: (width, height)
    color1, color2: RGB tuples
    direction: 'horizontal' or 'vertical'
    """
    rgb_color1 = ImageColor.getrgb(from_color)
    rgb_color2 = ImageColor.getrgb(to_color)

    width, height = size
    if direction == "horizontal":
        # Create a 1-pixel high gradient and stretch it
        grad = Image.new("RGB", (width, 1))
        for x in range(width):
            t = x / (width - 1) if width > 1 else 0
            r = int(rgb_color1[0] + (rgb_color2[0] - rgb_color1[0]) * t)
            g = int(rgb_color1[1] + (rgb_color2[1] - rgb_color1[1]) * t)
            b = int(rgb_color1[2] + (rgb_color2[2] - rgb_color1[2]) * t)
            grad.putpixel((x, 0), (r, g, b))
        return grad.resize((width, height))
    else:  # vertical
        grad = Image.new("RGB", (1, height))
        for y in range(height):
            t = y / (height - 1) if height > 1 else 0
            r = int(rgb_color1[0] + (rgb_color2[0] - rgb_color1[0]) * t)
            g = int(rgb_color1[1] + (rgb_color2[1] - rgb_color1[1]) * t)
            b = int(rgb_color1[2] + (rgb_color2[2] - rgb_color1[2]) * t)
            grad.putpixel((0, y), (r, g, b))
        return grad.resize((width, height))
