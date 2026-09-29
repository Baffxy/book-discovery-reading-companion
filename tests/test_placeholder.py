from src.models.book import Book


def test_book_creation():
    book = Book(
        title="The Hobbit",
        authors=["J.R.R. Tolkien"],
        publication_year=1937,
    )

    assert book.title == "The Hobbit"
    assert book.authors == ["J.R.R. Tolkien"]
    assert book.publication_year == 1937


def test_display_authors():
    book = Book(
        title="The Hobbit",
        authors=["J.R.R. Tolkien"],
    )

    assert book.display_authors() == "J.R.R. Tolkien"


def test_missing_author():
    book = Book(title="Unknown Book")

    assert book.display_authors() == "Unknown author"