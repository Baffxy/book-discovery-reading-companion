from pathlib import Path

import pytest

from src.models.book import Book
from src.reading.reading_list import ReadingListManager
from src.utils.storage import (
    StorageError,
    load_reading_list,
    save_reading_list,
)


def create_reading_list():
    """Create a sample reading list."""

    manager = ReadingListManager()

    book = Book(
        title="The Hobbit",
        authors=["J.R.R. Tolkien"],
        isbn="9780261102217",
        publication_year=1937,
        subjects=["Fantasy", "Adventure"],
        page_count=310,
        cover_url="https://example.com/hobbit.jpg",
    )

    manager.add_book(
        book,
        status="Reading",
    )

    return manager


def test_save_reading_list(tmp_path):
    """Test saving a reading list to JSON."""

    manager = create_reading_list()
    filepath = tmp_path / "reading_list.json"

    save_reading_list(manager, filepath)

    assert filepath.exists()
    assert filepath.read_text(encoding="utf-8")


def test_load_reading_list(tmp_path):
    """Test loading a saved reading list."""

    manager = create_reading_list()
    filepath = tmp_path / "reading_list.json"

    save_reading_list(manager, filepath)

    loaded = load_reading_list(filepath)

    assert len(loaded.get_books()) == 1

    book = loaded.get_books()[0]

    assert book.title == "The Hobbit"
    assert book.authors == ["J.R.R. Tolkien"]
    assert book.isbn == "9780261102217"
    assert book.publication_year == 1937
    assert book.subjects == ["Fantasy", "Adventure"]
    assert book.page_count == 310
    assert book.cover_url == "https://example.com/hobbit.jpg"

    assert loaded.get_status(book.isbn) == "Reading"


def test_missing_file_returns_empty_reading_list(tmp_path):
    """Test loading a file that does not exist."""

    filepath = tmp_path / "missing.json"

    loaded = load_reading_list(filepath)

    assert isinstance(loaded, ReadingListManager)
    assert loaded.get_books() == []


def test_invalid_json_raises_error(tmp_path):
    """Test invalid JSON handling."""

    filepath = tmp_path / "invalid.json"

    filepath.write_text(
        "this is not valid json",
        encoding="utf-8",
    )

    with pytest.raises(StorageError):
        load_reading_list(filepath)


def test_invalid_storage_structure_raises_error(tmp_path):
    """Test invalid JSON structure handling."""

    filepath = tmp_path / "invalid_structure.json"

    filepath.write_text(
        '{"book": "The Hobbit"}',
        encoding="utf-8",
    )

    with pytest.raises(StorageError):
        load_reading_list(filepath)