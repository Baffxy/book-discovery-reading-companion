from src.models.book import Book


class SimilarBooksRecommender:
    """Recommend books based on shared authors and subjects."""

    def __init__(self, books: list[Book] | None = None):
        """Initialize the recommender with a collection of books."""
        self.books = books or []

    @staticmethod
    def _similarity_score(book: Book, candidate: Book) -> int:
        """Calculate a similarity score between two books."""

        score = 0

        book_authors = {
            author.strip().lower()
            for author in book.authors
        }

        candidate_authors = {
            author.strip().lower()
            for author in candidate.authors
        }

        book_subjects = {
            subject.strip().lower()
            for subject in book.subjects
        }

        candidate_subjects = {
            subject.strip().lower()
            for subject in candidate.subjects
        }

        # A shared author gives a stronger similarity signal.
        if book_authors & candidate_authors:
            score += 3

        # Each shared subject contributes one point.
        score += len(book_subjects & candidate_subjects)

        return score

    @staticmethod
    def _book_key(book: Book) -> str:
        """Create a normalized identifier for a book."""

        if book.isbn:
            return book.isbn.strip().replace("-", "")

        return book.title.strip().lower()

    def find_similar(
        self,
        book: Book,
        limit: int = 5,
    ) -> list[Book]:
        """Return the most similar books."""

        if not isinstance(book, Book):
            raise TypeError("book must be a Book object.")

        if limit <= 0:
            return []

        target_key = self._book_key(book)
        candidates = []

        for candidate in self.books:
            if not isinstance(candidate, Book):
                continue

            # Do not recommend the same book.
            if self._book_key(candidate) == target_key:
                continue

            score = self._similarity_score(book, candidate)

            if score > 0:
                candidates.append((score, candidate))

        # Highest similarity first.
        candidates.sort(
            key=lambda item: (
                -item[0],
                item[1].title.lower(),
            )
        )

        return [
            candidate
            for _, candidate in candidates[:limit]
        ]

    def recommend(
        self,
        book: Book,
        books: list[Book] | None = None,
        limit: int = 5,
    ) -> list[Book]:
        """Recommend similar books from an optional collection."""

        if books is not None:
            self.books = books

        return self.find_similar(book, limit=limit)