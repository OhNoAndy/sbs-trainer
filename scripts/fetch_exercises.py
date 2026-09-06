"""
scripts/fetch_exercises.py - download and trim the free-exercise-db dataset.

Source: https://github.com/yuhonas/free-exercise-db
        (800+ exercises with photos, released into the public domain / Unlicense)

Run it from the project folder:

    python scripts/fetch_exercises.py               # everything (about 1750 photos, a few minutes)
    python scripts/fetch_exercises.py --limit 25    # quick test run
    python scripts/fetch_exercises.py --skip-images # only refresh data/exercises.json
    python scripts/fetch_exercises.py --force       # re-download images that already exist

What it writes:
    data/exercises.json         one trimmed entry per exercise (id, name, muscles, image)
    data/images/<id>.jpg        the start and finish photos side by side in one strip
    data/images/placeholder.png a generic image for exercises with no match

The dataset has two photos per exercise: the start position and the finish
position. A curl, for example, is "arms hanging" then "arms bent". Showing
only one frame is misleading, so both are pasted next to each other.

Images that already exist on disk are skipped unless --force is given, so
re-running is cheap and safe. Only the standard library plus Pillow is used.
"""
import io
import json
import os
import sys
import urllib.request

from PIL import Image, ImageDraw

JSON_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
IMAGE_URL_BASE = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/"

FRAME_WIDTH = 360            # each photo is shrunk to this width before pasting
FRAMES_PER_EXERCISE = 2      # start position + finish position
JPEG_QUALITY = 80
DOWNLOAD_ATTEMPTS = 3

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
CATALOG_PATH = os.path.join(DATA_DIR, "exercises.json")
PLACEHOLDER_PATH = os.path.join(IMAGES_DIR, "placeholder.png")


def download_bytes(url):
    """
    Fetch a URL and return its raw bytes, retrying a couple of times.

    Takes: url string. Returns: bytes. Raises the last error if every attempt fails.
    """
    last_error = None
    for attempt in range(DOWNLOAD_ATTEMPTS):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return response.read()
        except Exception as error:
            last_error = error
    raise last_error


def trim_exercise(raw):
    """
    Keep only the fields the app needs from one dataset entry.

    Takes: the raw dict from the dataset. Returns: a small dict.
    """
    image_name = ""
    if len(raw.get("images", [])) > 0:
        image_name = raw["id"] + ".jpg"
    return {
        "id": raw["id"],
        "name": raw["name"],
        "category": raw.get("category") or "",
        "equipment": raw.get("equipment") or "",
        "primary_muscles": raw.get("primaryMuscles", []),
        "image": image_name,
    }


def load_frame(image_bytes):
    """
    Open one downloaded photo and shrink it to FRAME_WIDTH.

    Takes: image bytes. Returns: a Pillow image.
    """
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    width, height = image.size
    if width > FRAME_WIDTH:
        new_height = int(height * FRAME_WIDTH / width)
        image = image.resize((FRAME_WIDTH, new_height), Image.LANCZOS)
    return image


def combine_frames(frames):
    """
    Paste the start and finish photos side by side on one canvas.

    Takes: a list of Pillow images. Returns: one wide Pillow image.
    """
    total_width = 0
    tallest = 0
    for frame in frames:
        total_width += frame.width
        if frame.height > tallest:
            tallest = frame.height
    canvas = Image.new("RGB", (total_width, tallest), (255, 255, 255))
    x_position = 0
    for frame in frames:
        canvas.paste(frame, (x_position, 0))
        x_position += frame.width
    return canvas


def make_placeholder_image(destination):
    """
    Draw a simple grey card with a barbell so exercises without a photo still show something.

    Takes: destination path. Returns: nothing.
    """
    width, height = FRAME_WIDTH * FRAMES_PER_EXERCISE, 240
    image = Image.new("RGB", (width, height), (235, 235, 235))
    draw = ImageDraw.Draw(image)
    bar_color = (120, 120, 120)
    plate_color = (70, 70, 70)
    middle = height // 2
    # The bar
    draw.rectangle([140, middle - 6, width - 140, middle + 6], fill=bar_color)
    # Two plates on each side
    for x in [160, 200, width - 240, width - 200]:
        draw.rectangle([x, middle - 60, x + 30, middle + 60], fill=plate_color)
    draw.text((width // 2 - 55, height - 40), "No image available", fill=(90, 90, 90))
    image.save(destination, "PNG")


def exercise_sort_key(exercise):
    """Takes one raw exercise dict. Returns its name, so the list sorts alphabetically."""
    return exercise["name"]


def read_options():
    """
    Read the command line flags.

    Returns: (limit, skip_images, force) where limit is None or an int.
    """
    limit = None
    skip_images = False
    force = False
    arguments = sys.argv[1:]
    for position in range(len(arguments)):
        if arguments[position] == "--limit" and position + 1 < len(arguments):
            limit = int(arguments[position + 1])
        if arguments[position] == "--skip-images":
            skip_images = True
        if arguments[position] == "--force":
            force = True
    return limit, skip_images, force


def main():
    """Downloads the dataset, trims it, and saves the image strips. Returns nothing."""
    limit, skip_images, force = read_options()
    os.makedirs(IMAGES_DIR, exist_ok=True)

    print("Downloading exercise list from " + JSON_URL)
    raw_exercises = json.loads(download_bytes(JSON_URL).decode("utf-8"))
    raw_exercises.sort(key=exercise_sort_key)
    if limit is not None:
        raw_exercises = raw_exercises[:limit]
    print("Found " + str(len(raw_exercises)) + " exercises")

    catalog = []
    downloaded = 0
    skipped = 0
    failed = 0
    for position in range(len(raw_exercises)):
        raw = raw_exercises[position]
        entry = trim_exercise(raw)
        if entry["image"] != "" and not skip_images:
            destination = os.path.join(IMAGES_DIR, entry["image"])
            if os.path.exists(destination) and not force:
                skipped += 1
            else:
                frames = []
                for image_name in raw["images"][:FRAMES_PER_EXERCISE]:
                    try:
                        frames.append(load_frame(download_bytes(IMAGE_URL_BASE + image_name)))
                    except Exception as error:
                        print("  could not fetch " + image_name + ": " + str(error))
                if len(frames) > 0:
                    combine_frames(frames).save(destination, "JPEG", quality=JPEG_QUALITY, optimize=True)
                    downloaded += 1
                else:
                    entry["image"] = ""
                    failed += 1
        catalog.append(entry)
        if (position + 1) % 50 == 0:
            print("  " + str(position + 1) + " / " + str(len(raw_exercises)) + " done", flush=True)

    with open(CATALOG_PATH, "w", encoding="utf-8") as file:
        json.dump(catalog, file, indent=1)
    make_placeholder_image(PLACEHOLDER_PATH)

    print("Wrote " + CATALOG_PATH + " with " + str(len(catalog)) + " exercises")
    print("Images written: " + str(downloaded) + ", already present: " + str(skipped) + ", failed: " + str(failed))


if __name__ == "__main__":
    main()
