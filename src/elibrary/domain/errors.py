from uuid import UUID


class DomainError(Exception):
    """Base for every expected failure. The API layer maps subclasses to status codes."""

    code = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    code = "not_found"


class ConflictError(DomainError):
    code = "conflict"


class AuthenticationError(DomainError):
    code = "authentication_failed"


class BookNotFound(NotFoundError):
    code = "book_not_found"

    def __init__(self, book_id: UUID) -> None:
        super().__init__(f"Book {book_id} does not exist.")


class LoanNotFound(NotFoundError):
    code = "loan_not_found"

    def __init__(self, loan_id: UUID) -> None:
        super().__init__(f"Loan {loan_id} does not exist.")


class NoCopiesAvailable(ConflictError):
    code = "no_copies_available"

    def __init__(self, book_id: UUID) -> None:
        super().__init__(f"Book {book_id} has no copies available.")


class AlreadyBorrowed(ConflictError):
    code = "already_borrowed"

    def __init__(self, book_id: UUID) -> None:
        super().__init__(f"Book {book_id} is already on loan to this user.")


class BorrowLimitReached(ConflictError):
    code = "borrow_limit_reached"

    def __init__(self, limit: int) -> None:
        super().__init__(f"Borrow limit of {limit} active loans reached.")


class LoanAlreadyReturned(ConflictError):
    code = "loan_already_returned"

    def __init__(self, loan_id: UUID) -> None:
        super().__init__(f"Loan {loan_id} was already returned.")


class EmailAlreadyRegistered(ConflictError):
    code = "email_already_registered"

    def __init__(self, email: str) -> None:
        super().__init__(f"{email} is already registered.")


class InvalidCredentials(AuthenticationError):
    code = "invalid_credentials"

    def __init__(self) -> None:
        super().__init__("Incorrect email or password.")


class InvalidToken(AuthenticationError):
    code = "invalid_token"

    def __init__(self) -> None:
        super().__init__("Access token is missing, expired or malformed.")
