import re

from .models import Account, Review, Role
from .storage import Store


class Reviews:
    def __init__(self, store: Store):
        self.store = store

    def reviewer(self, reviewer_id: str) -> Account:
        account = self.store.accounts.get(reviewer_id)
        if account is None or account.suspended or account.role not in (Role.CUSTOMER, Role.VIP):
            raise PermissionError("Sign in as an active customer to post a review.")
        return account

    def submit(self, reviewer_id: str, book_id: str, stars: int, comment: str) -> Review:
        account = self.reviewer(reviewer_id)
        if book_id not in self.store.books:
            raise ValueError("Book does not exist.")
        if type(stars) is not int or not 1 <= stars <= 5:
            raise ValueError("Choose between one and five stars.")
        if any(review.book_id == book_id and review.reviewer_id == account.id
               for review in self.store.reviews):
            raise ValueError("You have already reviewed this book.")

        taboo_words = [
            word for word in re.findall(r"\b\w+\b", comment)
            if word.casefold() in self.store.taboo_terms
        ]
        if len(taboo_words) > 3:
            warnings = self.store.warnings.get(reviewer_id, 0) + 1
            self.store.warnings[reviewer_id] = warnings
            if warnings > 2:
                if account.role is Role.VIP:
                    account.role = Role.CUSTOMER
                elif account.role is Role.CUSTOMER:
                    account.suspended = True
            raise ValueError("Comment blocked. A warning was recorded.")

        masked = re.sub(
            r"\b\w+\b",
            lambda match: "*" if match[0].casefold() in self.store.taboo_terms else match[0],
            comment,
        )
        verified = self.store.purchase_counts.get((reviewer_id, book_id), 0) > 0
        review = Review(book_id, reviewer_id, stars, masked, verified)
        self.store.reviews.append(review)
        return review

    def order_status(self, book_id: str) -> str:
        reviews = [review for review in self.store.reviews if review.book_id == book_id]
        if len(reviews) <= 3:
            return "standard"
        points = sum(review.stars * (2 if review.verified_purchase else 1) for review in reviews)
        weight = sum(2 if review.verified_purchase else 1 for review in reviews)
        if points < 2 * weight:
            return "no-order"
        if points > 4 * weight:
            return "to-order"
        return "standard"

    def update_taboo_term(self, actor: Account, term: str, *, remove: bool = False) -> None:
        if actor.role is not Role.ADMIN or actor.suspended:
            raise PermissionError("An active super-user is required.")
        term = term.strip().casefold()
        if not re.fullmatch(r"\w+", term):
            raise ValueError("Enter a single word.")
        if remove:
            self.store.taboo_terms.discard(term)
        else:
            self.store.taboo_terms.add(term)

