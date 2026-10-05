from src.models.book import Book


class ReadingListManager:
    """Manage a user's personal reading list."""

    VALID_STATUSES = {
        "Want to Read",
        "Reading",
        "Finished",
    }

    def __init__(self):
        self._books: dict[str, tuple[Book, str]] = {}

    def add_book(
        self,
        book: Book,
        status: str = "Want to Read",
    ) -> None:
        """Add a book to the reading list."""

        self._validate_status(status)

        if not isinstance(book, Book):
            raise TypeError("book must be a Book instance.")

        key = self._book_key(book)

        if key in self._books:
            raise ValueError("Book is already in the reading list.")

        self._books[key] = (book, status)

    def remove_book(self, isbn: str) -> None:
        """Remove a book using its ISBN."""

        if not isbn or not isbn.strip():
            raise ValueError("ISBN cannot be empty.")

        key = self._normalize_isbn(isbn)

        if key not in self._books:
            raise KeyError("Book not found in reading list.")

        del self._books[key]

    def update_status(self, isbn: str, status: str) -> None:
        """Update the reading status of a book."""

        self._validate_status(status)

        key = self._normalize_isbn(isbn)

        if key not in self._books:
            raise KeyError("Book not found in reading list.")

        book, _ = self._books[key]
        self._books[key] = (book, status)

    def get_books(self) -> list[Book]:
        """Return all books in the reading list."""

        return [book for book, _ in self._books.values()]

    def get_status(self, isbn: str) -> str:
        """Return the current reading status of a book."""

        key = self._normalize_isbn(isbn)

        if key not in self._books:
            raise KeyError("Book not found in reading list.")

        _, status = self._books[key]
        return status

    def find_book(self, isbn: str) -> Book | None:
        """Find a book by ISBN."""

        key = self._normalize_isbn(isbn)

        item = self._books.get(key)

        if item is None:
            return None

        return item[0]

    def clear(self) -> None:
        """Remove all books from the reading list."""

        self._books.clear()

    @classmethod
    def _validate_status(cls, status: str) -> None:
        if status not in cls.VALID_STATUSES:
            raise ValueError(
                f"Invalid status. Choose one of: "
                f"{', '.join(sorted(cls.VALID_STATUSES))}"
            )

    @staticmethod
    def _normalize_isbn(isbn: str) -> str:
        """Normalize an ISBN for consistent lookup."""

        if not isinstance(isbn, str):
            raise TypeError("ISBN must be a string.")

        normalized = isbn.replace("-", "").replace(" ", "").strip()

        if not normalized:
            raise ValueError("ISBN cannot be empty.")

        return normalized.upper()

    @classmethod
    def _book_key(cls, book: Book) -> str:
        """Create a unique key for a book."""

        if book.isbn:
            return cls._normalize_isbn(book.isbn)

        # Fallback for books without ISBN.
        title = book.title.strip().lower()
        authors = "|".join(
            author.strip().lower() for author in book.authors
        )

        return f"title:{title}|authors:{authors}"