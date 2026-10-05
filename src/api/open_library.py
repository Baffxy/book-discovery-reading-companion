import requests

from src.models.book import Book


class OpenLibraryError(Exception):
    """Raised when an Open Library request or response fails."""


class OpenLibraryClient:
    """Client for searching books through the Open Library Search API."""

    BASE_URL = "https://openlibrary.org/search.json"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def search_books(self, query: str, limit: int = 10) -> list[Book]:
        """
        Search Open Library and return matching books.

        Args:
            query: Book title, author, ISBN, or general search text.
            limit: Maximum number of results to return.

        Returns:
            A list of Book objects.

        Raises:
            ValueError: If the query is empty or limit is invalid.
            OpenLibraryError: If the API request or response fails.
        """
        query = query.strip()

        if not query:
            raise ValueError("Search query cannot be empty.")

        if limit < 1:
            raise ValueError("Limit must be at least 1.")

        params = {
            "q": query,
            "limit": limit,
            "fields": (
                "title,author_name,first_publish_year,"
                "subject,number_of_pages_median,isbn,cover_i"
            ),
        }

        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

        except requests.RequestException as exc:
            raise OpenLibraryError(
                "Failed to connect to Open Library."
            ) from exc

        except ValueError as exc:
            raise OpenLibraryError(
                "Open Library returned invalid JSON."
            ) from exc

        docs = data.get("docs", [])

        if not isinstance(docs, list):
            raise OpenLibraryError(
                "Unexpected response format from Open Library."
            )

        return [self._document_to_book(doc) for doc in docs]

    @staticmethod
    def _document_to_book(document: dict) -> Book:
        """Convert an Open Library search document into a Book object."""

        title = document.get("title") or "Unknown title"

        authors = document.get("author_name") or []
        if not isinstance(authors, list):
            authors = [str(authors)]

        subjects = document.get("subject") or []
        if not isinstance(subjects, list):
            subjects = [str(subjects)]

        isbn_values = document.get("isbn") or []
        isbn = isbn_values[0] if isbn_values else None

        publication_year = document.get("first_publish_year")

        page_count = document.get("number_of_pages_median")

        cover_id = document.get("cover_i")
        cover_url = (
            f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
            if cover_id
            else None
        )

        return Book(
            title=title,
            authors=authors,
            isbn=isbn,
            publication_year=publication_year,
            subjects=subjects,
            page_count=page_count,
            cover_url=cover_url,
        )