import os
from unittest.mock import MagicMock, patch

import psycopg
import pytest

from src.models.book import Book
from src.reading.reading_list import ReadingListManager
from src.utils.database import (
    DatabaseError,
    _book_key,
    get_database_url,
    initialize_database,
    load_reading_list_from_database,
    load_saved_reading_guides,
    save_reading_guide_to_database,
    save_reading_list_to_database,
)


def test_get_database_url_returns_configured_url(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://example:password@localhost/example",
    )

    assert get_database_url().startswith("postgresql://")


def test_get_database_url_raises_when_missing(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(DatabaseError, match="DATABASE_URL"):
        get_database_url()


def test_book_key_uses_isbn():
    book = Book(
        title="The Hobbit",
        authors=["J.R.R. Tolkien"],
        isbn="978-0261102217",
    )

    assert _book_key(book) == "isbn:9780261102217"


def test_book_key_supports_books_without_isbn():
    book = Book(
        title="The Hobbit",
        authors=["J.R.R. Tolkien"],
    )

    assert _book_key(book) == (
        "title:the hobbit|authors:j.r.r. tolkien"
    )


def test_save_reading_list_rejects_invalid_input():
    with pytest.raises(DatabaseError):
        save_reading_list_to_database([])


def test_save_reading_guide_rejects_invalid_book():
    with pytest.raises(DatabaseError):
        save_reading_guide_to_database(
            "not a book",
            {},
        )


def test_save_reading_guide_rejects_missing_fields():
    book = Book(title="Example")

    with pytest.raises(DatabaseError, match="missing required fields"):
        save_reading_guide_to_database(book, {})


def test_load_saved_reading_guides_rejects_invalid_limit():
    with pytest.raises(DatabaseError, match="positive integer"):
        load_saved_reading_guides(limit=0)


def test_initialize_database_executes_table_creation():
    connection = MagicMock()
    cursor = MagicMock()

    connection.cursor.return_value.__enter__.return_value = cursor

    with patch(
        "src.utils.database.get_connection"
    ) as mock_connection:
        mock_connection.return_value.__enter__.return_value = connection

        initialize_database()

    assert cursor.execute.call_count == 2


def test_database_connection_error_is_wrapped(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://example:password@localhost/example",
    )

    with patch(
        "src.utils.database.psycopg.connect",
        side_effect=psycopg.OperationalError("connection failed"),
    ):
        from src.utils.database import get_connection

        with pytest.raises(DatabaseError, match="Could not connect"):
            get_connection()