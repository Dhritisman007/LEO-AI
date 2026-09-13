from typing import List

__all__ = ["calculate_statistics", "main"]


def calculate_statistics(numbers: List[int]) -> dict:
    """
    Calculate sum, average, max, and min for a list of integers.

    Args:
        numbers: A list of integers to process.

    Returns:
        A dictionary containing 'sum', 'average', 'max', and 'min'.

    Raises:
        ValueError: If the input list is empty.
    """
    if not numbers:
        raise ValueError("The list of numbers cannot be empty.")

    total_sum = sum(numbers)
    average = total_sum / len(numbers)
    maximum = max(numbers)
    minimum = min(numbers)

    return {"sum": total_sum, "average": average, "max": maximum, "min": minimum}


def main() -> None:
    """
    Main execution function to process the predefined list and print results.
    """
    data = [4, 7, 2, 9, 1, 5, 8, 3, 6]
    try:
        stats = calculate_statistics(data)
        print(f"Sum: {stats['sum']}")
        print(f"Average: {stats['average']}")
        print(f"Max: {stats['max']}")
        print(f"Min: {stats['min']}")
    except ValueError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
