"""
Module to calculate and print the product of two integers.
"""

__all__ = ["calculate_product", "main"]

MULTIPLIER_A = 17
MULTIPLIER_B = 23


def calculate_product(factor_a: int, factor_b: int) -> int:
    """
    Calculate the product of two integers.

    Args:
        factor_a: The first integer.
        factor_b: The second integer.

    Returns:
        The product of factor_a and factor_b.

    Raises:
        TypeError: If inputs are not integers.

    Example:
        >>> calculate_product(2, 3)
        6
    """
    if not isinstance(factor_a, int) or not isinstance(factor_b, int):
        raise TypeError("Both factors must be integers")
    
    return factor_a * factor_b


def main() -> None:
    """
    Main entry point of the script.
    Calculates the product of MULTIPLIER_A and MULTIPLIER_B and prints the result.
    """
    result = calculate_product(MULTIPLIER_A, MULTIPLIER_B)
    print(result)


if __name__ == "__main__":
    main()
