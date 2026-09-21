from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from elibrary.api.deps import get_book_repository, get_loan_repository, get_user_repository
from elibrary.domain.policy import LendingPolicy
from elibrary.domain.services import LendingService
from elibrary.main import create_app
from tests.fakes import InMemoryBookRepository, InMemoryLoanRepository, InMemoryUserRepository


@pytest.fixture
def loan_repository() -> InMemoryLoanRepository:
    return InMemoryLoanRepository()


@pytest.fixture
def book_repository(loan_repository: InMemoryLoanRepository) -> InMemoryBookRepository:
    return InMemoryBookRepository(loan_repository)


@pytest.fixture
def user_repository() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def lending(
    book_repository: InMemoryBookRepository, loan_repository: InMemoryLoanRepository
) -> LendingService:
    return LendingService(book_repository, loan_repository, LendingPolicy(max_active_loans=2))


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def client(
    book_repository: InMemoryBookRepository,
    loan_repository: InMemoryLoanRepository,
    user_repository: InMemoryUserRepository,
) -> Iterator[TestClient]:
    """Real app, real services and real JWT auth; only the repositories are swapped."""
    app = create_app()
    app.dependency_overrides[get_book_repository] = lambda: book_repository
    app.dependency_overrides[get_loan_repository] = lambda: loan_repository
    app.dependency_overrides[get_user_repository] = lambda: user_repository
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    credentials = {"email": "reader@example.com", "password": "correct-horse"}
    client.post("/auth/register", json=credentials)
    token = client.post("/auth/login", json=credentials).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
