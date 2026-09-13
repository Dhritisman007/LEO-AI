from pathlib import Path

FILES = {
    "sample.txt": "Hello World",
    "script.py": "print('Hello')",
    "data.json": "{\"key\": \"value\"}",
    "table.csv": "id,name\n1,test",
    "readme.md": "# Title"
}

def create_sample_files() -> None:
    """Creates 5 sample files in the current directory."""
    for name, content in FILES.items():
        Path(name).write_text(content)
        print(f"Created {name}")

if __name__ == '__main__':
    create_sample_files()