from fastapi import FastAPI

from elibrary.api.errors import register_error_handlers
from elibrary.api.routers import auth, books, loans


def create_app() -> FastAPI:
    app = FastAPI(title="E-Library Service", version="0.1.0")
    register_error_handlers(app)
    app.include_router(auth.router)
    app.include_router(books.router)
    app.include_router(loans.router)

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
