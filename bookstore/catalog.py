from .image_search import rank_images
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
        terms = keywords.casefold().split()
        matches = [
            book for book in self.browse()
            if all(term in f"{book.title} {book.author} {book.category} {book.description}".casefold()
                   for term in terms)
        ]

        return rank_images(image, matches) if image is not None else matches

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
        if self.store.local_catalog is not None:
            self.store.local_catalog.save(book)
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
        if customer_id is not None and not any(scores.values()):
            return self.recommendations()
        return sorted(
            self.store.books.values(), key=lambda book: (-scores[book.id], book.id)
        )[:3]



    def read_alikes(self, book: Book) -> list[Book]:
        matches = []
        for candidate in self.store.books.values():
            if candidate.id == book.id:
                continue
            same_category = candidate.category.casefold() == book.category.casefold()
            same_author = (candidate.author.casefold() == book.author.casefold()
                           and book.author != "Unknown author")
            score = 2 * same_category + same_author
            if score:
                matches.append((-score, candidate.title.casefold(), candidate.id, candidate))
        return [candidate for _, _, _, candidate in sorted(matches)[:5]]