from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from elibrary.domain.errors import (
    AuthenticationError,
    ConflictError,
    DomainError,
    NotFoundError,
)

_STATUS_BY_ERROR: list[tuple[type[DomainError], int]] = [
    (NotFoundError, status.HTTP_404_NOT_FOUND),
    (ConflictError, status.HTTP_409_CONFLICT),
    (AuthenticationError, status.HTTP_401_UNAUTHORIZED),
]


def _status_for(error: DomainError) -> int:
    for error_type, code in _STATUS_BY_ERROR:
        if isinstance(error, error_type):
            return code
    return status.HTTP_400_BAD_REQUEST


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, error: DomainError) -> JSONResponse:
        response = JSONResponse(
            status_code=_status_for(error),
            content={"error": {"code": error.code, "message": error.message}},
        )
        if isinstance(error, AuthenticationError):
            response.headers["WWW-Authenticate"] = "Bearer"
        return response
