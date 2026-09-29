from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Book:
    """Represents a book in the application."""

    title: str
    authors: list[str] = field(default_factory=list)
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    subjects: list[str] = field(default_factory=list)
    page_count: Optional[int] = None
    cover_url: Optional[str] = None

    def display_authors(self) -> str:
        """Return authors as a readable string."""
        return ", ".join(self.authors) if self.authors else "Unknown author"