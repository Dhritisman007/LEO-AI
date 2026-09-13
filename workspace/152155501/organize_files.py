#!/usr/bin/env python3
"""File system organization utility to categorize files by extension.

This module provides robust file organization capabilities, moving files
into dedicated subdirectories corresponding to their file extensions.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
import shutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_EXCLUDED_DIRS: Set[str] = {
    '.git',
    '__pycache__',
    '.pytest_cache',
    'venv',
    'env'
}
DEFAULT_EXCLUDED_FILES: Set[str] = {
    'organize_files.py',
    'create_samples.py',
    'generate_sample_files.py',
    'install_commit_gen.sh'
}


def organize_directory(
    target_dir: Path,
    excluded_dirs: Optional[Set[str]] = None,
    excluded_files: Optional[Set[str]] = None,
    dry_run: bool = False
) -> Dict[str, List[str]]:
    """Organize files in the target directory into subfolders based on extensions.

    Args:
        target_dir (Path): The directory containing files to organize.
        excluded_dirs (Optional[Set[str]]): Directory names to ignore.
        excluded_files (Optional[Set[str]]): File names to ignore.
        dry_run (bool): If True, simulate actions without moving files.

    Returns:
        Dict[str, List[str]]: A mapping of extension categories to lists of moved filenames.

    Raises:
        NotADirectoryError: If target_dir does not exist or is not a directory.

    Example:
        >>> moved = organize_directory(Path('.'))
        >>> print(moved)
        {'txt': ['sample.txt'], 'py': ['script.py']}
    """
    if not target_dir.exists() or not target_dir.is_dir():
        raise NotADirectoryError(f"Target path '{target_dir}' is not a valid directory.")

    ignored_dirs = excluded_dirs if excluded_dirs is not None else DEFAULT_EXCLUDED_DIRS
    ignored_files = excluded_files if excluded_files is not None else DEFAULT_EXCLUDED_FILES

    organization_results: Dict[str, List[str]] = {}

    for item in target_dir.iterdir():
        if item.is_dir():
            if item.name in ignored_dirs:
                logger.debug(f"Skipping excluded directory: {item.name}")
            continue

        if item.name in ignored_files:
            logger.debug(f"Skipping excluded file: {item.name}")
            continue

        # Extract file extension (lowercase, strip leading dot)
        ext = item.suffix.lower().lstrip('.')
        if not ext:
            ext = 'no_extension'

        # Create destination subfolder
        dest_folder = target_dir / ext
        if not dry_run:
            dest_folder.mkdir(parents=True, exist_ok=True)

        dest_path = dest_folder / item.name

        logger.info(f"{'[DRY RUN] ' if dry_run else ''}Moving '{item.name}' -> '{ext}/{item.name}'")

        if not dry_run:
            try:
                if dest_path.exists():
                    logger.warning(f"Destination '{dest_path}' already exists.")
                shutil.move(str(item), str(dest_path))
            except Exception as e:
                logger.error(f"Failed to move {item.name} to {dest_folder}: {e}")
                raise

        organization_results.setdefault(ext, []).append(item.name)

    return organization_results


def main() -> None:
    """Main entry point for file organization script."""
    workspace_dir = Path(__file__).resolve().parent
    logger.info(f"Starting file organization in workspace: {workspace_dir}")
    
    try:
        results = organize_directory(workspace_dir, dry_run=False)
        logger.info("File organization completed successfully.")
        logger.info(f"Summary of organized files: {results}")
    except Exception as e:
        logger.error(f"Error during file organization: {e}")
        raise


if __name__ == '__main__':
    main()
