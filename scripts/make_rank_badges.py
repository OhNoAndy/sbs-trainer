"""
scripts/make_rank_badges.py - draw the rank badges as PNG files with Pillow.

The phone app draws its badges with vector graphics; the Streamlit app shows
pictures instead, so this script paints one PNG per rank tier (plus a grey
"locked" badge) into data/badges/. Shields for the lower tiers, a starburst
for Transcendent and a rainbow gem for the Legend steps, each with a soft glow.
The files are committed, so this only needs re-running after a design change:

    python scripts/make_rank_badges.py
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

import defaults  # noqa: E402

BADGES_DIR = os.path.join(PROJECT_DIR, "data", "badges")
SIZE = 256   # pixels; drawn at 4x and shrunk for smooth edges

TIER_COLORS = {
    "mortal": "#8a8f9c", "initiate": "#9fb3cc", "vanguard": "#4e9dff", "warden": "#2dd4bf",
    "colossus": "#46c57f", "titan": "#b07cff", "atlas": "#f5d90a", "demigod": "#ff9c3f",
    "transcendent": "#ff4d5a", "legend_1": "#c084fc", "legend_2": "#c084fc", "legend_3": "#c084fc",
}
GLYPHS = {
    "mortal": "M", "initiate": "I", "vanguard": "V", "warden": "W", "colossus": "C",
    "titan": "T", "atlas": "A", "demigod": "D",
}
NUMERALS = {"legend_1": "I", "legend_2": "II", "legend_3": "III"}
RAINBOW = ["#7dd3fc", "#c084fc", "#f472b6", "#fde68a", "#86efac"]
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def hex_to_rgb(text):
    """Takes "#rrggbb". Returns an (r, g, b) tuple of ints."""
    text = text.lstrip("#")
    return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))


def load_font(size):
    """Takes a pixel size. Returns a bold font, or Pillow's default if none is installed."""
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def hexagon_points(center_x, center_y, radius):
    """Takes a centre and radius. Returns the six corners of a pointy-top hexagon."""
    points = []
    for step in range(6):
        angle = math.radians(-90 + step * 60)
        points.append((center_x + radius * math.cos(angle), center_y + radius * math.sin(angle)))
    return points


def star_points(center_x, center_y, outer_radius, inner_radius, spikes):
    """Takes a centre, two radii and a spike count. Returns the corners of a star polygon."""
    points = []
    for step in range(spikes * 2):
        if step % 2 == 0:
            radius = outer_radius
        else:
            radius = inner_radius
        angle = -math.pi / 2 + step * math.pi / spikes
        points.append((center_x + radius * math.cos(angle), center_y + radius * math.sin(angle)))
    return points


def gem_points(scale):
    """Takes a scale (pixels per 100 units). Returns the gem outline used by the phone app."""
    outline = [(26, 10), (74, 10), (94, 38), (50, 95), (6, 38)]
    points = []
    for x, y in outline:
        points.append((x * scale, y * scale))
    return points


def rainbow_image(size):
    """Takes a pixel size. Returns a square RGBA image with a diagonal rainbow gradient."""
    image = Image.new("RGBA", (size, size))
    draw = ImageDraw.Draw(image)
    stops = []
    for color in RAINBOW:
        stops.append(hex_to_rgb(color))
    for x in range(size):
        position = x / (size - 1) * (len(stops) - 1)
        index = min(int(position), len(stops) - 2)
        share = position - index
        red = int(stops[index][0] + share * (stops[index + 1][0] - stops[index][0]))
        green = int(stops[index][1] + share * (stops[index + 1][1] - stops[index][1]))
        blue = int(stops[index][2] + share * (stops[index + 1][2] - stops[index][2]))
        draw.line([(x, 0), (x, size)], fill=(red, green, blue, 255))
    return image.rotate(-30, resample=Image.BICUBIC, expand=False)


def add_glow(image, points, color, radius):
    """
    Paint a blurred copy of a shape under an image (the badge's glow).

    Takes: the RGBA image, the shape's points, its colour, blur radius. Returns: a new image.
    """
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).polygon(points, fill=hex_to_rgb(color) + (190,))
    glow = glow.filter(ImageFilter.GaussianBlur(radius))
    return Image.alpha_composite(glow, image)


def draw_text_centered(draw, text, center, font, fill, stroke_fill=None, stroke_width=0):
    """Draws text so its box is centred on a point. Returns nothing."""
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    width = right - left
    height = bottom - top
    draw.text((center[0] - width / 2 - left, center[1] - height / 2 - top), text, font=font,
              fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)


def draw_badge(tier_key, glow):
    """
    Takes a tier key (or "locked") and whether to add a glow. Returns an RGBA badge image.
    """
    big = SIZE * 4
    scale = big / 100.0
    color = TIER_COLORS.get(tier_key, "#6b7280")
    rgb = hex_to_rgb(color)
    image = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    stroke = int(5 * scale)

    if tier_key == "transcendent":
        outer = star_points(50 * scale, 50 * scale, 47 * scale, 31 * scale, 8)
        inner = star_points(50 * scale, 50 * scale, 30 * scale, 20 * scale, 8)
        draw.polygon(outer, fill=(0, 0, 0, 115), outline=rgb + (255,), width=stroke)
        draw.polygon(inner, fill=rgb + (46,))
        core = 13 * scale
        draw.ellipse([50 * scale - core, 50 * scale - core, 50 * scale + core, 50 * scale + core],
                     fill=(0, 0, 0, 140), outline=rgb + (255,), width=int(3 * scale))
        dot = 5 * scale
        draw.ellipse([50 * scale - dot, 50 * scale - dot, 50 * scale + dot, 50 * scale + dot], fill=rgb + (255,))
        shape = outer
    elif tier_key in NUMERALS:
        shape = gem_points(scale)
        mask = Image.new("L", (big, big), 0)
        ImageDraw.Draw(mask).polygon(shape, fill=255)
        rainbow = rainbow_image(big)
        draw.polygon(shape, fill=(0, 0, 0, 128))
        fill = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        fill.paste(rainbow, (0, 0), mask)
        fill.putalpha(fill.getchannel("A").point(lambda value: int(value * 0.32)))
        image = Image.alpha_composite(image, fill)
        draw = ImageDraw.Draw(image)
        edge = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        edge_mask = Image.new("L", (big, big), 0)
        edge_draw = ImageDraw.Draw(edge_mask)
        edge_draw.polygon(shape, outline=255, width=stroke)
        edge_draw.line([(6 * scale, 38 * scale), (94 * scale, 38 * scale)], fill=255, width=int(2 * scale))
        edge_draw.line([(26 * scale, 10 * scale), (38 * scale, 38 * scale), (50 * scale, 95 * scale)], fill=200, width=int(2 * scale))
        edge_draw.line([(74 * scale, 10 * scale), (62 * scale, 38 * scale), (50 * scale, 95 * scale)], fill=200, width=int(2 * scale))
        edge.paste(rainbow, (0, 0), edge_mask)
        image = Image.alpha_composite(image, edge)
        draw = ImageDraw.Draw(image)
        draw_text_centered(draw, NUMERALS[tier_key], (50 * scale, 57 * scale), load_font(int(26 * scale)),
                           (255, 255, 255, 255), stroke_fill=(0, 0, 0, 160), stroke_width=int(1.2 * scale))
    else:
        shape = hexagon_points(50 * scale, 50 * scale, 46 * scale)
        inner = hexagon_points(50 * scale, 50 * scale, 34 * scale)
        draw.polygon(shape, fill=(0, 0, 0, 115), outline=rgb + (255,), width=stroke)
        draw.polygon(inner, fill=rgb + (41,))
        glyph = GLYPHS.get(tier_key, "?")
        draw_text_centered(draw, glyph, (50 * scale, 51 * scale), load_font(int(40 * scale)), rgb + (255,))

    if glow:
        image = add_glow(image, shape, color, int(6 * scale))
    return image.resize((SIZE, SIZE), Image.LANCZOS)


def main():
    """Writes every badge PNG. Returns nothing."""
    os.makedirs(BADGES_DIR, exist_ok=True)
    for tier in defaults.RANK_TIERS:
        badge = draw_badge(tier["key"], tier["effect"] != "none")
        badge.save(os.path.join(BADGES_DIR, tier["key"] + ".png"), "PNG")
    draw_badge("locked", False).save(os.path.join(BADGES_DIR, "locked.png"), "PNG")
    print("Wrote " + str(len(defaults.RANK_TIERS) + 1) + " badges to " + BADGES_DIR)


if __name__ == "__main__":
    main()
