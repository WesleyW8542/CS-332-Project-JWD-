import re
import tkinter as tk
from tkinter import ttk
from uuid import uuid4

from .catalog import Catalog
from .models import Account, Book


def add_book_dialog(parent: tk.Tk, catalog: Catalog, actor: Account) -> Book | None:
    window = tk.Toplevel(parent)
    window.title("Add a book")
    window.transient(parent)
    panel = ttk.Frame(window, padding=20)
    panel.pack(fill="both", expand=True)
    panel.columnconfigure(1, weight=1)
    fields = {}
    for row, label in enumerate(("Title", "Author", "Category", "Publication year", "Price ($)")):
        ttk.Label(panel, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=4)
        field = ttk.Entry(panel, width=35)
        field.grid(row=row, column=1, sticky="ew", pady=4)
        fields[label] = field

    error = tk.StringVar(window)
    ttk.Label(panel, textvariable=error, style="Warning.TLabel", wraplength=340).grid(
        row=5, column=0, columnspan=2, sticky="w", pady=(8, 4)
    )
    added = None

    def save(_event=None) -> None:
        nonlocal added
        year = fields["Publication year"].get().strip()
        price = fields["Price ($)"].get().strip()
        if not re.fullmatch(r"[0-9]{1,4}", year) or int(year) == 0:
            error.set("Enter a publication year between 1 and 9999.")
            return
        if not re.fullmatch(r"[0-9]{1,7}(?:\.[0-9]{1,2})?", price):
            error.set("Enter a price such as 5 or 5.99.")
            return
        dollars, _, cents = price.partition(".")
        book = Book(
            id=f"LOCAL-{uuid4().hex}",
            title=fields["Title"].get().strip(),
            author=fields["Author"].get().strip(),
            category=fields["Category"].get().strip(),
            year=int(year),
            price_cents=int(dollars) * 100 + int(cents.ljust(2, "0")),
        )
        try:
            catalog.add_book(actor, book)
        except (ValueError, PermissionError) as exc:
            error.set(str(exc))
            return
        added = book
        window.destroy()

    actions = ttk.Frame(panel)
    actions.grid(row=6, column=0, columnspan=2, sticky="e")
    ttk.Button(actions, text="Cancel", command=window.destroy).pack(side="left", padx=(0, 8))
    ttk.Button(actions, text="Save book", style="Accent.TButton", command=save).pack(side="left")
    window.bind("<Return>", save)
    window.bind("<Escape>", lambda _event: window.destroy())
    fields["Title"].focus_set()
    window.wait_visibility()
    window.grab_set()
    parent.wait_window(window)
    return added
