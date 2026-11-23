from contextlib import closing, nullcontext
from dataclasses import dataclass, field
from pathlib import Path
import sqlite3

from .activity import Activity
from .models import Account, Book, PurchaseRecord, Review, Role


LOCAL_CATALOG_PATH = Path(__file__).resolve().parent.parent / "local_catalog.sqlite3"


class LocalCatalog:
    def __init__(self, path: Path = LOCAL_CATALOG_PATH):
        self.path = path

    def load(self) -> dict[str, Book]:
        if not self.path.exists():
            return {}
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            self.prepare(connection)
            rows = connection.execute(
                "SELECT id, title, author, category, year, price_cents, NULL, description, cover "
                "FROM books ORDER BY rowid"
            )
            return {row[0]: Book(*row) for row in rows}

    @staticmethod
    def prepare(connection: sqlite3.Connection) -> None:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                category TEXT NOT NULL,
                year INTEGER,
                price_cents INTEGER NOT NULL CHECK (price_cents >= 0)
            )
        """)
        columns = {row[1] for row in connection.execute("PRAGMA table_info(books)")}
        if "description" not in columns:
            connection.execute("ALTER TABLE books ADD COLUMN description TEXT NOT NULL DEFAULT ''")
        if "cover" not in columns:
            connection.execute("ALTER TABLE books ADD COLUMN cover BLOB")

    def save(self, book: Book) -> None:
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            self.prepare(connection)
            connection.execute(
                "INSERT INTO books (id, title, author, category, year, price_cents, description, cover) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (book.id, book.title, book.author, book.category, book.year, book.price_cents,
                 book.description, book.cover),
            )


@dataclass
class Store:
    """Working records for the current session."""

    books: dict[str, Book] = field(default_factory=dict)
    accounts: dict[str, Account] = field(default_factory=dict)
    browse_counts: dict[tuple[str, str], int] = field(default_factory=dict)
    purchase_counts: dict[tuple[str, str], int] = field(default_factory=dict)
    purchases: list[PurchaseRecord] = field(default_factory=list)
    reviews: list[Review] = field(default_factory=list)
    taboo_terms: set[str] = field(default_factory=set)
    warnings: dict[str, int] = field(default_factory=dict)
    local_catalog: LocalCatalog | None = None
    activity: Activity | None = None
    store_info: str = ""
    team_info: str = ""
    voice_profiles: dict[str, list[list[float]]] = field(default_factory=dict)

    def change_activity(self):
        return self.activity.change(self) if self.activity else nullcontext()


def demo_store() -> Store:
    books = [
        Book("B001", "Pride and Prejudice", "Jane Austen", "Literature", 1813, 800),
        Book("B002", "Frankenstein", "Mary Shelley", "Science fiction", 1818, 650),
        Book("B003", "The Time Machine", "H. G. Wells", "Science fiction", 1895, 500),
        Book("B004", "The Souls of Black Folk", "W. E. B. Du Bois", "Essays", 1903, 700),
    ]
    customer = Account("demo-customer", Role.CUSTOMER, balance_cents=1200)
    return Store(
        books={book.id: book for book in books},
        accounts={customer.id: customer},
    )

