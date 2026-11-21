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
    year: int
    price_cents: int


@dataclass
class Account:
    id: str
    role: Role
    balance_cents: int = 0
    purchases: int = 0
    spent_cents: int = 0
    suspended: bool = False


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

