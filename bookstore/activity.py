from contextlib import closing, contextmanager
from dataclasses import asdict
import json
from pathlib import Path
import sqlite3

from .models import Account, PurchaseRecord, Review, Role

ACTIVITY_PATH = Path(__file__).resolve().parent.parent / "bookstore_activity.sqlite3"


class Activity:
    def __init__(self, path: Path = ACTIVITY_PATH):
        self.path = path
        self.revision = 0

    @staticmethod
    def prepare(connection: sqlite3.Connection) -> None:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS activity ("
            "id INTEGER PRIMARY KEY CHECK (id = 1), revision INTEGER NOT NULL, state TEXT NOT NULL)"
        )

    def load(self, store) -> None:
        with closing(sqlite3.connect(self.path)) as connection:
            self.prepare(connection)
            row = connection.execute("SELECT revision, state FROM activity WHERE id = 1").fetchone()
        if row:
            self.revision, state = row
            self.restore(store, json.loads(state))

    @staticmethod
    def snapshot(store) -> dict:
        return {
            "accounts": {key: asdict(value) for key, value in store.accounts.items()},
            "views": [[*key, count] for key, count in store.browse_counts.items()],
            "purchases": [[*key, count] for key, count in store.purchase_counts.items()],
            "receipts": [asdict(purchase) for purchase in store.purchases],
            "reviews": [asdict(review) for review in store.reviews],
            "taboo": sorted(store.taboo_terms),
            "warnings": dict(store.warnings),
            "voices": dict(store.voice_profiles),
            "store_info": store.store_info,
            "team_info": store.team_info,
        }

    @staticmethod
    def restore(store, state: dict) -> None:
        accounts = {}
        for account_id, fields in state["accounts"].items():
            account = store.accounts.get(account_id)
            fields = {**fields, "role": Role(fields["role"])}
            if account is None:
                account = Account(**fields)
            else:
                for key, value in fields.items():
                    setattr(account, key, value)
            accounts[account_id] = account
        store.accounts = accounts
        store.browse_counts = {(viewer, book): count for viewer, book, count in state["views"]}
        store.purchase_counts = {(viewer, book): count for viewer, book, count in state["purchases"]}
        store.purchases = [PurchaseRecord(**record) for record in state.get("receipts", [])]
        store.reviews = [Review(**review) for review in state["reviews"]]
        store.taboo_terms = set(state["taboo"])
        store.warnings = state["warnings"]
        store.voice_profiles = state["voices"]
        store.store_info = state.get("store_info", "")
        store.team_info = state.get("team_info", "")

    @contextmanager
    def change(self, store):
        before = self.snapshot(store)
        try:
            yield
            after = self.snapshot(store)
            if after != before:
                self.save(after)
        except Exception:
            self.restore(store, before)
            raise

    def save(self, state: dict) -> None:
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            self.prepare(connection)
            row = connection.execute("SELECT revision FROM activity WHERE id = 1").fetchone()
            if (row[0] if row else 0) != self.revision:
                raise sqlite3.OperationalError("Another bookstore window saved changes. Restart this window.")
            revision = self.revision + 1
            connection.execute(
                "INSERT OR REPLACE INTO activity(id, revision, state) VALUES (1, ?, ?)",
                (revision, json.dumps(state)),
            )
        self.revision = revision
