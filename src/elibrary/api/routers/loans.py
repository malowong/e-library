from uuid import UUID

from fastapi import APIRouter, status

from elibrary.api.deps import CurrentUserId, LendingServiceDep
from elibrary.api.schemas import BorrowRequest, LoanResponse

router = APIRouter(prefix="/loans", tags=["loans"])


@router.get("", response_model=list[LoanResponse])
async def list_loans(
    user_id: CurrentUserId, lending: LendingServiceDep, include_returned: bool = False
) -> list[LoanResponse]:
    loans = await lending.list_loans(user_id, active_only=not include_returned)
    return [LoanResponse.of(loan) for loan in loans]


@router.post("", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
async def borrow_book(
    payload: BorrowRequest, user_id: CurrentUserId, lending: LendingServiceDep
) -> LoanResponse:
    return LoanResponse.of(await lending.borrow(user_id, payload.book_id))


@router.post("/{loan_id}/return", response_model=LoanResponse)
async def return_book(
    loan_id: UUID, user_id: CurrentUserId, lending: LendingServiceDep
) -> LoanResponse:
    return LoanResponse.of(await lending.return_book(user_id, loan_id))
