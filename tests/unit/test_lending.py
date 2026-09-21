from uuid import uuid4

import pytest

from elibrary.domain.errors import (
    AlreadyBorrowed,
    BookNotFound,
    BorrowLimitReached,
    LoanAlreadyReturned,
    LoanNotFound,
    NoCopiesAvailable,
)


async def test_borrow_creates_an_active_loan_with_a_due_date(lending, book_repository, user_id):
    book = book_repository.seed()

    loan = await lending.borrow(user_id, book.id)

    assert loan.is_active
    assert loan.due_at > loan.borrowed_at
    assert (await book_repository.get(book.id)).available_copies == 0


async def test_borrowing_an_unknown_book_is_rejected(lending, user_id):
    with pytest.raises(BookNotFound):
        await lending.borrow(user_id, uuid4())


async def test_last_copy_cannot_be_borrowed_twice(lending, book_repository, user_id):
    book = book_repository.seed(total_copies=1)
    await lending.borrow(uuid4(), book.id)

    with pytest.raises(NoCopiesAvailable):
        await lending.borrow(user_id, book.id)


async def test_spare_copies_allow_a_second_borrower(lending, book_repository, user_id):
    book = book_repository.seed(total_copies=2)
    await lending.borrow(uuid4(), book.id)

    assert (await lending.borrow(user_id, book.id)).is_active


async def test_same_user_cannot_hold_two_copies_of_one_book(lending, book_repository, user_id):
    book = book_repository.seed(total_copies=2)
    await lending.borrow(user_id, book.id)

    with pytest.raises(AlreadyBorrowed):
        await lending.borrow(user_id, book.id)


async def test_borrow_limit_is_enforced(lending, book_repository, user_id):
    for _ in range(2):
        await lending.borrow(user_id, book_repository.seed().id)

    with pytest.raises(BorrowLimitReached):
        await lending.borrow(user_id, book_repository.seed().id)


async def test_returning_frees_the_copy_and_the_limit(lending, book_repository, user_id):
    book = book_repository.seed()
    loan = await lending.borrow(user_id, book.id)

    returned = await lending.return_book(user_id, loan.id)

    assert not returned.is_active
    assert (await book_repository.get(book.id)).available_copies == 1
    assert await lending.list_loans(user_id) == []


async def test_a_loan_cannot_be_returned_twice(lending, book_repository, user_id):
    loan = await lending.borrow(user_id, book_repository.seed().id)
    await lending.return_book(user_id, loan.id)

    with pytest.raises(LoanAlreadyReturned):
        await lending.return_book(user_id, loan.id)


async def test_another_users_loan_is_not_returnable(lending, book_repository, user_id):
    loan = await lending.borrow(uuid4(), book_repository.seed().id)

    with pytest.raises(LoanNotFound):
        await lending.return_book(user_id, loan.id)


async def test_history_is_available_on_request(lending, book_repository, user_id):
    loan = await lending.borrow(user_id, book_repository.seed().id)
    await lending.return_book(user_id, loan.id)

    assert await lending.list_loans(user_id, active_only=True) == []
    assert len(await lending.list_loans(user_id, active_only=False)) == 1
