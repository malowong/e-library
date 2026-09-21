from uuid import UUID

from fastapi import APIRouter

from elibrary.api.deps import CatalogueServiceDep
from elibrary.api.schemas import BookResponse

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=list[BookResponse])
async def browse_books(catalogue: CatalogueServiceDep) -> list[BookResponse]:
    return [BookResponse.of(book) for book in await catalogue.browse()]


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: UUID, catalogue: CatalogueServiceDep) -> BookResponse:
    return BookResponse.of(await catalogue.get_book(book_id))
