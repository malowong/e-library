"""Starting catalogue so a fresh database is browsable

Revision ID: 0002
Revises: 0001
"""
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

BOOKS = [
    ("The Pragmatic Programmer", "Andrew Hunt, David Thomas", "9780201616224", 1999, 3),
    ("Domain-Driven Design", "Eric Evans", "9780321125217", 2003, 2),
    ("Designing Data-Intensive Applications", "Martin Kleppmann", "9781449373320", 2017, 4),
    ("Refactoring", "Martin Fowler", "9780134757599", 2018, 2),
    ("The Mythical Man-Month", "Frederick P. Brooks Jr.", "9780201835953", 1975, 1),
    ("Journal of Systems Engineering, Vol. 12", "Various", "9772049112004", 2024, 1),
]


def upgrade() -> None:
    books = sa.table(
        "books",
        sa.column("id", sa.Uuid),
        sa.column("title", sa.String),
        sa.column("author", sa.String),
        sa.column("isbn", sa.String),
        sa.column("published_year", sa.Integer),
        sa.column("total_copies", sa.Integer),
    )
    op.bulk_insert(
        books,
        [
            {
                "id": uuid5(NAMESPACE_URL, f"urn:isbn:{isbn}"),
                "title": title,
                "author": author,
                "isbn": isbn,
                "published_year": year,
                "total_copies": copies,
            }
            for title, author, isbn, year, copies in BOOKS
        ],
    )


def downgrade() -> None:
    books = sa.table("books", sa.column("isbn", sa.String))
    op.execute(books.delete().where(books.c.isbn.in_([isbn for _, _, isbn, _, _ in BOOKS])))
