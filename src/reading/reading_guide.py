import json
import os

from dotenv import load_dotenv
from google import genai

from src.models.book import Book


load_dotenv()


class ReadingGuideError(Exception):
    """Raised when the AI reading guide cannot be generated."""


class ReadingGuideGenerator:
    """Generate AI-powered reading guides for books using Gemini."""

    def __init__(self, api_key: str | None = None, client=None):
        """Initialize the reading guide generator."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        if client is not None:
            self.client = client
        elif self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def _build_prompt(self, book: Book) -> str:
        """Build the prompt sent to Gemini."""
        authors = ", ".join(book.authors) if book.authors else "Unknown"

        subjects = (
            ", ".join(book.subjects[:10])
            if book.subjects
            else "Not available"
        )

        return f"""
Create a useful reading guide for the following book.

Book title: {book.title}
Authors: {authors}
ISBN: {book.isbn or "Not available"}
Publication year: {book.publication_year or "Not available"}
Subjects: {subjects}
Page count: {book.page_count or "Not available"}

Return ONLY valid JSON using exactly this structure:

{{
    "summary": "A clear plain-language summary of the book.",
    "reading_level": "Beginner, Intermediate, or Advanced",
    "discussion_questions": [
        "Question 1",
        "Question 2",
        "Question 3",
        "Question 4",
        "Question 5"
    ]
}}

Requirements:
- The summary should be concise and easy to understand.
- Select the most appropriate reading level.
- Provide exactly 5 useful discussion or comprehension questions.
- Do not invent specific plot details when the available information is insufficient.
- Return JSON only.
- Do not include markdown or code fences.
"""

    def generate(self, book: Book) -> dict:
        """Generate an AI reading guide for a Book object."""

        if not isinstance(book, Book):
            raise ReadingGuideError("book must be a Book object.")

        if self.client is None:
            raise ReadingGuideError(
                "GEMINI_API_KEY is not configured."
            )

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=self._build_prompt(book),
            )
        except Exception as exc:
            raise ReadingGuideError(
                f"Failed to generate reading guide: {exc}"
            ) from exc

        text = getattr(response, "text", None)

        if not text:
            raise ReadingGuideError(
                "Gemini returned an empty response."
            )

        try:
            cleaned_text = text.strip()

            # Handle responses wrapped in Markdown code fences.
            if cleaned_text.startswith("```"):
                lines = cleaned_text.splitlines()

                if lines and lines[0].strip().startswith("```"):
                    lines = lines[1:]

                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]

                cleaned_text = "\n".join(lines).strip()

            guide = json.loads(cleaned_text)

        except json.JSONDecodeError as exc:
            raise ReadingGuideError(
                "Gemini returned an invalid JSON response."
            ) from exc

        required_fields = {
            "summary",
            "reading_level",
            "discussion_questions",
        }

        if not required_fields.issubset(guide):
            raise ReadingGuideError(
                "Gemini response is missing required fields."
            )

        if not isinstance(guide["summary"], str):
            raise ReadingGuideError(
                "The summary must be a string."
            )

        if not isinstance(guide["reading_level"], str):
            raise ReadingGuideError(
                "The reading level must be a string."
            )

        if not isinstance(guide["discussion_questions"], list):
            raise ReadingGuideError(
                "Discussion questions must be a list."
            )

        if not guide["discussion_questions"]:
            raise ReadingGuideError(
                "At least one discussion question is required."
            )

        return guide

    def generate_guide(
        self,
        title: str | Book,
        author: str = "",
    ) -> dict:
        """Generate a guide from a title/author or an existing Book."""

        if isinstance(title, Book):
            return self.generate(title)

        book = Book(
            title=title,
            authors=[author] if author else [],
        )

        return self.generate(book)