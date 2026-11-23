import sqlite3
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from .models import Account, Book
from .reviews import Reviews


def show_reviews(parent, service: Reviews, book: Book, reviewer_id: str) -> None:
    window = tk.Toplevel(parent)
    window.title(f"Reviews — {book.title}")
    window.transient(parent)
    body = ttk.Frame(window, padding=16)
    body.pack(fill="both", expand=True)

    listing = tk.Text(body, width=56, height=9, wrap="word")
    listing.pack(fill="both", expand=True)
    summary = tk.StringVar(window)
    ttk.Label(body, textvariable=summary).pack(anchor="w")
    try:
        service.reviewer(reviewer_id)
        can_post = True
    except PermissionError:
        can_post = False
    feedback = tk.StringVar(window)
    if not can_post:
        ttk.Label(body, text="Sign in as an active customer to post a review.",
                  style="Muted.TLabel").pack(anchor="w", pady=(8, 0))
    else:
        ttk.Label(body, text="Stars").pack(anchor="w", pady=(8, 0))
        stars = ttk.Combobox(body, values=(1, 2, 3, 4, 5), state="readonly")
        stars.pack(anchor="w")
        stars.set("5")
        ttk.Label(body, text="Comment").pack(anchor="w", pady=(8, 0))
        comment = tk.Text(body, width=56, height=4, wrap="word")
        comment.pack(fill="x")
        ttk.Label(body, textvariable=feedback, wraplength=400).pack(anchor="w", pady=6)

    def refresh() -> None:
        reviews = [review for review in service.store.reviews if review.book_id == book.id]
        listing.configure(state="normal")
        listing.delete("1.0", tk.END)
        if not reviews:
            listing.insert("1.0", "No reviews yet.")
        for review in reviews:
            verified = " · verified purchase" if review.verified_purchase else ""
            listing.insert(tk.END, f"{review.stars}/5{verified}\n{review.comment}\n\n")
        listing.configure(state="disabled")
        if reviews:
            weights = [2 if review.verified_purchase else 1 for review in reviews]
            average = sum(review.stars * weight for review, weight in zip(reviews, weights)) / sum(weights)
            summary.set(f"{len(reviews)} ratings · weighted average {average:.1f}/5")
        else:
            summary.set("0 ratings")

    def submit() -> None:
        try:
            with service.store.change_activity():
                try:
                    service.submit(reviewer_id, book.id, int(stars.get()), comment.get("1.0", "end-1c"))
                except (ValueError, PermissionError) as error:
                    feedback.set(str(error))
                    return
        except sqlite3.Error as error:
            feedback.set(str(error))
            return
        feedback.set("Review posted.")
        comment.delete("1.0", tk.END)
        refresh()

    if can_post:
        ttk.Button(body, text="Post review", command=submit).pack(anchor="e")
    refresh()
    window.grab_set()
    parent.wait_window(window)


def manage_terms(parent, service: Reviews, admin: Account) -> None:
    window = tk.Toplevel(parent)
    window.title("Prohibited words")
    window.transient(parent)
    body = ttk.Frame(window, padding=16)
    body.pack(fill="both", expand=True)
    words = tk.Listbox(body, width=30)
    words.pack(fill="both", expand=True)

    def refresh() -> None:
        words.delete(0, tk.END)
        for term in sorted(service.store.taboo_terms):
            words.insert(tk.END, term)

    def change(remove: bool) -> None:
        selection = words.curselection()
        if remove:
            if not selection:
                return
            term = words.get(selection[0])
        else:
            term = simpledialog.askstring("Prohibited words", "Enter one word.", parent=window)
            if term is None:
                return
        try:
            with service.store.change_activity():
                service.update_taboo_term(admin, term, remove=remove)
        except (ValueError, PermissionError, sqlite3.Error) as error:
            messagebox.showerror("Prohibited words", str(error), parent=window)
            return
        refresh()

    ttk.Button(body, text="Add word", command=lambda: change(False)).pack(side="left", pady=8)
    ttk.Button(body, text="Remove selected", command=lambda: change(True)).pack(side="right", pady=8)
    refresh()
    window.grab_set()
    parent.wait_window(window)


def show_order_lists(parent, service: Reviews) -> None:
    groups: dict[str, list[str]] = {"to-order": [], "no-order": []}
    reviewed_ids = {review.book_id for review in service.store.reviews}
    for book_id in reviewed_ids:
        book = service.store.books.get(book_id)
        if book:
            status = service.order_status(book_id)
            if status in groups:
                groups[status].append(book.title)
    text = "\n\n".join(
        heading + "\n" + ("\n".join(sorted(titles)) or "No titles")
        for heading, titles in groups.items()
    )
    messagebox.showinfo("Order lists", text, parent=parent)
