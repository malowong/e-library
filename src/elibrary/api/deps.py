from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from elibrary import security
from elibrary.config import Settings, get_settings
from elibrary.db.repositories import (
    SqlAlchemyBookRepository,
    SqlAlchemyLoanRepository,
    SqlAlchemyUserRepository,
)
from elibrary.db.session import session_scope
from elibrary.domain.errors import InvalidToken
from elibrary.domain.policy import LendingPolicy
from elibrary.domain.repositories import BookRepository, LoanRepository, UserRepository
from elibrary.domain.services import AuthService, CatalogueService, LendingService

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(session_scope)]


def get_user_repository(session: SessionDep) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def get_book_repository(session: SessionDep) -> BookRepository:
    return SqlAlchemyBookRepository(session)


def get_loan_repository(session: SessionDep) -> LoanRepository:
    return SqlAlchemyLoanRepository(session)


def get_auth_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    return AuthService(users)


def get_catalogue_service(
    books: Annotated[BookRepository, Depends(get_book_repository)],
) -> CatalogueService:
    return CatalogueService(books)


def get_lending_service(
    books: Annotated[BookRepository, Depends(get_book_repository)],
    loans: Annotated[LoanRepository, Depends(get_loan_repository)],
    settings: SettingsDep,
) -> LendingService:
    policy = LendingPolicy(
        max_active_loans=settings.max_active_loans,
        loan_period_days=settings.loan_period_days,
    )
    return LendingService(books, loans, policy)


_bearer = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    settings: SettingsDep,
) -> UUID:
    if credentials is None:
        raise InvalidToken()
    return security.read_access_token(credentials.credentials, settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CatalogueServiceDep = Annotated[CatalogueService, Depends(get_catalogue_service)]
LendingServiceDep = Annotated[LendingService, Depends(get_lending_service)]
CurrentUserId = Annotated[UUID, Depends(get_current_user_id)]
