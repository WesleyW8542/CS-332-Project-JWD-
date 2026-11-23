import re
import sqlite3
from tkinter import messagebox, simpledialog

from . import money
from .accounts import Accounts
from .models import Account


def ask_amount(parent, title: str, prompt: str) -> int | None:
    while True:
        entry = simpledialog.askstring(title, prompt, parent=parent)
        if entry is None:
            return None
        entry = entry.strip()
        if re.fullmatch(r"[0-9]{1,7}(?:\.[0-9]{1,2})?", entry):
            dollars, _, cents = entry.partition(".")
            amount = int(dollars) * 100 + int(cents.ljust(2, "0"))
            if amount > 0:
                return amount
        messagebox.showerror(title, "Enter a positive dollar amount, such as 5.00.", parent=parent)


def deposit_funds(parent, accounts: Accounts, customer: Account) -> str | None:
    amount = ask_amount(parent, "Add funds", "Enter the deposit amount in dollars.")
    if amount is None:
        return None
    try:
        with accounts.store.change_activity():
            balance = accounts.deposit(customer.id, amount)
    except (ValueError, PermissionError, sqlite3.Error) as error:
        messagebox.showerror("Add funds", str(error), parent=parent)
        return None
    return f"Added {money(amount)}. New balance: {money(balance)}."


def reopen_account(parent, accounts: Accounts, admin: Account) -> str | None:
    suspended = [account for account in accounts.store.accounts.values() if account.suspended]
    if not suspended:
        messagebox.showinfo("Reopen account", "There are no suspended accounts.", parent=parent)
        return None
    options = {account.id: account for account in suspended}
    choices = "\n".join(f"{account.id} ({money(account.balance_cents)})" for account in suspended)
    selected = simpledialog.askstring(
        "Reopen account", f"Enter a suspended account ID:\n{choices}", parent=parent
    )
    if selected is None:
        return None
    account = options.get(selected.strip())
    if account is None:
        messagebox.showerror("Reopen account", "Choose a listed account ID.", parent=parent)
        return None
    amount = ask_amount(
        parent, "Reopen account", "Enter a deposit in dollars that brings the balance above zero."
    )
    if amount is None:
        return None
    try:
        with accounts.store.change_activity():
            balance = accounts.reopen(admin, account.id, amount)
    except (ValueError, PermissionError, sqlite3.Error) as error:
        messagebox.showerror("Reopen account", str(error), parent=parent)
        return None
    return f"Reopened {account.id}. New balance: {money(balance)}."


def show_account(parent, accounts: Accounts, customer: Account) -> None:
    store = accounts.store
    status = "Suspended" if customer.suspended else "Active"
    lines = [
        f"Account: {customer.id}",
        f"Role: {customer.role.value}",
        f"Status: {status}",
        f"Balance: {money(customer.balance_cents)}",
        f"Warnings: {store.warnings.get(customer.id, 0)}",
        "",
        "Purchase history",
    ]
    history = []
    for purchase in reversed(store.purchases):
        if purchase.account_id != customer.id:
            continue
        book = store.books.get(purchase.book_id)
        title = book.title if book else purchase.book_id
        fine = f" + {money(purchase.fine_cents)} fine" if purchase.fine_cents else ""
        history.append(f"{purchase.purchased_at[:10]}   {title}   {money(purchase.price_cents)}{fine}")
    messagebox.showinfo("My account", "\n".join(lines + (history or ["No purchases yet."])), parent=parent)