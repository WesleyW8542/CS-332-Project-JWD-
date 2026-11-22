import argparse
import csv

from . import money
from .gutenberg import download_catalog, load_books
from .models import Account, Role
from .storage import Store, demo_store


def main() -> None:
    parser = argparse.ArgumentParser(description="Smart Bookstore")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--sync-gutenberg", action="store_true", help="Download the official catalog")
    mode.add_argument("--demo", action="store_true", help="Use the sample catalog to test checkout")
    mode.add_argument("--demo-vip", action="store_true", help="Try checkout as a VIP customer")
    mode.add_argument("--demo-admin", action="store_true", help="Try adding books as a super-user")
    parser.add_argument("--list-books", action="store_true", help="List books without a GUI")
    args = parser.parse_args()

    try:
        if args.sync_gutenberg:
            print("Downloading the Project Gutenberg catalog…", flush=True)
            print(f"Downloaded {download_catalog():,} Project Gutenberg ebooks.")
            return
        demo = args.demo or args.demo_vip or args.demo_admin
        store = demo_store() if demo else Store(books=load_books())
    except FileNotFoundError:
        parser.exit(1, "Catalog missing. Run python -m bookstore --sync-gutenberg first.\n")
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"Could not prepare the Gutenberg catalog: {error}\n")

    if args.list_books:
        for book in store.books.values():
            price = "Free" if book.source_url else money(book.price_cents)
            print(f"{book.title} | {book.author} | {price}")
    else:
        from .desktop import launch

        actor = store.accounts.get("demo-customer")
        if args.demo_admin:
            actor = Account("demo-admin", Role.ADMIN)
        elif args.demo_vip:
            actor = store.accounts["demo-customer"]
            actor.role = Role.VIP
        launch(store, demo=demo, actor=actor)


if __name__ == "__main__":
    main()

