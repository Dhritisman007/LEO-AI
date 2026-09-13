"""
Module for calculating Fibonacci numbers with high performance and correctness.
"""

from dataclasses import dataclass
from typing import Final

__all__ = ["calculate_fibonacci", "FibonacciResult"]

MAX_N: Final[int] = 1000


@dataclass(frozen=True)
class FibonacciResult:
    """
    Container for Fibonacci calculation results.
    
    Attributes:
        n: The input index.
        value: The calculated Fibonacci number.
    """
    n: int
    value: int


def calculate_fibonacci(n: int) -> FibonacciResult:
    """
    Calculate the nth Fibonacci number efficiently using iteration.
    
    Args:
        n: The non-negative integer index of the Fibonacci sequence.
           F(0) = 0, F(1) = 1, F(2) = 1, etc.
    
    Returns:
        FibonacciResult containing n and its corresponding Fibonacci value.
    
    Raises:
        ValueError: If n is negative or exceeds MAX_N.
    
    Example:
        >>> result = calculate_fibonacci(10)
        >>> result.value
        55
    """
    if n < 0:
        raise ValueError(f"n must be a non-negative integer, got {n}")
    if n > MAX_N:
        raise ValueError(f"n cannot exceed {MAX_N}, got {n}")
    
    if n == 0:
        return FibonacciResult(n=0, value=0)
    if n == 1:
        return FibonacciResult(n=1, value=1)

    # Iterative calculation for O(n) time and O(1) space complexity
    prev_prev: int = 0
    prev: int = 1
    current: int = 1
    
    for _ in range(2, n + 1):
        current = prev_prev + prev
        prev_prev = prev
        prev = current
        
    return FibonacciResult(n=n, value=current)


if __name__ == "__main__":
    for i in range(15):
        result = calculate_fibonacci(i)
        print(f"F({result.n}) = {result.value}")
