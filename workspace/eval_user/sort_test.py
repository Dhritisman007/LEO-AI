"""
Module to sort a predefined list of integers and print the sorted result.

This script demonstrates clean Python coding standards, including type hints,
docstrings, and error handling.
"""

__all__ = ["sort_numbers"]

def sort_numbers(numbers: list[int]) -> list[int]:
    """
    Sort a list of integers in ascending order.

    Args:
        numbers: List of integers to be sorted. Must not be None.

    Returns:
        A new list containing the integers sorted in ascending order.

    Raises:
        ValueError: If numbers is None.

    Example:
        >>> sort_numbers([5, 2, 8, 1, 9, 3])
        [1, 2, 3, 5, 8, 9]
    """
    if numbers is None:
        raise ValueError("numbers cannot be None")
    
    return sorted(numbers)


def main() -> None:
    """
    Main execution entry point for the sort test script.
    
    Sorts the target list [5, 2, 8, 1, 9, 3] and prints the result.
    """
    target_list = [5, 2, 8, 1, 9, 3]
    sorted_list = sort_numbers(target_list)
    print(f"Sorted result: {sorted_list}")


if __name__ == "__main__":
    main()
