import pytest

from src.models.book import Book
from src.reading.reading_list import ReadingListManager


@pytest.fixture
def book():
    return Book(
        title="The Hobbit",
        authors=["J.R.R. Tolkien"],
        isbn="9780547928227",
        publication_year=1937,
        subjects=["Fantasy", "Adventure"],
        page_count=310,
    )


@pytest.fixture
def manager():
    return ReadingListManager()


def test_add_book(manager, book):
    manager.add_book(book)

    books = manager.get_books()

    assert len(books) == 1
    assert books[0].title == "The Hobbit"
    assert manager.get_status(book.isbn) == "Want to Read"


def test_add_book_with_status(manager, book):
    manager.add_book(book, "Reading")

    assert manager.get_status(book.isbn) == "Reading"


def test_update_status(manager, book):
    manager.add_book(book)

    manager.update_status(book.isbn, "Finished")

    assert manager.get_status(book.isbn) == "Finished"


def test_remove_book(manager, book):
    manager.add_book(book)

    manager.remove_book(book.isbn)

    assert manager.get_books() == []


def test_find_book(manager, book):
    manager.add_book(book)

    found = manager.find_book(book.isbn)

    assert found is book


def test_duplicate_book(manager, book):
    manager.add_book(book)

    with pytest.raises(ValueError):
        manager.add_book(book)


def test_invalid_status(manager, book):
    with pytest.raises(ValueError):
        manager.add_book(book, "Currently Reading")


def test_missing_book(manager):
    with pytest.raises(KeyError):
        manager.update_status(
            "9780547928227",
            "Reading",
        )


def test_clear(manager, book):
    manager.add_book(book)

    manager.clear()

    assert manager.get_books() == []