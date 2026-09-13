"""
Hacker News top stories title scraper.

This module fetches the front page of Hacker News (https://news.ycombinator.com),
parses the HTML using BeautifulSoup, extracts story titles, and prints the first 5.
"""

__all__ = ["fetch_html", "extract_titles", "print_top_titles", "main"]

import sys
from typing import List
from bs4 import BeautifulSoup
import requests

# Configuration constants
TARGET_URL: str = "https://news.ycombinator.com"
REQUEST_TIMEOUT_SECONDS: int = 10
MAX_TITLES_TO_PRINT: int = 5
USER_AGENT: str = "Mozilla/5.0 (compatible; LEO-Scraper/1.0; +https://github.com/)"


def fetch_html(url: str) -> str:
    """
    Fetch HTML content from the specified URL.

    Args:
        url: The web URL to fetch.

    Returns:
        The HTML response text as a string.

    Raises:
        requests.RequestException: If the network request fails or returns an HTTP error.

    Example:
        >>> html = fetch_html("https://news.ycombinator.com")
        >>> isinstance(html, str)
        True
    """
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.text
    except requests.RequestException as error:
        raise requests.RequestException(f"Failed to fetch URL '{url}': {error}") from error


def extract_titles(html_content: str) -> List[str]:
    """
    Extract story titles from Hacker News HTML content.

    Args:
        html_content: Raw HTML string of the Hacker News front page.

    Returns:
        A list of extracted story titles as strings.

    Raises:
        ValueError: If html_content is empty or whitespace.

    Example:
        >>> html = '<tr class="athing">...<span class="titleline"><a href="#">Example Title</a></span>...</tr>'
        >>> extract_titles(html)
        ['Example Title']
    """
    if not html_content or not html_content.strip():
        raise ValueError("html_content cannot be empty or whitespace")

    soup = BeautifulSoup(html_content, "html.parser")
    title_elements = soup.select(".titleline > a")
    
    titles: List[str] = []
    for element in title_elements:
        title_text = element.get_text(strip=True)
        if title_text:
            titles.append(title_text)

    return titles


def print_top_titles(titles: List[str], count: int = MAX_TITLES_TO_PRINT) -> None:
    """
    Print the top N titles to standard output.

    Args:
        titles: List of available story titles.
        count: Number of top titles to print.

    Raises:
        ValueError: If count is negative.

    Example:
        >>> print_top_titles(["Title 1", "Title 2"], count=1)
        1. Title 1
    """
    if count < 0:
        raise ValueError(f"count cannot be negative: {count}")

    selected_titles = titles[:count]
    for index, title in enumerate(selected_titles, start=1):
        print(f"{index}. {title}")


def main() -> None:
    """
    Main execution flow for the Hacker News scraper script.
    """
    try:
        html = fetch_html(TARGET_URL)
        titles = extract_titles(html)
        if not titles:
            print("No titles found on the page.", file=sys.stderr)
            sys.exit(1)
        print_top_titles(titles, MAX_TITLES_TO_PRINT)
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
