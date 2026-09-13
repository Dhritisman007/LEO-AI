__all__ = ["is_palindrome"]


def is_palindrome(text: str) -> bool:
    """
    Checks if a given string is a palindrome.

    Args:
        text: The string to check.

    Returns:
        True if the string is a palindrome, False otherwise.

    Example:
        >>> is_palindrome('racecar')
        True
        >>> is_palindrome('hello')
        False
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string.")

    # Normalize by removing non-alphanumeric and case-folding if needed,
    # but for this requirement, we perform a direct comparison.
    return text == text[::-1]


if __name__ == "__main__":
    test_cases = ["racecar", "hello"]
    for case in test_cases:
        result = is_palindrome(case)
        print(f"'{case}': {result}")
