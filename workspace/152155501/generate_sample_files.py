"""Module to generate sample files with various extensions in the workspace.

This script creates five distinct sample files (.txt, .py, .json, .csv, .md)
with meaningful placeholder content, demonstrating robust file handling using pathlib.
"""

from pathlib import Path
from typing import Dict

__all__ = ["create_sample_files", "SAMPLE_FILES_DATA"]

# Configuration mapping file names to their corresponding sample content
SAMPLE_FILES_DATA: Dict[str, str] = {
    "sample.txt": "This is a sample text file.\nCreated by LEO's Python File Generation Specialist.\n",
    "sample.py": (
        "\"\"\"Sample Python module.\"\"\"\n\n"
        "def greet(name: str) -> str:\n"
        "    \"\"\"Return a greeting message.\"\"\"\n"
        "    return f'Hello, {name}!'\n\n"
        "if __name__ == '__main__':\n"
        "    print(greet('World'))\n"
    ),
    "sample.json": (
        "{\n"
        "  \"name\": \"sample\",\n"
        "  \"type\": \"json\",\n"
        "  \"version\": 1.0,\n"
        "  \"active\": true\n"
        "}\n"
    ),
    "sample.csv": (
        "id,name,role\n"
        "1,Alice,Engineer\n"
        "2,Bob,Designer\n"
        "3,Charlie,Manager\n"
    ),
    "sample.md": (
        "# Sample Markdown Document\n\n"
        "This is a sample markdown file generated automatically.\n\n"
        "- Item one\n"
        "- Item two\n"
    ),
}


def create_sample_files(target_directory: Path = Path(".")) -> None:
    """Create sample files with different extensions in the target directory.

    Args:
        target_directory: The directory where files will be created.

    Raises:
        OSError: If file creation fails due to I/O issues.

    Example:
        >>> create_sample_files()
    """
    for filename, content in SAMPLE_FILES_DATA.items():
        file_path: Path = target_directory / filename
        try:
            file_path.write_text(content, encoding="utf-8")
            print(f"Successfully created: {file_path}")
        except OSError as exc:
            raise OSError(f"Failed to create file {file_path}: {exc}") from exc


if __name__ == "__main__":
    create_sample_files()
