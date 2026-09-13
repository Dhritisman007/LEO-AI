import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

class CSVProcessor:
    """Handles robust parsing of CSV files."""

    def read_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Reads a CSV file and returns a list of dictionaries.
        
        Args:
            file_path: Path to the CSV file.
            
        Returns:
            List of rows as dictionaries.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is empty or malformed.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.stat().st_size == 0:
            raise ValueError(f"File is empty: {file_path}")

        try:
            with path.open(mode='r', encoding='utf-8', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                data = [row for row in reader]
                
                if not data:
                    raise ValueError("CSV file contains no data rows.")
                
                return data
        except csv.Error as e:
            raise ValueError(f"Error parsing CSV: {e}")

if __name__ == "__main__":
    # Simple demonstration
    processor = CSVProcessor()
    print("CSVProcessor initialized.")
