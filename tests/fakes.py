from dataclasses import replace
from datetime import datetime
from uuid import UUID, uuid4

from elibrary.domain.errors import LoanNotFound
from elibrary.domain.models import Book, Loan, User
from elibrary.domain.repositories import BookRepository, LoanRepository, UserRepository


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self.users: dict[UUID, User] = {}

    async def add(self, user: User) -> User:
        self.users[user.id] = user
        return user

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.users.values() if u.email == email), None)


class InMemoryBookRepository(BookRepository):
    """Availability is derived from the loan repository, mirroring the SQL implementation."""

    def __init__(self, loans: "InMemoryLoanRepository") -> None:
        self.books: dict[UUID, Book] = {}
        self._loans = loans

    def seed(self, title: str = "A Book", total_copies: int = 1) -> Book:
        book = Book(
            id=uuid4(),
            title=title,
            author="Author",
            isbn=str(uuid4())[:20],
            published_year=2020,
            total_copies=total_copies,
            available_copies=total_copies,
        )
        self.books[book.id] = book
        return book

    def _with_availability(self, book: Book) -> Book:
        on_loan = sum(
            1 for loan in self._loans.loans.values() if loan.book_id == book.id and loan.is_active
        )
        return replace(book, available_copies=max(book.total_copies - on_loan, 0))

    async def list_all(self) -> list[Book]:
        ordered = sorted(self.books.values(), key=lambda b: b.title)
        return [self._with_availability(book) for book in ordered]

    async def get(self, book_id: UUID) -> Book | None:
        book = self.books.get(book_id)
        return self._with_availability(book) if book else None

    async def get_for_update(self, book_id: UUID) -> Book | None:
        return await self.get(book_id)


class InMemoryLoanRepository(LoanRepository):
    def __init__(self) -> None:
        self.loans: dict[UUID, Loan] = {}

    async def add(self, loan: Loan) -> Loan:
        self.loans[loan.id] = loan
        return loan

    async def get(self, loan_id: UUID) -> Loan | None:
        return self.loans.get(loan_id)

    async def list_for_user(self, user_id: UUID, *, active_only: bool) -> list[Loan]:
        return [
            loan
            for loan in sorted(self.loans.values(), key=lambda x: x.borrowed_at, reverse=True)
            if loan.user_id == user_id and (loan.is_active or not active_only)
        ]

    async def count_active_for_user(self, user_id: UUID) -> int:
        return sum(1 for loan in self.loans.values() if loan.user_id == user_id and loan.is_active)

    async def find_active(self, user_id: UUID, book_id: UUID) -> Loan | None:
        return next(
            (
                loan
                for loan in self.loans.values()
                if loan.user_id == user_id and loan.book_id == book_id and loan.is_active
            ),
            None,
        )

    async def mark_returned(self, loan_id: UUID, returned_at: datetime) -> Loan:
        loan = self.loans.get(loan_id)
        if loan is None:
            raise LoanNotFound(loan_id)
        updated = replace(loan, returned_at=returned_at)
        self.loans[loan_id] = updated
        return updated
