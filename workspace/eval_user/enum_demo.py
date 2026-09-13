from typing import Iterable

__all__ = ["print_indexed_items"]


def print_indexed_items(items: Iterable[str]) -> None:
    """
    Iterates through a list and prints each item with its index.

    Args:
        items: An iterable of strings to be printed.

    Returns:
        None
    """
    if not items:
        print("The list is empty.")
        return

    for index, value in enumerate(items):
        print(f"{index}: {value}")


if __name__ == "__main__":
    fruits = ["apple", "banana", "cherry"]
    print_indexed_items(fruits)
