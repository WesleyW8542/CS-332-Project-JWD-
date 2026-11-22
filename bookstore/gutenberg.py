import csv
from pathlib import Path
from shutil import copyfileobj
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

from .models import Book


CATALOG_PATH = Path(__file__).resolve().parent.parent / "pg_catalog.csv"
CATALOG_URL = "https://gutenberg.pglaf.org/cache/epub/feeds/pg_catalog.csv"
REQUIRED_COLUMNS = {"Text#", "Type", "Issued", "Title", "Authors", "Bookshelves"}


def load_books(path: Path = CATALOG_PATH) -> dict[str, Book]:
    books = {}
    with path.open(encoding="utf-8-sig", newline="") as source:
        rows = csv.DictReader(source, strict=True)
        if not REQUIRED_COLUMNS.issubset(rows.fieldnames or ()):
            raise ValueError("The file is missing Project Gutenberg catalog columns.")
        for row in rows:
            ebook_id = (row["Text#"] or "").strip()
            title = (row["Title"] or "").strip()
            if row["Type"] != "Text" or not title or not ebook_id.isascii() or not ebook_id.isdecimal():
                continue
            author = (row["Authors"] or "").strip()
            shelves = (row["Bookshelves"] or "").split(";")
            categories = [shelf.strip().removeprefix("Category: ") for shelf in shelves
                          if shelf.strip().startswith("Category: ")]
            category = categories[0] if categories else next(
                (shelf.strip() for shelf in shelves if shelf.strip()), "Uncategorized"
            )
            issued = (row["Issued"] or "")[:4]
            year = int(issued) if len(issued) == 4 and issued.isdecimal() else None
            book_id = f"PG-{ebook_id}"
            books[book_id] = Book(
                book_id, title, author or "Unknown author", category, year, 0,
                source_url=f"https://www.gutenberg.org/ebooks/{ebook_id}",
            )
    if not books:
        raise ValueError("The Project Gutenberg catalog contains no ebook records.")
    return books


def download_catalog(path: Path = CATALOG_PATH) -> int:
    temporary_path = None
    try:
        with urlopen(CATALOG_URL, timeout=30) as response:
            expected_size = response.headers.get("Content-Length")
            with NamedTemporaryFile(
                dir=path.parent, prefix=".gutenberg-", suffix=".part", delete=False
            ) as temporary:
                temporary_path = Path(temporary.name)
                copyfileobj(response, temporary)
                if expected_size and temporary.tell() != int(expected_size):
                    raise OSError("The catalog download ended before the full file arrived.")
        count = len(load_books(temporary_path))
        temporary_path.replace(path)
        return count
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

