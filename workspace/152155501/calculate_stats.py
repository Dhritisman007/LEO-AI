"""
Module to calculate statistical metrics for a predefined list of numbers.

This script computes the mean, median, max, min, and standard deviation
of a dataset using Python's built-in statistics module.
"""

__all__ = ["calculate_dataset_statistics", "main"]

import statistics
from dataclasses import dataclass
from typing import Sequence

DATASET: list[float] = [23.0, 45.0, 12.0, 67.0, 34.0, 89.0, 11.0, 56.0]

@dataclass(frozen=True)
class DatasetStatistics:
    """
    Container for statistical metrics of a dataset.
    
    Attributes:
        mean: The arithmetic mean.
        median: The median value.
        maximum: The maximum value.
        minimum: The minimum value.
        std_dev: The sample standard deviation.
    """
    mean: float
    median: float
    maximum: float
    minimum: float
    std_dev: float


def calculate_dataset_statistics(data: Sequence[float]) -> DatasetStatistics:
    """
    Calculate mean, median, max, min, and standard deviation for a sequence of numbers.
    
    Args:
        data: A sequence of numeric values. Must contain at least 2 elements for std dev.
        
    Returns:
        DatasetStatistics object containing the computed metrics.
        
    Raises:
        ValueError: If data is empty or has fewer than 2 elements for standard deviation.
        
    Example:
        >>> stats = calculate_dataset_statistics([1.0, 2.0, 3.0])
        >>> stats.mean
        2.0
    """
    if not data:
        raise ValueError("Dataset cannot be empty.")
    if len(data) < 2:
        raise ValueError("Dataset must contain at least 2 elements to calculate standard deviation.")

    mean_val: float = statistics.mean(data)
    median_val: float = statistics.median(data)
    max_val: float = max(data)
    min_val: float = min(data)
    std_dev_val: float = statistics.stdev(data)

    return DatasetStatistics(
        mean=mean_val,
        median=median_val,
        maximum=max_val,
        minimum=min_val,
        std_dev=std_dev_val
    )


def main() -> None:
    """
    Execute the statistics calculation on the predefined dataset and print results.
    """
    stats = calculate_dataset_statistics(DATASET)
    print(f"Dataset: {DATASET}")
    print(f"Mean:               {stats.mean:.2f}")
    print(f"Median:             {stats.median:.2f}")
    print(f"Max:                {stats.maximum:.2f}")
    print(f"Min:                {stats.minimum:.2f}")
    print(f"Standard Deviation: {stats.std_dev:.2f}")


if __name__ == "__main__":
    main()
