from src.models.book import Book
from src.recommendations.similar_books import SimilarBooksRecommender


def create_books():
    """Create sample books for testing."""

    target = Book(
        title="The Hobbit",
        authors=["J.R.R. Tolkien"],
        isbn="9780261102217",
        publication_year=1937,
        subjects=["Fantasy", "Adventure"],
    )

    same_author = Book(
        title="The Fellowship of the Ring",
        authors=["J.R.R. Tolkien"],
        isbn="9780261103573",
        publication_year=1954,
        subjects=["Fantasy", "Adventure"],
    )

    shared_subjects = Book(
        title="A Game of Thrones",
        authors=["George R.R. Martin"],
        isbn="9780553103540",
        publication_year=1996,
        subjects=["Fantasy", "Adventure"],
    )

    unrelated = Book(
        title="Pride and Prejudice",
        authors=["Jane Austen"],
        isbn="9780141439518",
        publication_year=1813,
        subjects=["Romance", "Fiction"],
    )

    return (
        target,
        same_author,
        shared_subjects,
        unrelated,
    )


def test_find_similar_books():
    """Test that similar books are returned."""

    target, same_author, shared_subjects, unrelated = create_books()

    recommender = SimilarBooksRecommender(
        [
            target,
            same_author,
            shared_subjects,
            unrelated,
        ]
    )

    results = recommender.find_similar(target)

    assert same_author in results
    assert shared_subjects in results
    assert unrelated not in results


def test_shared_author_has_higher_similarity():
    """Test that a shared author gives a stronger score."""

    target, same_author, shared_subjects, _ = create_books()

    author_score = SimilarBooksRecommender._similarity_score(
        target,
        same_author,
    )

    subject_score = SimilarBooksRecommender._similarity_score(
        target,
        shared_subjects,
    )

    assert author_score > subject_score


def test_original_book_is_not_recommended():
    """Test that the original book is excluded."""

    target, same_author, _, _ = create_books()

    recommender = SimilarBooksRecommender(
        [target, same_author]
    )

    results = recommender.find_similar(target)

    assert target not in results


def test_limit_is_respected():
    """Test that the requested result limit is respected."""

    target, same_author, shared_subjects, _ = create_books()

    another = Book(
        title="Another Fantasy",
        authors=["Another Author"],
        subjects=["Fantasy"],
    )

    recommender = SimilarBooksRecommender(
        [
            target,
            same_author,
            shared_subjects,
            another,
        ]
    )

    results = recommender.find_similar(
        target,
        limit=2,
    )

    assert len(results) == 2


def test_empty_subjects_and_authors_are_handled():
    """Test books with missing metadata safely."""

    target = Book(
        title="Book One",
        authors=[],
        subjects=[],
    )

    candidate = Book(
        title="Book Two",
        authors=[],
        subjects=[],
    )

    recommender = SimilarBooksRecommender(
        [target, candidate]
    )

    results = recommender.find_similar(target)

    assert results == []


def test_invalid_book_raises_error():
    """Test that an invalid book argument raises TypeError."""

    recommender = SimilarBooksRecommender([])

    try:
        recommender.find_similar("not a book")
        assert False
    except TypeError:
        assert True 