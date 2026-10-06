import pytest

from src.api.open_library import OpenLibraryClient, OpenLibraryError


def test_empty_query():
    client = OpenLibraryClient()

    with pytest.raises(ValueError):
        client.search_books("")


def test_invalid_limit():
    client = OpenLibraryClient()

    with pytest.raises(ValueError):
        client.search_books("The Hobbit", limit=0)


def test_document_to_book():
    document = {
        "title": "The Hobbit",
        "author_name": ["J.R.R. Tolkien"],
        "first_publish_year": 1937,
        "subject": ["Fantasy", "Adventure"],
        "number_of_pages_median": 310,
        "isbn": ["9780547928227"],
        "cover_i": 123456,
    }

    book = OpenLibraryClient._document_to_book(document)

    assert book.title == "The Hobbit"
    assert book.authors == ["J.R.R. Tolkien"]
    assert book.publication_year == 1937
    assert book.subjects == ["Fantasy", "Adventure"]
    assert book.page_count == 310
    assert book.isbn == "9780547928227"
    assert book.cover_url == (
        "https://covers.openlibrary.org/b/id/123456-L.jpg"
    )


def test_missing_fields():
    document = {
        "title": "Unknown Book",
    }

    book = OpenLibraryClient._document_to_book(document)

    assert book.title == "Unknown Book"
    assert book.authors == []
    assert book.isbn is None
    assert book.publication_year is None
    assert book.subjects == []
    assert book.page_count is None
    assert book.cover_url is None