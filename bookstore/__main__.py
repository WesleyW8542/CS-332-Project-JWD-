import argparse

from .accounts import Accounts
from .catalog import Catalog
from .storage import demo_store


def money(cents: int) -> str:
    return f"${cents / 100:,.2f}"


def launch() -> None:
    import tkinter as tk
    from tkinter import ttk

    store = demo_store()
    catalog = Catalog(store)
    accounts = Accounts(store)
    customer = store.accounts["demo-customer"]
    root = tk.Tk()
    root.title("Smart Bookstore")
    root.minsize(520, 330)
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Smart Bookstore", font=("TkDefaultFont", 20)).pack(anchor="w")
    status = tk.StringVar()
    ttk.Label(frame, textvariable=status, wraplength=480).pack(anchor="w", pady=8)
    query = ttk.Entry(frame)
    query.pack(fill="x")
    results = tk.Listbox(frame, height=7, exportselection=False)
    results.pack(fill="both", expand=True, pady=8)
    visible_books = []

    def show(books):
        visible_books[:] = books
        results.delete(0, tk.END)
        for book in books:
            results.insert(tk.END, f"{book.title} | {book.author} | {money(book.price_cents)}")

    def search(_event=None):
        books = catalog.search(query.get())
        show(books)
        status.set(f"{len(books)} result(s) | Demo balance {money(customer.balance_cents)}")

    def checkout():
        selected = results.curselection()
        if not selected:
            status.set("Select a book to purchase.")
            return
        book = visible_books[selected[0]]
        try:
            sale = accounts.checkout(customer.id, book.id)
        except PermissionError as error:
            status.set(str(error))
            return
        if sale.purchased:
            message = f"Purchased {book.title} for {money(sale.total_cents)}."
        else:
            message = f"Insufficient funds. Fine: {money(sale.fine_cents)}."
        if sale.suspended:
            message += " Account suspended. Contact a super-user to reopen it."
        status.set(f"{message} Balance: {money(sale.balance_cents)}")

    buttons = ttk.Frame(frame)
    buttons.pack(fill="x")
    ttk.Button(buttons, text="Search", command=search).pack(side="left")
    ttk.Button(buttons, text="Buy selected book", command=checkout).pack(side="right")
    query.bind("<Return>", search)
    show(catalog.recommendations(customer))
    status.set(f"Recommended books | Demo balance {money(customer.balance_cents)}")
    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Smart Bookstore prototype")
    parser.add_argument("--list-books", action="store_true", help="List demo books without a GUI")
    args = parser.parse_args()
    if args.list_books:
        for book in Catalog(demo_store()).browse():
            print(f"{book.title} | {book.author} | {money(book.price_cents)}")
    else:
        launch()


if __name__ == "__main__":
    main()

