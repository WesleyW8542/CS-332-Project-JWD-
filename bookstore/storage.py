from dataclasses import dataclass, field

from .models import Account, Book, Review, Role


@dataclass
class Store:
    """In-memory records for the prototype. Add durable storage here."""

    books: dict[str, Book] = field(default_factory=dict)
    accounts: dict[str, Account] = field(default_factory=dict)
    browse_counts: dict[tuple[str, str], int] = field(default_factory=dict)
    purchase_counts: dict[tuple[str, str], int] = field(default_factory=dict)
    reviews: list[Review] = field(default_factory=list)
    taboo_terms: set[str] = field(default_factory=set)
    warnings: dict[str, int] = field(default_factory=dict)


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

