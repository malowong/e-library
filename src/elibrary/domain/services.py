from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from elibrary import security
from elibrary.domain.errors import (
    AlreadyBorrowed,
    BookNotFound,
    BorrowLimitReached,
    EmailAlreadyRegistered,
    InvalidCredentials,
    LoanAlreadyReturned,
    LoanNotFound,
    NoCopiesAvailable,
)
from elibrary.domain.models import Book, Loan, User
from elibrary.domain.policy import LendingPolicy
from elibrary.domain.repositories import BookRepository, LoanRepository, UserRepository


class CatalogueService:
    def __init__(self, books: BookRepository) -> None:
        self._books = books

    async def browse(self) -> list[Book]:
        return await self._books.list_all()

    async def get_book(self, book_id: UUID) -> Book:
        book = await self._books.get(book_id)
        if book is None:
            raise BookNotFound(book_id)
        return book


class LendingService:
    def __init__(
        self, books: BookRepository, loans: LoanRepository, policy: LendingPolicy
    ) -> None:
        self._books = books
        self._loans = loans
        self._policy = policy

    async def borrow(self, user_id: UUID, book_id: UUID) -> Loan:
        # Locked read: two concurrent borrows of the last copy must not both succeed.
        book = await self._books.get_for_update(book_id)
        if book is None:
            raise BookNotFound(book_id)
        if await self._loans.find_active(user_id, book_id) is not None:
            raise AlreadyBorrowed(book_id)
        if await self._loans.count_active_for_user(user_id) >= self._policy.max_active_loans:
            raise BorrowLimitReached(self._policy.max_active_loans)
        if not book.is_available:
            raise NoCopiesAvailable(book_id)

        borrowed_at = datetime.now(UTC)
        return await self._loans.add(
            Loan(
                id=uuid4(),
                user_id=user_id,
                book_id=book_id,
                borrowed_at=borrowed_at,
                due_at=borrowed_at + timedelta(days=self._policy.loan_period_days),
                returned_at=None,
            )
        )

    async def return_book(self, user_id: UUID, loan_id: UUID) -> Loan:
        loan = await self._loans.get(loan_id)
        # Another user's loan is reported as missing rather than forbidden.
        if loan is None or loan.user_id != user_id:
            raise LoanNotFound(loan_id)
        if not loan.is_active:
            raise LoanAlreadyReturned(loan_id)
        return await self._loans.mark_returned(loan_id, datetime.now(UTC))

    async def list_loans(self, user_id: UUID, *, active_only: bool = True) -> list[Loan]:
        return await self._loans.list_for_user(user_id, active_only=active_only)


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def register(self, email: str, password: str) -> User:
        email = email.strip().lower()
        if await self._users.get_by_email(email) is not None:
            raise EmailAlreadyRegistered(email)
        return await self._users.add(
            User(id=uuid4(), email=email, password_hash=security.hash_password(password))
        )

    async def authenticate(self, email: str, password: str) -> User:
        user = await self._users.get_by_email(email.strip().lower())
        if user is None or not security.verify_password(password, user.password_hash):
            raise InvalidCredentials()
        return user
