"""
Module for printing a greeting from LEO.
"""

__all__ = ["main"]

GREETING_MESSAGE = "Hello from LEO"


def main() -> None:
    """
    Print the greeting message to standard output.
    
    Args:
        None
    
    Returns:
        None
    
    Raises:
        None
    
    Example:
        >>> main()
        Hello from LEO
    """
    print(GREETING_MESSAGE)


if __name__ == "__main__":
    main()
