__all__ = ["get_fibonacci"]


def get_fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number using an iterative approach.

    Args:
        n: The position in the Fibonacci sequence (0-indexed).

    Returns:
        The nth Fibonacci number.

    Raises:
        ValueError: If n is a negative integer.

    Example:
        >>> get_fibonacci(10)
        55
    """
    if n < 0:
        raise ValueError("n must be a non-negative integer")
    if n == 0:
        return 0
    if n == 1:
        return 1

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


if __name__ == "__main__":
    N = 10
    result = get_fibonacci(N)
    print(f"The {N}th Fibonacci number is {result}")
