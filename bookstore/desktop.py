import tkinter as tk
from tkinter import ttk

from . import money
from .accounts import Accounts
from .catalog import Catalog
from .models import Book
from .storage import demo_store


def configure_styles(root: tk.Tk) -> None:
    style = ttk.Style(root)
    style.theme_use("clam")
    ink = "#172d2a"
    muted = "#4b645c"
    paper = "#fbfaf6"
    white = "#ffffff"
    forest = "#17493c"
    style.configure(".", font=("Segoe UI", 10), foreground=ink, background=paper)
    style.configure("Page.TFrame", background=paper)
    style.configure("Header.TFrame", background=forest)
    style.configure("Header.TLabel", background=forest, foreground=white,
                    font=("Georgia", 25, "bold"))
    style.configure("Balance.TLabel", background=forest, foreground=white,
                    font=("Segoe UI", 12, "bold"))
    style.configure("Section.TLabel", font=("Georgia", 18, "bold"))
    style.configure("Muted.TLabel", foreground=muted)
    style.configure("Card.TFrame", background=white, relief="solid", borderwidth=1)
    style.configure("CardTitle.TLabel", background=white, font=("Georgia", 17, "bold"))
    style.configure("CardText.TLabel", background=white, foreground=muted)
    style.configure("CardPrice.TLabel", background=white, font=("Segoe UI", 13, "bold"))
    style.configure("TButton", padding=(14, 8))
    style.configure("Accent.TButton", background=forest, foreground=white)
    style.map("Accent.TButton",
              background=[("disabled", "#e2e8e3"), ("pressed", "#10372d"), ("active", "#216451")],
              foreground=[("disabled", "#4b645c")])
    style.configure("TEntry", fieldbackground=white, padding=8)
    style.configure("Treeview", background=white, fieldbackground=white, rowheight=38)
    style.configure("Treeview.Heading", background="#e8eee8", padding=(6, 8),
                    font=("Segoe UI", 10, "bold"))
    style.map("Treeview", background=[("selected", "#cde5d8")],
              foreground=[("selected", ink)])
    style.configure("Success.TLabel", foreground="#176140")
    style.configure("Warning.TLabel", foreground="#a02e20")


def launch() -> None:
    store = demo_store()
    catalog = Catalog(store)
    accounts = Accounts(store)
    customer = store.accounts["demo-customer"]
    root = tk.Tk()
    root.title("Smart Bookstore")
    root.geometry("1060x620")
    root.minsize(800, 490)
    configure_styles(root)

    header = ttk.Frame(root, style="Header.TFrame", padding=(26, 18))
    header.pack(fill="x")
    ttk.Label(header, text="Smart Bookstore", style="Header.TLabel").pack(side="left")
    balance = tk.StringVar()
    ttk.Label(header, textvariable=balance, style="Balance.TLabel").pack(side="right")

    page = ttk.Frame(root, style="Page.TFrame", padding=(26, 20))
    page.pack(fill="both", expand=True)
    page.columnconfigure(0, weight=1)
    page.rowconfigure(1, weight=1)

    toolbar = ttk.Frame(page)
    toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 18))
    ttk.Label(toolbar, text="Search by title, author, or category").pack(anchor="w", pady=(0, 5))
    search_row = ttk.Frame(toolbar)
    search_row.pack(fill="x")
    query = ttk.Entry(search_row)
    query.pack(side="left", fill="x", expand=True)

    catalog_panel = ttk.Frame(page)
    catalog_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 18))
    heading = tk.StringVar()
    ttk.Label(catalog_panel, textvariable=heading, style="Section.TLabel").pack(anchor="w")
    count = tk.StringVar()
    ttk.Label(catalog_panel, textvariable=count, style="Muted.TLabel").pack(anchor="w", pady=(3, 10))

    table = ttk.Frame(catalog_panel)
    table.pack(fill="both", expand=True)
    results = ttk.Treeview(table, columns=("title", "author", "price"),
                           show="headings", selectmode="browse")
    results.heading("title", text="Title", anchor="w")
    results.heading("author", text="Author", anchor="w")
    results.heading("price", text="List price", anchor="e")
    results.column("title", width=225, minwidth=140)
    results.column("author", width=135, minwidth=100)
    results.column("price", width=85, minwidth=85, stretch=False, anchor="e")
    scrollbar = ttk.Scrollbar(table, orient="vertical", command=results.yview)
    results.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    results.pack(side="left", fill="both", expand=True)

    card = ttk.Frame(page, style="Card.TFrame", padding=16, width=250)
    card.grid(row=1, column=1, sticky="nsew")
    card.grid_propagate(False)
    card.columnconfigure(0, weight=1)
    card.rowconfigure(4, weight=1)
    title = tk.StringVar()
    details = tk.StringVar()
    price = tk.StringVar()
    ttk.Label(card, text="BOOK DETAILS", style="CardText.TLabel").grid(row=0, sticky="w")
    ttk.Label(card, textvariable=title, style="CardTitle.TLabel", wraplength=210).grid(
        row=1, sticky="w", pady=(12, 6)
    )
    ttk.Label(card, textvariable=details, style="CardText.TLabel", wraplength=210).grid(
        row=2, sticky="w"
    )
    ttk.Label(card, textvariable=price, style="CardPrice.TLabel").grid(
        row=3, sticky="w", pady=(12, 0)
    )
    feedback = tk.StringVar()
    feedback_label = ttk.Label(page, textvariable=feedback, wraplength=720)
    feedback_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(12, 0))

    def update_balance() -> None:
        balance.set(f"Demo balance  {money(customer.balance_cents)}")

    def selected_book() -> Book | None:
        selection = results.selection()
        return store.books[selection[0]] if selection else None

    def update_details(_event=None) -> None:
        book = selected_book()
        title.set(book.title if book else "Select a book")
        details.set(f"{book.author}\n{book.category} · {book.year}" if book else "")
        price.set(f"List price  {money(book.price_cents)}" if book else "")
        buy.state(["!disabled"] if book and not customer.suspended else ["disabled"])

    def show(books: list[Book], label: str) -> None:
        children = results.get_children()
        if children:
            results.delete(*children)
        for book in books:
            results.insert("", "end", iid=book.id,
                           values=(book.title, book.author, money(book.price_cents)))
        heading.set(label)
        count.set(f"{len(books)} titles" if books else "No books match your search.")
        update_details()

    def search(_event=None) -> None:
        keywords = query.get().strip()
        show(catalog.search(keywords), "Search results" if keywords else "All books")

    def recommend() -> None:
        query.delete(0, tk.END)
        show(catalog.recommendations(customer), "Recommended books")

    def checkout() -> None:
        book = selected_book()
        if book is None:
            return
        try:
            sale = accounts.checkout(customer.id, book.id)
        except PermissionError as error:
            feedback_label.configure(style="Warning.TLabel")
            feedback.set(str(error))
            return
        if sale.purchased:
            message = f"Purchased {book.title} for {money(sale.total_cents)}."
        else:
            message = f"Insufficient funds. A {money(sale.fine_cents)} fine was charged."
        if sale.suspended:
            message += " Account suspended. Contact a super-user to reopen it."
        feedback_label.configure(style="Success.TLabel" if sale.purchased else "Warning.TLabel")
        feedback.set(message)
        update_balance()
        update_details()

    buy = ttk.Button(card, text="Buy selected book", style="Accent.TButton", command=checkout)
    buy.grid(row=5, sticky="ew")
    ttk.Button(search_row, text="Search", style="Accent.TButton", command=search).pack(
        side="left", padx=8
    )
    ttk.Button(search_row, text="Recommendations", command=recommend).pack(side="left")
    results.bind("<<TreeviewSelect>>", update_details)
    query.bind("<Return>", search)
    update_balance()
    recommend()
    query.focus_set()
    root.mainloop()

