"""
Group 40 - Book Discovery & Reading Companion
Member: Princess Jonathan
Role: Open Library API - API client for searching and retrieving book information

Handles:
- Empty search input
- Invalid ISBN
- Book not found
- Failed API request
- Missing publication year
- Missing cover image
- Missing page count
- Invalid/incomplete API responses

Design note:
    Missing values are returned as None (or an empty list), NOT as display text.
    This keeps the data clean for other modules (Reading List, Storage, Validation).
    Use format_for_display() when you need friendly "not available" messages for the UI.
"""
import re
import requests


# --- Custom Exceptions (Error Handling Strategy) ---
class EmptySearchError(Exception):
    """User submitted an empty search."""
    pass


class InvalidISBNError(Exception):
    """ISBN format is invalid."""
    pass


class BookNotFoundError(Exception):
    """No book found."""
    pass


class APIRequestError(Exception):
    """Open Library API is unavailable or returned a bad response."""
    pass


class OpenLibraryClient:
    """Communicates with the Open Library API and retrieves book information."""

    # Only ask the API for the fields we actually use (smaller, faster responses)
    SEARCH_FIELDS = (
        "key,title,author_name,first_publish_year,isbn,"
        "number_of_pages_median,cover_i,subject"
    )

    def __init__(self):
        self.base_url = "https://openlibrary.org"
        self.search_url = f"{self.base_url}/search.json"
        self.cover_base = "https://covers.openlibrary.org/b/id"
        self.timeout = 10
        # Open Library asks apps to identify themselves
        self.headers = {
            "User-Agent": "BookDiscoveryReadingCompanion/1.0 (student project)"
        }

    # ------------------------------------------------------------------
    # REGEX VALIDATION / CLEANING HELPERS
    # ------------------------------------------------------------------
    def validate_isbn(self, isbn_input: str) -> str:
        """Validate ISBN-10 or ISBN-13 with regex. Returns the cleaned ISBN."""
        if not isbn_input or not str(isbn_input).strip():
            raise InvalidISBNError("ISBN is empty")

        # Remove hyphens and spaces
        clean_isbn = re.sub(r"[-\s]", "", str(isbn_input).strip())

        isbn10_pattern = r"\d{9}[\dXx]"   # 9 digits + a digit or X
        isbn13_pattern = r"\d{13}"        # 13 digits

        if re.fullmatch(isbn10_pattern, clean_isbn) or re.fullmatch(isbn13_pattern, clean_isbn):
            return clean_isbn.upper()

        raise InvalidISBNError(
            f"Invalid ISBN '{isbn_input}'. ISBN-10 has 10 characters "
            f"(e.g. 0439023521) and ISBN-13 has 13 digits (e.g. 9780439023528)."
        )

    def extract_publication_year(self, date_value):
        """Extract a 4-digit year (as int) from values like 1999, 'June 1999', '1999-05-01'.
        Returns None if no year can be found."""
        if not date_value:
            return None

        match = re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", str(date_value))
        if match:
            return int(match.group(1))
        return None

    def clean_text(self, text):
        """Remove extra spaces/newlines from titles and author names.
        Returns None if the text is missing."""
        if not text:
            return None
        cleaned = re.sub(r"\s+", " ", str(text)).strip()
        return cleaned or None

    def _looks_like_isbn(self, query: str) -> bool:
        """True if the query is made only of digits/X (with optional hyphens/spaces)
        and is long enough that the user probably meant an ISBN."""
        compact = re.sub(r"[-\s]", "", query)
        return bool(re.fullmatch(r"[\dXx]+", compact)) and len(compact) >= 8

    # ------------------------------------------------------------------
    # 1. BOOK SEARCH
    # ------------------------------------------------------------------
    def search_books(self, query, limit: int = 10):
        """
        Search by title, author, or ISBN.
        Calls: https://openlibrary.org/search.json?q=...
        Returns a list of normalized book dictionaries.
        """
        # Error 1: empty search input
        if query is None or str(query).strip() == "":
            raise EmptySearchError(
                "Search query cannot be empty. Please enter a title, author or ISBN."
            )

        query = str(query).strip()

        # Error 2: invalid ISBN (validated BEFORE any network call)
        if self._looks_like_isbn(query):
            isbn = self.validate_isbn(query)  # raises InvalidISBNError if wrong
            params = {"q": f"isbn:{isbn}", "limit": limit, "fields": self.SEARCH_FIELDS}
        else:
            params = {"q": query, "limit": limit, "fields": self.SEARCH_FIELDS}

        # Error 4: failed API request
        try:
            response = requests.get(
                self.search_url,
                params=params,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()  # raises HTTPError for 4xx/5xx
            data = response.json()
        except requests.exceptions.Timeout:
            raise APIRequestError(
                "Open Library API timed out. Please check your internet and try again."
            )
        except requests.exceptions.ConnectionError:
            raise APIRequestError(
                "Failed to connect to Open Library API. Please check your internet connection."
            )
        except requests.exceptions.HTTPError as e:
            raise APIRequestError(f"Open Library API request failed: {e}")
        except requests.exceptions.RequestException as e:
            raise APIRequestError(f"Open Library API request failed: {e}")
        except ValueError:
            raise APIRequestError("Received invalid JSON from Open Library API.")

        # Error 8: invalid or incomplete API response
        if not isinstance(data, dict) or not isinstance(data.get("docs"), list):
            raise APIRequestError("Received an invalid response format from Open Library API.")

        # Error 3: book not found
        if not data["docs"]:
            raise BookNotFoundError(f"No books found for '{query}'.")

        return [self._normalize_book(doc) for doc in data["docs"][:limit]]

    # ------------------------------------------------------------------
    # 2. NORMALIZE A BOOK (handles missing data: Errors 5, 6, 7)
    # ------------------------------------------------------------------
    def _normalize_book(self, doc: dict) -> dict:
        """Turn a raw API record into a clean dictionary.
        Missing values become None (or an empty list), never a crash."""
        title = self.clean_text(doc.get("title"))

        authors = [
            a for a in (self.clean_text(x) for x in (doc.get("author_name") or [])) if a
        ]

        # Error 5: missing publication year -> None
        year = self.extract_publication_year(doc.get("first_publish_year"))

        # Error 7: missing page count -> None
        pages = doc.get("number_of_pages_median")
        page_count = pages if isinstance(pages, int) and pages > 0 else None

        # Error 6: missing cover image -> None (UI shows a placeholder)
        cover_id = doc.get("cover_i")
        cover_url = f"{self.cover_base}/{cover_id}-M.jpg" if cover_id else None

        isbn_list = doc.get("isbn") or []
        isbn = isbn_list[0] if isbn_list else None

        subjects = (doc.get("subject") or [])[:5]

        return {
            "key": doc.get("key", ""),
            "title": title,
            "authors": authors,
            "publication_year": year,
            "isbn": isbn,
            "page_count": page_count,
            "cover_url": cover_url,
            "subjects": subjects,
        }

    # ------------------------------------------------------------------
    # 3. BOOK DETAILS
    # ------------------------------------------------------------------
    def get_book_details(self, work_key: str) -> dict:
        """Get details for one book using its work key, e.g. '/works/OL45804W'.
        Returns a cleaned dictionary (same style as search results)."""
        if not work_key or not str(work_key).strip():
            raise EmptySearchError("Work key is missing.")

        work_key = str(work_key).strip()
        if not work_key.startswith("/"):
            work_key = "/" + work_key

        try:
            response = requests.get(
                f"{self.base_url}{work_key}.json",
                headers=self.headers,
                timeout=self.timeout,
            )
            if response.status_code == 404:
                raise BookNotFoundError(f"Book details not found for {work_key}.")
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            raise APIRequestError(f"Failed to retrieve book details: {e}")
        except ValueError:
            raise APIRequestError("Received invalid JSON from Open Library API.")

        if not isinstance(data, dict):
            raise APIRequestError("Received an invalid response format from Open Library API.")

        # 'description' can be a plain string or {"type": ..., "value": ...}
        description = data.get("description")
        if isinstance(description, dict):
            description = description.get("value")

        covers = data.get("covers") or []
        cover_url = f"{self.cover_base}/{covers[0]}-M.jpg" if covers else None

        return {
            "key": data.get("key", work_key),
            "title": self.clean_text(data.get("title")),
            "description": self.clean_text(description),
            "publication_year": self.extract_publication_year(data.get("first_publish_date")),
            "cover_url": cover_url,
            "subjects": (data.get("subjects") or [])[:10],
        }

    # ------------------------------------------------------------------
    # 4. DISPLAY HELPER (friendly messages for the UI)
    # ------------------------------------------------------------------
    def format_for_display(self, book: dict) -> dict:
        """Return a copy of a book dict with friendly text for missing values.
        Use this only when showing data to the user, not when saving or sorting."""
        return {
            "title": book.get("title") or "Title not available",
            "authors": ", ".join(book.get("authors") or []) or "Author not available",
            "publication_year": book.get("publication_year") or "Publication year not available",
            "isbn": book.get("isbn") or "ISBN not available",
            "page_count": (
                f"{book['page_count']} pages" if book.get("page_count") else "Page count not available"
            ),
            "cover_url": book.get("cover_url"),  # None -> UI shows placeholder
            "subjects": book.get("subjects") or ["No subjects listed"],
        }


# --- Quick self-test (run this file directly) ---
if __name__ == "__main__":
    client = OpenLibraryClient()

    tests = [
        "",                      # Error 1: empty search
        "12345678",              # Error 2: invalid ISBN
        "asdfghjklqwerty12345",  # Error 3: book not found
        "The Great Gatsby",      # valid title search
        "9780439023528",         # valid ISBN-13
    ]

    for q in tests:
        print(f"\n--- Searching for: '{q}' ---")
        try:
            books = client.search_books(q, limit=2)
            for b in books:
                shown = client.format_for_display(b)
                print(
                    f"Found: {shown['title']} | {shown['authors']} | "
                    f"{shown['publication_year']} | {shown['page_count']} | "
                    f"Cover: {'Yes' if shown['cover_url'] else 'No cover - placeholder will be used'}"
                )
        except (EmptySearchError, InvalidISBNError, BookNotFoundError, APIRequestError) as e:
            print(f"Handled Error: {type(e).__name__}: {e}")           