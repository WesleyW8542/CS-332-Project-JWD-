from .models import Account, Book, Role
from .storage import Store


class Catalog:
    def __init__(self, store: Store):
        self.store = store

    def browse(
        self, category: str = "", author: str = "", year: int | None = None
    ) -> list[Book]:
        return [
            book for book in self.store.books.values()
            if (not category or book.category.casefold() == category.casefold())
            and (not author or author.casefold() in book.author.casefold())
            and (year is None or book.year == year)
        ]

    def search(self, keywords: str, image: bytes | None = None) -> list[Book]:
        if image is not None:
            raise NotImplementedError("Connect the image matching component here.")
        terms = keywords.casefold().split()
        return [
            book for book in self.browse()
            if all(term in f"{book.title} {book.author} {book.category}".casefold()
                   for term in terms)
        ]

    def open_book(self, book_id: str, viewer_id: str) -> Book:
        book = self.store.books[book_id]
        key = (viewer_id, book_id)
        self.store.browse_counts[key] = self.store.browse_counts.get(key, 0) + 1
        return book

    def add_book(self, actor: Account, book: Book) -> None:
        if actor.role is not Role.ADMIN or actor.suspended:
            raise PermissionError("An active super-user is required.")
        if (not book.id.strip() or not book.title.strip()
                or not book.author.strip() or not book.category.strip()
                or book.price_cents < 0 or book.id in self.store.books):
            raise ValueError("Enter complete book details and a unique book ID.")
        self.store.books[book.id] = book

    def recommendations(self, account: Account | None = None) -> list[Book]:
        customer_id = None
        if account and account.role in (Role.CUSTOMER, Role.VIP):
            customer_id = account.id

        scores = dict.fromkeys(self.store.books, 0)
        for counts in (self.store.browse_counts, self.store.purchase_counts):
            for (viewer_id, book_id), count in counts.items():
                if book_id in scores and (customer_id is None or viewer_id == customer_id):
                    scores[book_id] += count
        return sorted(
            self.store.books.values(), key=lambda book: (-scores[book.id], book.id)
        )[:3]

