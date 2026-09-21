# E-Library Service

A lending service for digital content: browse the catalogue, borrow a title, return it, and see
what you currently have out. FastAPI, async SQLAlchemy 2.0, PostgreSQL.

## Running

```bash
docker compose up --build        # API on http://localhost:8000, docs at /docs
```

The API container runs `alembic upgrade head` on start, so a fresh database is migrated and
seeded with a small catalogue.

Locally, without Docker:

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
cp .env.example .env             # point ELIBRARY_DATABASE_URL at a Postgres instance
.venv/bin/alembic upgrade head
.venv/bin/uvicorn elibrary.main:app --reload
```

## API

| Method | Path                  | Auth | Purpose                          |
| ------ | --------------------- | ---- | -------------------------------- |
| POST   | `/auth/register`      | –    | Create an account                |
| POST   | `/auth/login`         | –    | Exchange credentials for a JWT   |
| GET    | `/books`              | –    | Browse the catalogue             |
| GET    | `/books/{id}`         | –    | Book detail with availability    |
| POST   | `/loans`              | ✓    | Borrow a book                    |
| GET    | `/loans`              | ✓    | Currently borrowed books         |
| POST   | `/loans/{id}/return`  | ✓    | Return a book                    |

`GET /loans?include_returned=true` returns borrowing history rather than just active loans.
Authenticated routes take `Authorization: Bearer <token>`.

```bash
curl -X POST localhost:8000/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"reader@example.com","password":"correct-horse"}'

TOKEN=$(curl -s -X POST localhost:8000/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"reader@example.com","password":"correct-horse"}' | jq -r .access_token)

BOOK=$(curl -s localhost:8000/books | jq -r '.[0].id')
curl -X POST localhost:8000/loans -H "authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' -d "{\"book_id\":\"$BOOK\"}"
```

## Design

### Layers

```
  POST /loans
      │
      ▼
  api/routers/loans.py     read the JWT, validate the body
      │
      ▼
  domain/services.py       LendingService.borrow() — the lending rules
      │
      ▼
  domain/repositories.py   BookRepository, LoanRepository — interfaces
      │
      ▼  concrete class injected by api/deps.py
  db/repositories.py       SQLAlchemy  ──►  PostgreSQL
```

- The flow is the typical controller → service → repository chain.
- The service calls a repository *interface* defined in `domain/` rather than the SQLAlchemy
  implementation, which keeps the rules testable without a database.

### Domain model

- A `Book` is a title with a number of copies. A `Loan` is one user holding one copy between
  `borrowed_at` and `returned_at`.
- Availability is derived (copies minus active loans), not stored. No counter to drift.

### Lending rules

- To borrow: the book exists, a copy is free, the user does not already hold it, and the user is
  under the active-loan limit.
- Limit and loan period live in `LendingPolicy` and come from config, not hardcoded values.

### Concurrency

- `get_for_update` locks the book row for the rest of the transaction.
- A partial unique index on `(user_id, book_id) WHERE returned_at IS NULL` stops double-borrowing
  at the database.
- One transaction per request: commits on success, rolls back on any error.

### Errors

- The domain raises typed exceptions and knows nothing about HTTP.
- One handler maps the `NotFoundError` / `ConflictError` / `AuthenticationError` families to
  404 / 409 / 401 and returns `{"error": {"code": ..., "message": ...}}`.
- A new rule means a new exception, not a change to the web layer.
- Returning someone else's loan gives 404, not 403, so loan IDs cannot be probed.

### Auth

- Register and login issue a short-lived JWT. Passwords are bcrypt-hashed.
- Deliberately thin: no refresh tokens, no roles. It exists to give a loan a real owner.
- Every route reads identity through one `get_current_user_id` dependency, so swapping in a real
  identity provider is a change to that one function.

## Tests

```bash
.venv/bin/pytest
```

- 24 tests in total.
- Unit tests run the lending and auth rules against in-memory repositories.
- Integration tests run the real app through `TestClient` with real routing, real JWTs and real
  error mapping.

## AI use

Built with Claude Code. The AI assisted in writing and iterating on the implementation, based on
the requirements and stack I chose.

## License

[MIT](LICENSE)
