from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from elibrary.db.orm import BookRow, LoanRow, UserRow
from elibrary.domain.errors import LoanNotFound
from elibrary.domain.models import Book, Loan, User
from elibrary.domain.repositories import BookRepository, LoanRepository, UserRepository


def _to_user(row: UserRow) -> User:
    return User(id=row.id, email=row.email, password_hash=row.password_hash)


def _to_book(row: BookRow, on_loan: int) -> Book:
    return Book(
        id=row.id,
        title=row.title,
        author=row.author,
        isbn=row.isbn,
        published_year=row.published_year,
        total_copies=row.total_copies,
        available_copies=max(row.total_copies - on_loan, 0),
    )


def _to_loan(row: LoanRow) -> Loan:
    return Loan(
        id=row.id,
        user_id=row.user_id,
        book_id=row.book_id,
        borrowed_at=row.borrowed_at,
        due_at=row.due_at,
        returned_at=row.returned_at,
    )


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user: User) -> User:
        self._session.add(
            UserRow(id=user.id, email=user.email, password_hash=user.password_hash)
        )
        await self._session.flush()
        return user

    async def get_by_email(self, email: str) -> User | None:
        row = await self._session.scalar(select(UserRow).where(UserRow.email == email))
        return _to_user(row) if row else None


class SqlAlchemyBookRepository(BookRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _select_with_availability(self) -> Select:
        on_loan = (
            select(LoanRow.book_id, func.count().label("on_loan"))
            .where(LoanRow.returned_at.is_(None))
            .group_by(LoanRow.book_id)
            .subquery()
        )
        return select(BookRow, func.coalesce(on_loan.c.on_loan, 0)).outerjoin(
            on_loan, on_loan.c.book_id == BookRow.id
        )

    async def list_all(self) -> list[Book]:
        stmt = self._select_with_availability().order_by(BookRow.title)
        result = await self._session.execute(stmt)
        return [_to_book(row, on_loan) for row, on_loan in result.all()]

    async def get(self, book_id: UUID) -> Book | None:
        stmt = self._select_with_availability().where(BookRow.id == book_id)
        result = (await self._session.execute(stmt)).first()
        return _to_book(*result) if result else None

    async def get_for_update(self, book_id: UUID) -> Book | None:
        row = await self._session.get(BookRow, book_id, with_for_update=True)
        if row is None:
            return None
        on_loan = await self._session.scalar(
            select(func.count())
            .select_from(LoanRow)
            .where(LoanRow.book_id == book_id, LoanRow.returned_at.is_(None))
        )
        return _to_book(row, on_loan or 0)


class SqlAlchemyLoanRepository(LoanRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, loan: Loan) -> Loan:
        self._session.add(
            LoanRow(
                id=loan.id,
                user_id=loan.user_id,
                book_id=loan.book_id,
                borrowed_at=loan.borrowed_at,
                due_at=loan.due_at,
                returned_at=loan.returned_at,
            )
        )
        await self._session.flush()
        return loan

    async def get(self, loan_id: UUID) -> Loan | None:
        row = await self._session.get(LoanRow, loan_id)
        return _to_loan(row) if row else None

    async def list_for_user(self, user_id: UUID, *, active_only: bool) -> list[Loan]:
        stmt = select(LoanRow).where(LoanRow.user_id == user_id)
        if active_only:
            stmt = stmt.where(LoanRow.returned_at.is_(None))
        rows = await self._session.scalars(stmt.order_by(LoanRow.borrowed_at.desc()))
        return [_to_loan(row) for row in rows]

    async def count_active_for_user(self, user_id: UUID) -> int:
        count = await self._session.scalar(
            select(func.count())
            .select_from(LoanRow)
            .where(LoanRow.user_id == user_id, LoanRow.returned_at.is_(None))
        )
        return count or 0

    async def find_active(self, user_id: UUID, book_id: UUID) -> Loan | None:
        row = await self._session.scalar(
            select(LoanRow).where(
                LoanRow.user_id == user_id,
                LoanRow.book_id == book_id,
                LoanRow.returned_at.is_(None),
            )
        )
        return _to_loan(row) if row else None

    async def mark_returned(self, loan_id: UUID, returned_at: datetime) -> Loan:
        row = await self._session.get(LoanRow, loan_id, with_for_update=True)
        if row is None:
            raise LoanNotFound(loan_id)
        row.returned_at = returned_at
        await self._session.flush()
        return _to_loan(row)
