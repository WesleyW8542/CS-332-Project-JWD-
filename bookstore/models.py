from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    VISITOR = "visitor"
    CUSTOMER = "registered customer"
    VIP = "VIP customer"
    ADMIN = "super-user"


@dataclass(frozen=True)
class Book:
    id: str
    title: str
    author: str
    category: str
    year: int | None
    price_cents: int
    source_url: str | None = None
    description: str = ""
    cover: bytes | None = None


@dataclass
class Account:
    id: str
    role: Role
    balance_cents: int = 0
    purchases: int = 0
    spent_cents: int = 0
    suspended: bool = False


@dataclass(frozen=True)
class PurchaseRecord:
    id: str
    account_id: str
    book_id: str
    purchased_at: str
    price_cents: int
    fine_cents: int


@dataclass(frozen=True)
class CheckoutResult:
    purchased: bool
    total_cents: int
    balance_cents: int
    fine_cents: int
    suspended: bool
    role: Role


@dataclass(frozen=True)
class Review:
    book_id: str
    reviewer_id: str
    stars: int
    comment: str
    verified_purchase: bool


@dataclass(frozen=True)
class ChatAnswer:
    text: str
    source: str

