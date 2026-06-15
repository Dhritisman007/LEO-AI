from .file_tools import read_file, write_file, list_files
from .shell_tools import run_python, run_shell
from .search_tools import web_search

# Tool registry — maps tool name to function
TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    "run_python": run_python,
    "run_shell": run_shell,
    "web_search": web_search,
}

# Tool descriptions for the LLM
TOOL_DESCRIPTIONS = [
    {
        "name": "read_file",
        "description": "Read a file from the workspace",
        "parameters": {"filename": "string — name of the file to read"},
    },
    {
        "name": "write_file",
        "description": "Write content to a file in the workspace",
        "parameters": {
            "filename": "string — name of the file",
            "content": "string — content to write",
        },
    },
    {
        "name": "list_files",
        "description": "List all files in the workspace",
        "parameters": {},
    },
    {
        "name": "run_python",
        "description": "Execute Python code in an isolated Docker sandbox",
        "parameters": {"code": "string — Python code to run"},
    },
    {
        "name": "run_shell",
        "description": "Run a shell command in an isolated Docker sandbox",
        "parameters": {"command": "string — shell command to run"},
    },
    {
        "name": "web_search",
        "description": "Search the web for information",
        "parameters": {"query": "string — search query"},
    },
]
