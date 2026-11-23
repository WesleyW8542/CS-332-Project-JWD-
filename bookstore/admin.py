import re
import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from uuid import uuid4

from .catalog import Catalog
from .image_search import image_signature, read_image
from .models import Account, Book, Role
from .storage import Store


def add_book_dialog(parent: tk.Tk, catalog: Catalog, actor: Account) -> Book | None:
    window = tk.Toplevel(parent)
    window.title("Add a book")
    window.transient(parent)
    panel = ttk.Frame(window, padding=20)
    panel.pack(fill="both", expand=True)
    panel.columnconfigure(1, weight=1)
    fields = {}
    for row, label in enumerate(("Title", "Author", "Category", "Publication year", "Price ($)", "Description")):
        ttk.Label(panel, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=4)
        field = ttk.Entry(panel, width=35)
        field.grid(row=row, column=1, sticky="ew", pady=4)
        fields[label] = field

    error = tk.StringVar(window)
    ttk.Label(panel, textvariable=error, style="Warning.TLabel", wraplength=340).grid(
        row=7, column=0, columnspan=2, sticky="w", pady=(8, 4)
    )
    added = None
    cover = None
    cover_name = tk.StringVar(window, value="No cover selected")

    def choose_cover() -> None:
        nonlocal cover
        filename = filedialog.askopenfilename(
            parent=window, filetypes=[("Cover images", "*.jpg *.jpeg *.png")]
        )
        if not filename:
            return
        try:
            data = read_image(Path(filename))
            image_signature(data)
        except (OSError, ValueError) as exc:
            error.set(str(exc))
            return
        cover = data
        cover_name.set(Path(filename).name)
        error.set("")

    ttk.Button(panel, text="Attach cover", command=choose_cover).grid(row=6, column=0, sticky="w")
    ttk.Label(panel, textvariable=cover_name, wraplength=220).grid(row=6, column=1, sticky="w")

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
            description=fields["Description"].get().strip(),
            cover=cover,
            price_cents=int(dollars) * 100 + int(cents.ljust(2, "0")),
        )
        try:
            catalog.add_book(actor, book)
        except (ValueError, PermissionError) as exc:
            error.set(str(exc))
            return
        except sqlite3.Error as exc:
            error.set(f"Could not save the book. {exc}")
            return
        added = book
        window.destroy()

    actions = ttk.Frame(panel)
    actions.grid(row=8, column=0, columnspan=2, sticky="e")
    ttk.Button(actions, text="Cancel", command=window.destroy).pack(side="left", padx=(0, 8))
    ttk.Button(actions, text="Save book", style="Accent.TButton", command=save).pack(side="left")
    window.bind("<Return>", save)
    window.bind("<Escape>", lambda _event: window.destroy())
    fields["Title"].focus_set()
    window.wait_visibility()
    window.grab_set()
    parent.wait_window(window)
    return added


def edit_store_information(parent: tk.Tk, store: Store, actor: Account) -> None:
    if actor.role is not Role.ADMIN or actor.suspended:
        raise PermissionError("An active super-user is required.")
    window = tk.Toplevel(parent)
    window.title("Store and team information")
    window.transient(parent)
    panel = ttk.Frame(window, padding=16)
    panel.pack(fill="both", expand=True)
    ttk.Label(panel, text="Store information").pack(anchor="w")
    store_text = tk.Text(panel, width=55, height=5, wrap="word")
    store_text.pack(fill="both", expand=True, pady=(4, 8))
    store_text.insert("1.0", store.store_info)
    ttk.Label(panel, text="Team information").pack(anchor="w")
    team_text = tk.Text(panel, width=55, height=5, wrap="word")
    team_text.pack(fill="both", expand=True, pady=(4, 8))
    team_text.insert("1.0", store.team_info)
    feedback = tk.StringVar(window)
    ttk.Label(panel, textvariable=feedback, style="Warning.TLabel", wraplength=420).pack(anchor="w")

    def save() -> None:
        try:
            with store.change_activity():
                store.store_info = store_text.get("1.0", "end-1c").strip()
                store.team_info = team_text.get("1.0", "end-1c").strip()
        except sqlite3.Error as error:
            feedback.set(str(error))
            return
        window.destroy()

    ttk.Button(panel, text="Save information", command=save).pack(anchor="e")
    window.grab_set()
    parent.wait_window(window)