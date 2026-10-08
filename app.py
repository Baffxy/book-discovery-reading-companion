from pathlib import Path
import json

import streamlit as st

from src.api.open_library import OpenLibraryClient, OpenLibraryError
from src.models.book import Book
from src.reading.reading_guide import (
    ReadingGuideError,
    ReadingGuideGenerator,
)
from src.reading.reading_list import ReadingListManager
from src.recommendations.similar_books import SimilarBooksRecommender
from src.utils.storage import (
    StorageError,
    load_reading_list,
    save_reading_list,
)
from src.utils.validators import is_valid_isbn, validate_title


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="Book Discovery & Reading Companion",
    page_icon="📚",
    layout="wide",
)


# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------

STORAGE_FILE = Path("data/reading_list.json")
READING_GUIDE_FILE = Path("data/reading_guide.json")

READING_STATUSES = [
    "Want to Read",
    "Reading",
    "Finished",
]


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

if "reading_list" not in st.session_state:
    try:
        st.session_state.reading_list = load_reading_list(
            STORAGE_FILE
        )
    except StorageError:
        st.session_state.reading_list = ReadingListManager()


if "search_results" not in st.session_state:
    st.session_state.search_results = []


if "selected_book" not in st.session_state:
    st.session_state.selected_book = None


if "current_reading_guide" not in st.session_state:
    st.session_state.current_reading_guide = None


if "similar_books" not in st.session_state:
    st.session_state.similar_books = []


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def save_current_reading_list() -> None:
    """Save the current reading list to local JSON storage."""

    try:
        save_reading_list(
            st.session_state.reading_list,
            STORAGE_FILE,
        )

        st.success(
            "Reading list saved successfully."
        )

    except StorageError as exc:
        st.error(str(exc))


def save_current_reading_guide(
    book: Book,
    guide: dict,
) -> None:
    """Save the generated reading guide to local JSON storage."""

    guide_data = {
        "book": {
            "title": book.title,
            "authors": book.authors,
            "isbn": book.isbn,
        },
        "reading_guide": guide,
    }

    try:
        READING_GUIDE_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with READING_GUIDE_FILE.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                guide_data,
                file,
                indent=4,
                ensure_ascii=False,
            )

        st.success(
            "Reading guide saved successfully."
        )

    except OSError as exc:
        st.error(
            f"Failed to save reading guide: {exc}"
        )


def display_book(book: Book) -> None:
    """Display the details of a book."""

    col1, col2 = st.columns([1, 3])

    with col1:
        if book.cover_url:
            st.image(
                book.cover_url,
                width=180,
            )
        else:
            st.info("No cover available.")

    with col2:
        st.subheader(book.title)

        st.write(
            f"**Author(s):** {book.display_authors()}"
        )

        if book.publication_year:
            st.write(
                f"**First publication:** "
                f"{book.publication_year}"
            )

        if book.isbn:
            st.write(
                f"**ISBN:** {book.isbn}"
            )

        if book.page_count:
            st.write(
                f"**Pages:** {book.page_count}"
            )

        if book.subjects:
            st.write(
                "**Subjects:** "
                + ", ".join(book.subjects[:10])
            )


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.title(
    "📚 Book Discovery & Reading Companion"
)

st.caption(
    "Search books, build your reading list, "
    "generate AI reading guides, and discover similar books."
)


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:
    st.header("📚 Reading List")

    entries = (
        st.session_state.reading_list.get_entries()
    )

    st.metric(
        "Books in your list",
        len(entries),
    )

    status_counts = {
        status: 0
        for status in READING_STATUSES
    }

    for _, status in entries:
        status_counts[status] += 1

    for status in READING_STATUSES:
        st.write(
            f"**{status}:** {status_counts[status]}"
        )

    st.divider()

    if st.button(
        "💾 Save Reading List",
        use_container_width=True,
    ):
        save_current_reading_list()


# ---------------------------------------------------------
# Search section
# ---------------------------------------------------------

st.header("🔎 Discover Books")

search_query = st.text_input(
    "Search by title, author, or ISBN",
    placeholder=(
        "e.g. The Hobbit, J.R.R. Tolkien, "
        "or 9780261102217"
    ),
)

search_limit = st.slider(
    "Maximum results",
    min_value=1,
    max_value=10,
    value=5,
)


if st.button(
    "🔍 Search",
    type="primary",
):
    if not search_query.strip():
        st.warning(
            "Please enter a title, author, or ISBN."
        )

    else:
        try:
            client = OpenLibraryClient()

            st.session_state.search_results = (
                client.search_books(
                    search_query,
                    limit=search_limit,
                )
            )

            if not st.session_state.search_results:
                st.info("No books found.")

        except (
            OpenLibraryError,
            ValueError,
        ) as exc:
            st.error(str(exc))


# ---------------------------------------------------------
# Search results
# ---------------------------------------------------------

if st.session_state.search_results:
    st.subheader("Search Results")

    for index, book in enumerate(
        st.session_state.search_results
    ):
        with st.container(border=True):

            result_col1, result_col2 = st.columns(
                [1, 4]
            )

            with result_col1:
                if book.cover_url:
                    st.image(
                        book.cover_url,
                        width=100,
                    )

            with result_col2:
                st.markdown(
                    f"### {book.title}"
                )

                st.write(
                    f"**Author(s):** "
                    f"{book.display_authors()}"
                )

                if book.publication_year:
                    st.write(
                        f"**First published:** "
                        f"{book.publication_year}"
                    )

                if book.isbn:
                    st.write(
                        f"**ISBN:** {book.isbn}"
                    )

                if st.button(
                    "View Details",
                    key=f"details_{index}",
                ):
                    st.session_state.selected_book = (
                        book
                    )

                    # Clear results belonging to
                    # the previously selected book.
                    st.session_state.current_reading_guide = None
                    st.session_state.similar_books = []

            st.divider()


# ---------------------------------------------------------
# Selected book
# ---------------------------------------------------------

selected_book = (
    st.session_state.selected_book
)


if selected_book:

    st.header("📖 Book Details")

    display_book(selected_book)

    st.divider()


    # -----------------------------------------------------
    # Reading list controls
    # -----------------------------------------------------

    st.subheader("📚 Add to Reading List")

    if selected_book.isbn:
        isbn_valid = is_valid_isbn(
            selected_book.isbn
        )

        if not isbn_valid:
            st.warning(
                "The ISBN returned by Open Library "
                "could not be validated."
            )

    if not validate_title(
        selected_book.title
    ):
        st.error(
            "This book has an invalid title."
        )

    else:
        selected_status = st.selectbox(
            "Reading status",
            READING_STATUSES,
            key="selected_book_status",
        )

        add_col, remove_col = st.columns(2)


        # -------------------------------------------------
        # Add to reading list
        # -------------------------------------------------

        with add_col:

            if st.button(
                "➕ Add to Reading List",
                use_container_width=True,
            ):

                try:
                    st.session_state.reading_list.add_book(
                        selected_book,
                        status=selected_status,
                    )

                    save_current_reading_list()

                except ValueError as exc:
                    st.warning(str(exc))


        # -------------------------------------------------
        # Remove from reading list
        # -------------------------------------------------

        with remove_col:

            if st.button(
                "🗑️ Remove from Reading List",
                use_container_width=True,
            ):

                if selected_book.isbn:

                    try:
                        st.session_state.reading_list.remove_book(
                            selected_book.isbn
                        )

                        save_current_reading_list()

                    except (
                        ValueError,
                        KeyError,
                    ) as exc:
                        st.warning(str(exc))

                else:
                    st.warning(
                        "This book does not have an ISBN."
                    )


    st.divider()


    # -----------------------------------------------------
    # AI Reading Guide
    # -----------------------------------------------------

    st.subheader("🤖 AI Reading Guide")

    if st.button(
        "✨ Generate Reading Guide",
        key="generate_guide",
    ):

        try:
            generator = ReadingGuideGenerator()

            with st.spinner(
                "Generating reading guide..."
            ):
                guide = generator.generate(
                    selected_book
                )

            st.session_state.current_reading_guide = (
                guide
            )

        except ReadingGuideError as exc:
            st.error(str(exc))


    guide = (
        st.session_state.current_reading_guide
    )


    # -----------------------------------------------------
    # Display generated guide
    # -----------------------------------------------------

    if guide:

        st.markdown("### Summary")

        st.write(
            guide["summary"]
        )


        st.markdown("### Reading Level")

        st.info(
            guide["reading_level"]
        )


        st.markdown(
            "### Discussion Questions"
        )

        for number, question in enumerate(
            guide["discussion_questions"],
            start=1,
        ):
            st.write(
                f"**{number}.** {question}"
            )


        # -------------------------------------------------
        # Save generated guide
        # -------------------------------------------------

        if st.button(
            "💾 Save Reading Guide",
            key="save_reading_guide",
        ):
            save_current_reading_guide(
                selected_book,
                guide,
            )


    st.divider()


    # -----------------------------------------------------
    # Similar books
    # -----------------------------------------------------

    st.subheader("📚 Similar Books")

    if st.button(
        "🔎 Find Similar Books",
        key="find_similar",
    ):

        recommender = (
            SimilarBooksRecommender(
                st.session_state.search_results
            )
        )

        similar_books = (
            recommender.recommend(
                selected_book,
                books=st.session_state.search_results,
                limit=5,
            )
        )

        st.session_state.similar_books = (
            similar_books
        )


    similar_books = (
        st.session_state.similar_books
    )


    if similar_books:

        for book in similar_books:

            with st.container(
                border=True
            ):

                st.write(
                    f"**{book.title}**"
                )

                st.write(
                    book.display_authors()
                )

                if book.publication_year:
                    st.caption(
                        f"Published: "
                        f"{book.publication_year}"
                    )

    else:
        st.info(
            "Search for books first, then select "
            "a book to discover similar titles."
        )


# ---------------------------------------------------------
# Reading list section
# ---------------------------------------------------------

st.divider()

st.header("📖 My Reading List")

entries = (
    st.session_state.reading_list.get_entries()
)


if not entries:

    st.info(
        "Your reading list is empty. "
        "Search for a book and add it above."
    )


else:

    for index, (book, status) in enumerate(
        entries
    ):

        with st.container(
            border=True
        ):

            list_col1, list_col2, list_col3 = (
                st.columns([3, 2, 1])
            )


            # ---------------------------------------------
            # Book information
            # ---------------------------------------------

            with list_col1:

                st.write(
                    f"**{book.title}**"
                )

                st.caption(
                    book.display_authors()
                )


            # ---------------------------------------------
            # Status
            # ---------------------------------------------

            with list_col2:

                new_status = st.selectbox(
                    "Status",
                    READING_STATUSES,
                    index=READING_STATUSES.index(
                        status
                    ),
                    key=f"status_{index}",
                )


                if new_status != status:

                    if book.isbn:

                        try:

                            st.session_state.reading_list.update_status(
                                book.isbn,
                                new_status,
                            )

                            save_current_reading_list()

                            st.rerun()

                        except (
                            ValueError,
                            KeyError,
                        ) as exc:
                            st.error(str(exc))

                    else:
                        st.warning(
                            "This book does not have "
                            "an ISBN, so its status "
                            "cannot be updated here."
                        )


            # ---------------------------------------------
            # Remove
            # ---------------------------------------------

            with list_col3:

                if st.button(
                    "Remove",
                    key=f"remove_{index}",
                ):

                    if book.isbn:

                        try:

                            st.session_state.reading_list.remove_book(
                                book.isbn
                            )

                            save_current_reading_list()

                            st.rerun()

                        except (
                            ValueError,
                            KeyError,
                        ) as exc:
                            st.error(str(exc))

                    else:
                        st.warning(
                            "Cannot remove a book "
                            "without an ISBN."
                        )