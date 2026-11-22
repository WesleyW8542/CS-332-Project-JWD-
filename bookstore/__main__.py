import argparse

from . import money
from .catalog import Catalog
from .storage import demo_store


def main() -> None:
    parser = argparse.ArgumentParser(description="Smart Bookstore prototype")
    parser.add_argument("--list-books", action="store_true", help="List demo books without a GUI")
    args = parser.parse_args()
    if args.list_books:
        for book in Catalog(demo_store()).browse():
            print(f"{book.title} | {book.author} | {money(book.price_cents)}")
    else:
        from .desktop import launch

        launch()


if __name__ == "__main__":
    main()

