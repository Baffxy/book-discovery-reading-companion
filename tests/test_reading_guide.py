from types import SimpleNamespace

import pytest

from src.models.book import Book
from src.reading.reading_guide import (
    ReadingGuideError,
    ReadingGuideGenerator,
)


class FakeModels:
    """Fake Gemini models interface used for testing."""

    def __init__(self, response_text):
        self.response_text = response_text

    def generate_content(self, model, contents):
        return SimpleNamespace(text=self.response_text)


class FakeClient:
    """Fake Gemini client used to avoid real API calls."""

    def __init__(self, response_text):
        self.models = FakeModels(response_text)


def create_book():
    """Create a sample Book object for testing."""

    return Book(
        title="The Hobbit",
        authors=["J.R.R. Tolkien"],
        isbn="9780261102217",
        publication_year=1937,
        subjects=["Fantasy", "Adventure", "Fiction"],
        page_count=310,
        cover_url=None,
    )


def test_generate_reading_guide():
    """Test successful reading-guide generation."""

    response = """
    {
        "summary": "A fantasy adventure about Bilbo Baggins.",
        "reading_level": "Intermediate",
        "discussion_questions": [
            "What motivates Bilbo to join the adventure?",
            "How does Bilbo change throughout the story?",
            "What challenges does Bilbo face?",
            "How do the other characters influence Bilbo?",
            "What are the main themes of the story?"
        ]
    }
    """

    generator = ReadingGuideGenerator(
        client=FakeClient(response)
    )

    guide = generator.generate(create_book())

    assert "summary" in guide
    assert "reading_level" in guide
    assert "discussion_questions" in guide

    assert isinstance(guide["summary"], str)
    assert isinstance(guide["reading_level"], str)
    assert isinstance(guide["discussion_questions"], list)

    assert len(guide["discussion_questions"]) == 5


def test_missing_api_client_raises_error():
    """Test that a missing Gemini client/API key raises an error."""

    generator = ReadingGuideGenerator(
        api_key=None,
        client=None,
    )

    with pytest.raises(ReadingGuideError):
        generator.generate(create_book())


def test_invalid_json_raises_error():
    """Test that invalid Gemini JSON raises an error."""

    generator = ReadingGuideGenerator(
        client=FakeClient("This is not JSON")
    )

    with pytest.raises(ReadingGuideError):
        generator.generate(create_book())


def test_api_failure_raises_error():
    """Test that API failures are converted to ReadingGuideError."""

    class FailingModels:
        def generate_content(self, model, contents):
            raise RuntimeError("API unavailable")

    class FailingClient:
        def __init__(self):
            self.models = FailingModels()

    generator = ReadingGuideGenerator(
        client=FailingClient()
    )

    with pytest.raises(ReadingGuideError):
        generator.generate(create_book())