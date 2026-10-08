from src.utils.validators import (
    is_valid_isbn,
    normalize_isbn,
    validate_title,
)


def test_normalize_isbn():
    """Test ISBN spaces and hyphens are removed."""

    assert normalize_isbn("978-0-261-10221-7") == "9780261102217"
    assert normalize_isbn("0-306-40615-2") == "0306406152"


def test_valid_isbn_13():
    """Test valid ISBN-13 values."""

    assert is_valid_isbn("9780261102217")
    assert is_valid_isbn("978-0-261-10221-7")


def test_valid_isbn_10():
    """Test valid ISBN-10 values."""

    assert is_valid_isbn("0306406152")
    assert is_valid_isbn("0-306-40615-2")


def test_invalid_isbn():
    """Test invalid ISBN values."""

    assert not is_valid_isbn("1234567890")
    assert not is_valid_isbn("9780261102218")
    assert not is_valid_isbn("not-an-isbn")


def test_empty_isbn():
    """Test empty ISBN input."""

    assert not is_valid_isbn("")


def test_validate_title():
    """Test valid and invalid book titles."""

    assert validate_title("The Hobbit")
    assert validate_title("  The Hobbit  ")

    assert not validate_title("")
    assert not validate_title("   ")
    assert not validate_title(None)