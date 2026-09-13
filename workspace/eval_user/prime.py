import math

__all__ = ["is_prime"]


def is_prime(n: int) -> bool:
    """
    Checks if a given integer is a prime number.

    Args:
        n: The integer to check.

    Returns:
        True if n is prime, False otherwise.

    Example:
        >>> is_prime(17)
        True
        >>> is_prime(15)
        False
    """
    if not isinstance(n, int):
        raise ValueError("Input must be an integer.")

    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False

    # Optimization: check divisors up to sqrt(n)
    # Primes > 3 are of the form 6k +/- 1
    for i in range(5, int(math.sqrt(n)) + 1, 6):
        if n % i == 0 or n % (i + 2) == 0:
            return False

    return True


if __name__ == "__main__":
    print(f"Is 17 prime? {is_prime(17)}")
    print(f"Is 15 prime? {is_prime(15)}")
