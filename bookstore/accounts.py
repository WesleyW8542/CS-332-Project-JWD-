from .models import Account, CheckoutResult, Role
from .storage import Store


class Accounts:
    def __init__(self, store: Store):
        self.store = store

    def deposit(self, account_id: str, amount_cents: int) -> int:
        account = self._active_customer(account_id)
        self._validate_amount(amount_cents)
        account.balance_cents += amount_cents
        return account.balance_cents

    def reopen(self, actor: Account, account_id: str, amount_cents: int) -> int:
        if actor.role is not Role.ADMIN or actor.suspended:
            raise PermissionError("An active super-user is required.")
        self._validate_amount(amount_cents)
        account = self.store.accounts[account_id]
        if not account.suspended or account.balance_cents + amount_cents <= 0:
            raise ValueError("A suspended account must reach a positive balance.")
        account.balance_cents += amount_cents
        account.suspended = False
        return account.balance_cents

    def checkout(self, account_id: str, book_id: str) -> CheckoutResult:
        """Buy one copy in the in-memory demo."""
        account = self._active_customer(account_id)
        book = self.store.books[book_id]
        if book.source_url:
            raise ValueError("Open this free ebook from its source page.")
        total = book.price_cents
        if account.role is Role.VIP:
            total = (total * 90 + 50) // 100

        fine = 0
        purchased = total <= account.balance_cents
        if purchased:
            account.balance_cents -= total
            account.purchases += 1
            account.spent_cents += total
            key = (account_id, book_id)
            self.store.purchase_counts[key] = self.store.purchase_counts.get(key, 0) + 1
            if account.role is Role.CUSTOMER and (
                account.purchases > 3 or account.spent_cents > 20_000
            ):
                account.role = Role.VIP
        else:
            fine = 100
            account.balance_cents -= fine
            account.suspended = account.balance_cents < 0

        return CheckoutResult(
            purchased, total, account.balance_cents, fine, account.suspended, account.role
        )

    def _active_customer(self, account_id: str) -> Account:
        account = self.store.accounts[account_id]
        if account.suspended or account.role not in (Role.CUSTOMER, Role.VIP):
            raise PermissionError("An active customer account is required.")
        return account

    @staticmethod
    def _validate_amount(amount_cents: int) -> None:
        if type(amount_cents) is not int or amount_cents <= 0:
            raise ValueError("Enter a positive deposit amount in cents.")

