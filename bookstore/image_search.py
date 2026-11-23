from io import BytesIO
from pathlib import Path

from .models import Book

IMAGE_DIR = Path(__file__).resolve().parent.parent / "book_images"
MAX_IMAGE_BYTES = 10 * 1024 * 1024
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def read_image(path: Path) -> bytes:
    with path.open("rb") as image:
        data = image.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Choose a JPEG or PNG smaller than 10 MB.")
    return data


def image_signature(data: bytes) -> tuple[int, tuple[int, ...]]:
    try:
        from PIL import Image, ImageOps
    except ImportError as error:
        raise ValueError("Install the image dependency with python -m pip install Pillow.") from error
    try:
        with Image.open(BytesIO(data), formats=["JPEG", "PNG"]) as image:
            if image.width * image.height > 20_000_000:
                raise ValueError("Choose an image with at most 20 million pixels.")
            oriented = ImageOps.exif_transpose(image)
            gray = list(oriented.convert("L").resize((9, 8)).getdata())
            colors = tuple(channel for pixel in oriented.convert("RGB").resize((4, 4)).getdata()
                           for channel in pixel)
    except (OSError, Image.DecompressionBombError) as error:
        raise ValueError("Choose a readable JPEG or PNG.") from error
    bits = 0
    for row in range(0, 72, 9):
        for column in range(8):
            bits = (bits << 1) | (gray[row + column] > gray[row + column + 1])
    return bits, colors


def rank_images(query: bytes, books: list[Book], directory: Path = IMAGE_DIR) -> list[Book]:
    query_bits, query_colors = image_signature(query)
    assets: dict[str, list[Path]] = {}
    if directory.is_dir():
        for file in directory.iterdir():
            if file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS:
                book_id = file.stem.split("__", 1)[0]
                assets.setdefault(book_id, []).append(file)

    def distance(data: bytes) -> float:
        bits, colors = image_signature(data)
        edges = (query_bits ^ bits).bit_count() / 64
        color = sum(abs(left - right) for left, right in zip(query_colors, colors)) / (48 * 255)
        return edges * 0.7 + color * 0.3

    matches = []
    for book in books:
        scores = [distance(book.cover)] if book.cover else []
        for path in assets.get(book.id, ()):
            try:
                scores.append(distance(read_image(path)))
            except (OSError, ValueError):
                continue
        if scores and min(scores) <= 0.22:
            matches.append((min(scores), book.id, book))
    return [book for _, _, book in sorted(matches)]
