import json
from pathlib import Path

from src.models.book import Book
from src.reading.reading_list import ReadingListManager


class StorageError(Exception):
    """Raised when reading-list storage cannot be processed."""


def save_reading_list(
    reading_list: ReadingListManager,
    filepath: str | Path,
) -> None:
    """Save a reading list to a JSON file."""

    if not isinstance(reading_list, ReadingListManager):
        raise StorageError(
            "reading_list must be a ReadingListManager."
        )

    path = Path(filepath)

    data = []

    for book in reading_list.get_books():
        data.append(
            {
                "title": book.title,
                "authors": book.authors,
                "isbn": book.isbn,
                "publication_year": book.publication_year,
                "subjects": book.subjects,
                "page_count": book.page_count,
                "cover_url": book.cover_url,
                "status": reading_list.get_status(book.isbn),
            }
        )

    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    except OSError as exc:
        raise StorageError(
            f"Could not save reading list: {exc}"
        ) from exc


def load_reading_list(
    filepath: str | Path,
) -> ReadingListManager:
    """Load a reading list from a JSON file."""

    path = Path(filepath)

    if not path.exists():
        return ReadingListManager()

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError(
            f"Could not load reading list: {exc}"
        ) from exc

    if not isinstance(data, list):
        raise StorageError(
            "Stored reading list must be a JSON list."
        )

    reading_list = ReadingListManager()

    try:
        for item in data:
            if not isinstance(item, dict):
                raise StorageError(
                    "Each stored book must be a JSON object."
                )

            book = Book(
                title=item["title"],
                authors=item.get("authors", []),
                isbn=item.get("isbn"),
                publication_year=item.get(
                    "publication_year"
                ),
                subjects=item.get("subjects", []),
                page_count=item.get("page_count"),
                cover_url=item.get("cover_url"),
            )

            status = item.get("status", "Want to Read")

            reading_list.add_book(
                book,
                status=status,
            )

    except (KeyError, TypeError, ValueError) as exc:
        raise StorageError(
            f"Invalid stored book data: {exc}"
        ) from exc

    return reading_list