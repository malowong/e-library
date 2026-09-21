from uuid import uuid4


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_browse_and_read_a_book(client, book_repository):
    book = book_repository.seed(title="Domain-Driven Design", total_copies=2)

    listing = client.get("/books")
    assert listing.status_code == 200
    assert [b["title"] for b in listing.json()] == ["Domain-Driven Design"]

    detail = client.get(f"/books/{book.id}")
    assert detail.status_code == 200
    assert detail.json()["available_copies"] == 2


def test_unknown_book_returns_a_structured_404(client):
    response = client.get(f"/books/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "book_not_found"


def test_loans_require_authentication(client):
    assert client.get("/loans").status_code == 401
    assert client.get("/loans", headers={"Authorization": "Bearer nonsense"}).status_code == 401


def test_borrow_then_view_then_return(client, book_repository, auth_headers):
    book = book_repository.seed()

    borrowed = client.post("/loans", json={"book_id": str(book.id)}, headers=auth_headers)
    assert borrowed.status_code == 201
    loan_id = borrowed.json()["id"]

    active = client.get("/loans", headers=auth_headers).json()
    assert [loan["id"] for loan in active] == [loan_id]
    assert client.get(f"/books/{book.id}").json()["available_copies"] == 0

    returned = client.post(f"/loans/{loan_id}/return", headers=auth_headers)
    assert returned.status_code == 200
    assert returned.json()["returned_at"] is not None

    assert client.get("/loans", headers=auth_headers).json() == []
    assert len(client.get("/loans?include_returned=true", headers=auth_headers).json()) == 1
    assert client.get(f"/books/{book.id}").json()["available_copies"] == 1


def test_borrowing_an_unavailable_book_returns_409(client, book_repository, auth_headers):
    book = book_repository.seed(total_copies=1)
    client.post("/loans", json={"book_id": str(book.id)}, headers=auth_headers)

    response = client.post("/loans", json={"book_id": str(book.id)}, headers=auth_headers)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "already_borrowed"


def test_registering_a_duplicate_email_returns_409(client):
    credentials = {"email": "reader@example.com", "password": "correct-horse"}
    client.post("/auth/register", json=credentials)

    response = client.post("/auth/register", json=credentials)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "email_already_registered"


def test_login_with_a_bad_password_returns_401(client):
    client.post("/auth/register", json={"email": "reader@example.com", "password": "correct-horse"})

    response = client.post(
        "/auth/login", json={"email": "reader@example.com", "password": "nope"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_short_passwords_are_rejected_by_validation(client):
    response = client.post("/auth/register", json={"email": "a@b.com", "password": "short"})

    assert response.status_code == 422
