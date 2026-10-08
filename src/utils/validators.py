import re


def normalize_isbn(isbn: str) -> str:
    """Remove spaces and hyphens from an ISBN."""

    if not isinstance(isbn, str):
        return ""

    return re.sub(r"[\s-]", "", isbn).upper()


def is_valid_isbn(isbn: str) -> bool:
    """Validate an ISBN-10 or ISBN-13."""

    normalized = normalize_isbn(isbn)

    if len(normalized) == 10:
        if not re.fullmatch(r"\d{9}[\dX]", normalized):
            return False

        total = 0

        for index, character in enumerate(normalized):
            value = 10 if character == "X" else int(character)
            total += value * (10 - index)

        return total % 11 == 0

    if len(normalized) == 13:
        if not normalized.isdigit():
            return False

        total = 0

        for index, character in enumerate(normalized):
            value = int(character)

            if index % 2 == 0:
                total += value
            else:
                total += value * 3

        return total % 10 == 0

    return False


def validate_title(title: str) -> bool:
    """Validate that a book title is a non-empty string."""

    if not isinstance(title, str):
        return False

    return bool(title.strip())