from .file_tools import read_file, write_file, list_files, get_file_tree, get_file_content
from .shell_tools import run_python, run_shell, run_code
from .search_tools import web_search
from .git_tools import (
    git_create_branch, git_commit_changes, git_push_branch,
    git_open_pull_request, git_status
)

TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    "run_python": run_python,
    "run_shell": run_shell,
    "web_search": web_search,
    "git_create_branch": git_create_branch,
    "git_commit_changes": git_commit_changes,
    "git_push_branch": git_push_branch,
    "git_open_pull_request": git_open_pull_request,
    "git_status": git_status,
    "run_code": run_code,
}

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
    {
        "name": "git_create_branch",
        "description": "Create and switch to a new git branch in the project repo",
        "parameters": {"branch_name": "string — e.g. 'leo/add-feature'"},
    },
    {
        "name": "git_commit_changes",
        "description": "Write a file to the git repo, stage it, and commit it",
        "parameters": {
            "filename": "string — path relative to repo root",
            "content": "string — file content",
            "commit_message": "string — clear, concise commit message"
        },
    },
    {
        "name": "git_push_branch",
        "description": "Push the current branch to GitHub",
        "parameters": {"branch_name": "string — branch to push"},
    },
    {
        "name": "git_open_pull_request",
        "description": "Open a pull request on GitHub from a branch into main",
        "parameters": {
            "branch_name": "string — source branch",
            "title": "string — PR title",
            "description": "string — PR body explaining the change"
        },
    },
    {
        "name": "git_status",
        "description": "Check the current git status of the project repo",
        "parameters": {},
    },
    {
        "name": "run_code",
        "description": "Execute code in any supported language: python, javascript, java, cpp, c, go, rust, bash",
        "parameters": {
            "code": "string — the code to run",
            "language": "string — python | javascript | java | cpp | c | go | rust | bash",
            "filename": "string (optional) — filename to use, required for Java to match class name"
        },
    },
]
