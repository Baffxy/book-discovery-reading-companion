"""PostgreSQL persistence for the Book Discovery & Reading Companion."""

import os

import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

from src.models.book import Book
from src.reading.reading_list import ReadingListManager


# Load local environment variables during development.
load_dotenv()


class DatabaseError(Exception):
    """Raised when a database operation fails."""


def get_database_url() -> str:
    """Return the PostgreSQL connection string.

    Check local environment variables first, then Streamlit secrets.
    """

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        try:
            import streamlit as st

            database_url = st.secrets.get("DATABASE_URL")

        except Exception:
            # Streamlit secrets might not be configured locally.
            database_url = None

    if not database_url:
        raise DatabaseError(
            "DATABASE_URL is not configured. "
            "Set it in your local .env file or "
            "Streamlit Community Cloud secrets."
        )

    return database_url


def get_connection():
    """Create a connection to the configured PostgreSQL database."""

    try:
        return psycopg.connect(
            get_database_url(),
            connect_timeout=10,
        )

    except (psycopg.Error, DatabaseError) as exc:
        raise DatabaseError(
            f"Could not connect to PostgreSQL: {exc}"
        ) from exc


def initialize_database() -> None:
    """Create the application's database tables if necessary."""

    statements = [
        """
        CREATE TABLE IF NOT EXISTS reading_list (
            book_key TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            authors JSONB NOT NULL DEFAULT '[]'::jsonb,
            isbn TEXT,
            publication_year INTEGER,
            subjects JSONB NOT NULL DEFAULT '[]'::jsonb,
            page_count INTEGER,
            cover_url TEXT,
            status TEXT NOT NULL DEFAULT 'Want to Read',
            CONSTRAINT valid_reading_status
                CHECK (
                    status IN (
                        'Want to Read',
                        'Reading',
                        'Finished'
                    )
                )
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS reading_guides (
            id BIGSERIAL PRIMARY KEY,
            book_title TEXT NOT NULL,
            authors JSONB NOT NULL DEFAULT '[]'::jsonb,
            isbn TEXT,
            summary TEXT NOT NULL,
            reading_level TEXT NOT NULL,
            discussion_questions JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
    ]

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)

    except (psycopg.Error, DatabaseError) as exc:
        raise DatabaseError(
            f"Could not initialize the database: {exc}"
        ) from exc


def _book_key(book: Book) -> str:
    """Generate a stable identifier, including for books without ISBNs."""

    if book.isbn:
        normalized_isbn = (
            book.isbn.replace("-", "")
            .replace(" ", "")
            .strip()
            .upper()
        )

        if normalized_isbn:
            return f"isbn:{normalized_isbn}"

    normalized_title = book.title.strip().casefold()

    normalized_authors = "|".join(
        author.strip().casefold()
        for author in book.authors
    )

    return f"title:{normalized_title}|authors:{normalized_authors}"


def save_reading_list_to_database(
    reading_list: ReadingListManager,
) -> None:
    """Replace the shared database reading list with the supplied list."""

    if not isinstance(reading_list, ReadingListManager):
        raise DatabaseError(
            "reading_list must be a ReadingListManager."
        )

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                # Replace the shared list in a single transaction.
                cursor.execute("DELETE FROM reading_list;")

                for book, status in reading_list.get_entries():
                    cursor.execute(
                        """
                        INSERT INTO reading_list (
                            book_key,
                            title,
                            authors,
                            isbn,
                            publication_year,
                            subjects,
                            page_count,
                            cover_url,
                            status
                        )
                        VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s
                        );
                        """,
                        (
                            _book_key(book),
                            book.title,
                            Jsonb(book.authors),
                            book.isbn,
                            book.publication_year,
                            Jsonb(book.subjects),
                            book.page_count,
                            book.cover_url,
                            status,
                        ),
                    )

    except (psycopg.Error, DatabaseError) as exc:
        raise DatabaseError(
            f"Could not save the reading list: {exc}"
        ) from exc


def load_reading_list_from_database() -> ReadingListManager:
    """Load the shared reading list from PostgreSQL."""

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        title,
                        authors,
                        isbn,
                        publication_year,
                        subjects,
                        page_count,
                        cover_url,
                        status
                    FROM reading_list
                    ORDER BY title;
                    """
                )

                rows = cursor.fetchall()

    except (psycopg.Error, DatabaseError) as exc:
        raise DatabaseError(
            f"Could not load the reading list: {exc}"
        ) from exc

    reading_list = ReadingListManager()

    try:
        for row in rows:
            (
                title,
                authors,
                isbn,
                publication_year,
                subjects,
                page_count,
                cover_url,
                status,
            ) = row

            book = Book(
                title=title,
                authors=authors,
                isbn=isbn,
                publication_year=publication_year,
                subjects=subjects,
                page_count=page_count,
                cover_url=cover_url,
            )

            reading_list.add_book(
                book,
                status=status,
            )

    except (TypeError, ValueError) as exc:
        raise DatabaseError(
            f"Invalid book data in the database: {exc}"
        ) from exc

    return reading_list


def save_reading_guide_to_database(
    book: Book,
    guide: dict,
) -> None:
    """Save a generated reading guide in PostgreSQL."""

    if not isinstance(book, Book):
        raise DatabaseError(
            "book must be a Book instance."
        )

    if not isinstance(guide, dict):
        raise DatabaseError(
            "guide must be a dictionary."
        )

    required_fields = {
        "summary",
        "reading_level",
        "discussion_questions",
    }

    if not required_fields.issubset(guide):
        raise DatabaseError(
            "The reading guide is missing required fields."
        )

    if not isinstance(guide["summary"], str):
        raise DatabaseError(
            "The reading guide summary must be a string."
        )

    if not isinstance(guide["reading_level"], str):
        raise DatabaseError(
            "The reading level must be a string."
        )

    if not isinstance(guide["discussion_questions"], list):
        raise DatabaseError(
            "Discussion questions must be a list."
        )

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO reading_guides (
                        book_title,
                        authors,
                        isbn,
                        summary,
                        reading_level,
                        discussion_questions
                    )
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    (
                        book.title,
                        Jsonb(book.authors),
                        book.isbn,
                        guide["summary"],
                        guide["reading_level"],
                        Jsonb(guide["discussion_questions"]),
                    ),
                )

    except (psycopg.Error, DatabaseError) as exc:
        raise DatabaseError(
            f"Could not save the reading guide: {exc}"
        ) from exc


def load_saved_reading_guides(
    limit: int = 20,
) -> list[dict]:
    """Load the most recently saved reading guides."""

    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or limit < 1
    ):
        raise DatabaseError(
            "limit must be a positive integer."
        )

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        book_title,
                        authors,
                        isbn,
                        summary,
                        reading_level,
                        discussion_questions,
                        created_at
                    FROM reading_guides
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s;
                    """,
                    (limit,),
                )

                rows = cursor.fetchall()

    except (psycopg.Error, DatabaseError) as exc:
        raise DatabaseError(
            f"Could not load saved reading guides: {exc}"
        ) from exc

    return [
        {
            "id": row[0],
            "book_title": row[1],
            "authors": row[2],
            "isbn": row[3],
            "summary": row[4],
            "reading_level": row[5],
            "discussion_questions": row[6],
            "created_at": row[7],
        }
        for row in rows
    ]