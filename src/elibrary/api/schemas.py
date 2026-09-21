from dataclasses import asdict
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from elibrary.domain.models import Book, Loan, User


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: str

    @classmethod
    def of(cls, user: User) -> "UserResponse":
        return cls(id=user.id, email=user.email)


class BookResponse(BaseModel):
    id: UUID
    title: str
    author: str
    isbn: str
    published_year: int | None
    total_copies: int
    available_copies: int

    @classmethod
    def of(cls, book: Book) -> "BookResponse":
        return cls(**asdict(book))


class BorrowRequest(BaseModel):
    book_id: UUID


class LoanResponse(BaseModel):
    id: UUID
    book_id: UUID
    borrowed_at: datetime
    due_at: datetime
    returned_at: datetime | None

    @classmethod
    def of(cls, loan: Loan) -> "LoanResponse":
        return cls(
            id=loan.id,
            book_id=loan.book_id,
            borrowed_at=loan.borrowed_at,
            due_at=loan.due_at,
            returned_at=loan.returned_at,
        )


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody
