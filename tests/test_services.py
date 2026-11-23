import sqlite3
import tempfile
import unittest
from pathlib import Path

from bookstore import money
from bookstore.accounts import Accounts
from bookstore.activity import Activity
from bookstore.catalog import Catalog
from bookstore.models import Account, Book, Role
from bookstore.reviews import Reviews
from bookstore.storage import demo_store


def add_customer(store, account_id, role=Role.CUSTOMER, balance_cents=10_000):
    account = Account(account_id, role, balance_cents=balance_cents)
    store.accounts[account_id] = account
    return account


ADMIN = Account("admin", Role.ADMIN)


class MoneyTest(unittest.TestCase):
    def test_formats_cents(self):
        self.assertEqual(money(0), "$0.00")
        self.assertEqual(money(123_456), "$1,234.56")
        self.assertEqual(money(-350), "-$3.50")


class CheckoutTest(unittest.TestCase):
    """UC-06 purchase and the README demo walkthrough."""

    def setUp(self):
        self.store = demo_store()
        self.accounts = Accounts(self.store)

    def test_demo_walkthrough(self):
        sale = self.accounts.checkout("demo-customer", "B001")
        self.assertEqual((sale.total_cents, sale.balance_cents, sale.fine_cents), (800, 400, 0))
        self.assertFalse(sale.suspended)

        sale = self.accounts.checkout("demo-customer", "B002")
        self.assertEqual((sale.balance_cents, sale.fine_cents), (-350, 100))
        self.assertTrue(sale.suspended)
        self.assertEqual(len(self.store.purchases), 2)
        with self.assertRaises(PermissionError):
            self.accounts.deposit("demo-customer", 500)
        with self.assertRaises(PermissionError):
            self.accounts.checkout("demo-customer", "B003")

    def test_exact_balance_has_no_fine(self):
        self.store.accounts["demo-customer"].balance_cents = 800
        sale = self.accounts.checkout("demo-customer", "B001")
        self.assertEqual((sale.balance_cents, sale.fine_cents, sale.suspended), (0, 0, False))

    def test_vip_discount_rounds_to_nearest_cent(self):
        self.assertEqual(Accounts.purchase_price(800, Role.VIP), 720)
        self.assertEqual(Accounts.purchase_price(650, Role.VIP), 585)
        self.assertEqual(Accounts.purchase_price(5, Role.VIP), 5)
        self.assertEqual(Accounts.purchase_price(800, Role.CUSTOMER), 800)

    def test_promotion_after_more_than_three_purchases(self):
        self.store.accounts["demo-customer"].balance_cents = 10_000
        for book_id in ("B001", "B002", "B003"):
            self.assertIs(self.accounts.checkout("demo-customer", book_id).role, Role.CUSTOMER)
        self.assertIs(self.accounts.checkout("demo-customer", "B004").role, Role.VIP)

    def test_promotion_after_spending_more_than_200_dollars(self):
        self.store.books["BIG"] = Book("BIG", "Atlas", "A", "Maps", 2000, 20_001)
        self.store.accounts["demo-customer"].balance_cents = 30_000
        self.assertIs(self.accounts.checkout("demo-customer", "BIG").role, Role.VIP)

    def test_free_ebooks_cannot_be_bought(self):
        self.store.books["PG-1"] = Book("PG-1", "Free", "A", "C", None, 0, source_url="https://x")
        with self.assertRaises(ValueError):
            self.accounts.checkout("demo-customer", "PG-1")

    def test_deposit_requires_positive_integer_cents(self):
        for amount in (0, -1, 1.5):
            with self.assertRaises(ValueError):
                self.accounts.deposit("demo-customer", amount)
        self.assertEqual(self.accounts.deposit("demo-customer", 50), 1250)


class ReopenTest(unittest.TestCase):
    """UC-09 super-user reopening."""

    def setUp(self):
        self.store = demo_store()
        self.accounts = Accounts(self.store)
        self.suspended = Account("late", Role.VIP, balance_cents=-50, suspended=True)
        self.store.accounts["late"] = self.suspended

    def test_deposit_must_restore_positive_balance(self):
        with self.assertRaises(ValueError):
            self.accounts.reopen(ADMIN, "late", 50)
        self.assertTrue(self.suspended.suspended)
        self.assertEqual(self.accounts.reopen(ADMIN, "late", 75), 25)
        self.assertFalse(self.suspended.suspended)
        self.assertIs(self.suspended.role, Role.CUSTOMER)

    def test_requires_active_super_user(self):
        with self.assertRaises(PermissionError):
            self.accounts.reopen(self.store.accounts["demo-customer"], "late", 500)
        with self.assertRaises(PermissionError):
            self.accounts.reopen(Account("x", Role.ADMIN, suspended=True), "late", 500)

    def test_active_account_cannot_be_reopened(self):
        with self.assertRaises(ValueError):
            self.accounts.reopen(ADMIN, "demo-customer", 500)


class ReviewTest(unittest.TestCase):
    """UC-08 ratings and reviews, and the warning rules from UC-09."""

    def setUp(self):
        self.store = demo_store()
        self.store.taboo_terms = {"bad"}
        self.reviews = Reviews(self.store)

    def test_only_active_customers_can_review(self):
        for reviewer in ("@visitor", "nobody"):
            with self.assertRaises(PermissionError):
                self.reviews.submit(reviewer, "B001", 5, "Great")
        self.store.accounts["admin"] = ADMIN
        with self.assertRaises(PermissionError):
            self.reviews.submit("admin", "B001", 5, "Great")
        add_customer(self.store, "gone").suspended = True
        with self.assertRaises(PermissionError):
            self.reviews.submit("gone", "B001", 5, "Great")
        self.assertEqual(self.store.reviews, [])

    def test_one_review_per_customer_and_book(self):
        self.reviews.submit("demo-customer", "B001", 5, "Great")
        with self.assertRaises(ValueError):
            self.reviews.submit("demo-customer", "B001", 1, "Changed my mind")
        self.reviews.submit("demo-customer", "B002", 4, "Good")
        self.assertEqual(len(self.store.reviews), 2)

    def test_star_range(self):
        for stars in (0, 6, 4.5):
            with self.assertRaises(ValueError):
                self.reviews.submit("demo-customer", "B001", stars, "x")

    def test_masks_up_to_three_prohibited_words(self):
        review = self.reviews.submit("demo-customer", "B001", 2, "Bad plot, bad pacing, BAD end")
        self.assertEqual(review.comment, "* plot, * pacing, * end")
        self.assertEqual(self.store.warnings, {})

    def test_verified_purchase_flag(self):
        Accounts(self.store).checkout("demo-customer", "B001")
        self.assertTrue(self.reviews.submit("demo-customer", "B001", 5, "x").verified_purchase)
        self.assertFalse(self.reviews.submit("demo-customer", "B002", 5, "x").verified_purchase)

    def test_third_blocked_review_suspends_customer(self):
        for attempt in range(3):
            with self.assertRaises(ValueError):
                self.reviews.submit("demo-customer", "B001", 1, "bad bad bad bad")
        self.assertEqual(self.store.warnings["demo-customer"], 3)
        self.assertTrue(self.store.accounts["demo-customer"].suspended)
        self.assertEqual(self.store.reviews, [])

    def test_third_blocked_review_demotes_vip(self):
        vip = add_customer(self.store, "vip", Role.VIP)
        for attempt in range(3):
            with self.assertRaises(ValueError):
                self.reviews.submit("vip", "B001", 1, "bad bad bad bad")
        self.assertIs(vip.role, Role.CUSTOMER)
        self.assertFalse(vip.suspended)

    def test_order_status_uses_weighted_average(self):
        def rate(book_id, stars_list, buyers=()):
            for index, stars in enumerate(stars_list):
                reviewer = f"{book_id}-r{index}"
                add_customer(self.store, reviewer)
                if index in buyers:
                    self.store.purchase_counts[(reviewer, book_id)] = 1
                self.reviews.submit(reviewer, book_id, stars, "x")

        rate("B001", [5, 5, 5])
        self.assertEqual(self.reviews.order_status("B001"), "standard")
        rate("B002", [5, 5, 5, 5])
        self.assertEqual(self.reviews.order_status("B002"), "to-order")
        rate("B003", [1, 1, 1, 2])
        self.assertEqual(self.reviews.order_status("B003"), "no-order")
        # Average 3.0 unweighted, but a verified 1-star counts twice: (1*2+3+3+5)/5 = 2.6.
        rate("B004", [1, 3, 3, 5], buyers={0})
        self.assertEqual(self.reviews.order_status("B004"), "standard")

    def test_taboo_terms_require_super_user(self):
        with self.assertRaises(PermissionError):
            self.reviews.update_taboo_term(self.store.accounts["demo-customer"], "rude")
        self.reviews.update_taboo_term(ADMIN, "  Rude ")
        self.assertIn("rude", self.store.taboo_terms)
        with self.assertRaises(ValueError):
            self.reviews.update_taboo_term(ADMIN, "two words")
        self.reviews.update_taboo_term(ADMIN, "rude", remove=True)
        self.assertNotIn("rude", self.store.taboo_terms)


class CatalogTest(unittest.TestCase):
    """UC-02 browse, UC-03 search, UC-04 recommendations, UC-10, and read-alikes."""

    def setUp(self):
        self.store = demo_store()
        self.catalog = Catalog(self.store)

    def ids(self, books):
        return [book.id for book in books]

    def test_browse_and_search(self):
        self.assertEqual(self.ids(self.catalog.browse(category="science FICTION")), ["B002", "B003"])
        self.assertEqual(self.ids(self.catalog.browse(author="wells")), ["B003"])
        self.assertEqual(self.ids(self.catalog.browse(year=1813)), ["B001"])
        self.assertEqual(self.ids(self.catalog.search("shelley science")), ["B002"])
        self.assertEqual(self.catalog.search("nothing matches"), [])

    def test_personal_and_overall_recommendations(self):
        add_customer(self.store, "other")
        for _ in range(3):
            self.catalog.open_book("B004", "other")
        self.catalog.open_book("B003", "demo-customer")
        customer = self.store.accounts["demo-customer"]
        self.assertEqual(self.ids(self.catalog.recommendations(customer))[0], "B003")
        self.assertEqual(self.ids(self.catalog.recommendations(None))[:2], ["B004", "B003"])
        self.assertEqual(self.ids(self.catalog.recommendations(ADMIN))[:2], ["B004", "B003"])
        self.assertEqual(len(self.catalog.recommendations(None)), 3)

    def test_customer_without_history_gets_overall_ranking(self):
        self.catalog.open_book("B004", "@visitor")
        fresh = add_customer(self.store, "fresh")
        self.assertEqual(self.ids(self.catalog.recommendations(fresh))[0], "B004")

    def test_read_alikes(self):
        self.store.books["B005"] = Book("B005", "Emma", "Jane Austen", "Romance", 1815, 500)
        matches = self.ids(self.catalog.read_alikes(self.store.books["B002"]))
        self.assertEqual(matches, ["B003"])
        matches = self.ids(self.catalog.read_alikes(self.store.books["B001"]))
        self.assertEqual(matches, ["B005"])

    def test_add_book_validation(self):
        book = Book("NEW", "Title", "Author", "Category", 2020, 999)
        with self.assertRaises(PermissionError):
            self.catalog.add_book(self.store.accounts["demo-customer"], book)
        with self.assertRaises(ValueError):
            self.catalog.add_book(ADMIN, Book("B001", "Dup", "A", "C", 2020, 1))
        with self.assertRaises(ValueError):
            self.catalog.add_book(ADMIN, Book("X", "T", "A", "C", 2020, -1))
        self.catalog.add_book(ADMIN, book)
        self.assertIs(self.store.books["NEW"], book)


class ActivityTest(unittest.TestCase):
    """Transactional persistence of account activity."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "activity.sqlite3"
        self.store = demo_store()
        self.store.activity = Activity(self.path)
        self.store.activity.load(self.store)

    def tearDown(self):
        self.directory.cleanup()

    def reload(self):
        store = demo_store()
        store.activity = Activity(self.path)
        store.activity.load(store)
        return store

    def test_committed_changes_survive_restart(self):
        with self.store.change_activity():
            Accounts(self.store).checkout("demo-customer", "B001")
        saved = self.reload()
        self.assertEqual(saved.accounts["demo-customer"].balance_cents, 400)
        self.assertEqual(saved.purchase_counts[("demo-customer", "B001")], 1)
        self.assertEqual(len(saved.purchases), 1)

    def test_failed_operation_rolls_back(self):
        customer = self.store.accounts["demo-customer"]
        with self.assertRaises(RuntimeError):
            with self.store.change_activity():
                customer.balance_cents = 0
                raise RuntimeError("boom")
        self.assertEqual(customer.balance_cents, 1200)
        self.assertIs(self.store.accounts["demo-customer"], customer)

    def test_stale_writer_is_rejected(self):
        other = self.reload()
        with other.change_activity():
            Accounts(other).deposit("demo-customer", 100)
        with self.assertRaises(sqlite3.OperationalError):
            with self.store.change_activity():
                Accounts(self.store).deposit("demo-customer", 100)
        self.assertEqual(self.store.accounts["demo-customer"].balance_cents, 1200)


if __name__ == "__main__":
    unittest.main()
