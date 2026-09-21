from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    email: str
    password_hash: str


@dataclass(frozen=True, slots=True)
class Book:
    id: UUID
    title: str
    author: str
    isbn: str
    published_year: int | None
    total_copies: int
    available_copies: int

    @property
    def is_available(self) -> bool:
        return self.available_copies > 0


@dataclass(frozen=True, slots=True)
class Loan:
    id: UUID
    user_id: UUID
    book_id: UUID
    borrowed_at: datetime
    due_at: datetime
    returned_at: datetime | None

    @property
    def is_active(self) -> bool:
        return self.returned_at is None
