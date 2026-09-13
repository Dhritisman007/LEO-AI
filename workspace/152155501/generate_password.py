"""
Module for generating cryptographically secure random passwords.

This module provides functionality to generate passwords using Python's
'secrets' module, guaranteeing sufficient entropy and diverse character sets.
"""

import string
import secrets
from typing import Final

# Configuration constants
DEFAULT_PASSWORD_LENGTH: Final[int] = 16
MIN_PASSWORD_LENGTH: Final[int] = 4


def generate_password(length: int = DEFAULT_PASSWORD_LENGTH) -> str:
    """Generate a secure random password with diverse character types.

    Args:
        length: The length of the password to generate. Defaults to 16.

    Returns:
        A securely generated random password string.

    Raises:
        ValueError: If the requested length is less than MIN_PASSWORD_LENGTH.

    Example:
        >>> password = generate_password(16)
        >>> len(password)
        16
    """
    if length < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password length must be at least {MIN_PASSWORD_LENGTH}, got {length}"
        )

    # Define character pools
    uppercase_pool: Final[str] = string.ascii_uppercase
    lowercase_pool: Final[str] = string.ascii_lowercase
    digits_pool: Final[str] = string.digits
    symbols_pool: Final[str] = string.punctuation

    # Guarantee at least one character from each required category
    password_chars = [
        secrets.choice(uppercase_pool),
        secrets.choice(lowercase_pool),
        secrets.choice(digits_pool),
        secrets.choice(symbols_pool),
    ]

    # Fill the remaining length with a combination of all pools
    all_characters: Final[str] = (
        uppercase_pool + lowercase_pool + digits_pool + symbols_pool
    )
    for _ in range(length - len(password_chars)):
        password_chars.append(secrets.choice(all_characters))

    # Shuffle the characters securely to avoid predictable initial positions
    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars)


if __name__ == "__main__":
    secure_password = generate_password()
    print(f"Generated secure password: {secure_password}")
