"""
scripts/make_icons.py - draw the phone app's icons with Pillow.

Writes phone/icons/icon-180.png (iPhone home screen), icon-192.png and
icon-512.png (Android / manifest). Run from the project folder:

    python scripts/make_icons.py
"""
import os

from PIL import Image, ImageDraw

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS_DIR = os.path.join(PROJECT_DIR, "phone", "icons")
SIZES = [180, 192, 512]


def draw_icon(size):
    """
    Draw one square icon: a barbell on a dark rounded background.

    Takes: the size in pixels. Returns: a Pillow image.
    """
    image = Image.new("RGB", (size, size), (20, 22, 28))
    draw = ImageDraw.Draw(image)
    unit = size / 100.0
    middle = size / 2
    bar_color = (230, 232, 238)
    plate_color = (255, 90, 78)
    # The bar
    draw.rounded_rectangle([14 * unit, middle - 4 * unit, 86 * unit, middle + 4 * unit], radius=4 * unit, fill=bar_color)
    # Plates: two on each side, the inner one taller
    for x, height in [(20, 30), (30, 24), (62, 24), (72, 30)]:
        draw.rounded_rectangle([x * unit, middle - height * unit, (x + 8) * unit, middle + height * unit],
                               radius=3 * unit, fill=plate_color)
    return image


def main():
    """Writes every icon size. Returns nothing."""
    os.makedirs(ICONS_DIR, exist_ok=True)
    for size in SIZES:
        path = os.path.join(ICONS_DIR, "icon-" + str(size) + ".png")
        draw_icon(size).save(path, "PNG")
        print("Wrote " + path)


if __name__ == "__main__":
    main()
