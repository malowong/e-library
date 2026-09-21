from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from elibrary.domain.models import Book, Loan, User


class UserRepository(ABC):
    @abstractmethod
    async def add(self, user: User) -> User: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...


class BookRepository(ABC):
    @abstractmethod
    async def list_all(self) -> list[Book]: ...

    @abstractmethod
    async def get(self, book_id: UUID) -> Book | None: ...

    @abstractmethod
    async def get_for_update(self, book_id: UUID) -> Book | None:
        """Same as get(), but holds a row lock until the transaction ends."""


class LoanRepository(ABC):
    @abstractmethod
    async def add(self, loan: Loan) -> Loan: ...

    @abstractmethod
    async def get(self, loan_id: UUID) -> Loan | None: ...

    @abstractmethod
    async def list_for_user(self, user_id: UUID, *, active_only: bool) -> list[Loan]: ...

    @abstractmethod
    async def count_active_for_user(self, user_id: UUID) -> int: ...

    @abstractmethod
    async def find_active(self, user_id: UUID, book_id: UUID) -> Loan | None: ...

    @abstractmethod
    async def mark_returned(self, loan_id: UUID, returned_at: datetime) -> Loan: ...
