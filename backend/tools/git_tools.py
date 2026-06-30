import subprocess
import os
from github import Github
from dotenv import load_dotenv

load_dotenv()

GIT_WORKSPACE = os.getenv("GIT_WORKSPACE")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_REPO = os.getenv("GITHUB_REPO")


def _run_git(args: list, cwd: str = None) -> dict:
    """Run a git command in the workspace repo."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd or GIT_WORKSPACE,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def git_create_branch(branch_name: str) -> dict:
    """Create and switch to a new branch."""
    if not GIT_WORKSPACE or not os.path.exists(GIT_WORKSPACE):
        return {"success": False, "error": "GIT_WORKSPACE not configured or path doesn't exist"}

    # Make sure we're up to date first
    _run_git(["checkout", "main"])
    _run_git(["pull", "origin", "main"])

    result = _run_git(["checkout", "-b", branch_name])
    if not result["success"] and "already exists" in result.get("stderr", ""):
        # Branch exists, just switch to it
        result = _run_git(["checkout", branch_name])
    return result


def git_commit_changes(filename: str, content: str, commit_message: str) -> dict:
    """Write a file into the git workspace, stage it, and commit."""
    if not GIT_WORKSPACE or not os.path.exists(GIT_WORKSPACE):
        return {"success": False, "error": "GIT_WORKSPACE not configured or path doesn't exist"}

    try:
        filepath = os.path.join(GIT_WORKSPACE, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            f.write(content)
    except Exception as e:
        return {"success": False, "error": f"Failed to write file: {str(e)}"}

    add_result = _run_git(["add", filename])
    if not add_result["success"]:
        return add_result

    commit_result = _run_git(["commit", "-m", commit_message])
    return commit_result


def git_push_branch(branch_name: str) -> dict:
    """Push the current branch to origin."""
    if not GITHUB_TOKEN:
        return {"success": False, "error": "GITHUB_TOKEN not configured"}

    # Use token-authenticated URL for push
    push_url = f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{GITHUB_REPO}.git"
    result = _run_git(["push", push_url, branch_name])
    return result


def git_open_pull_request(branch_name: str, title: str, description: str) -> dict:
    """Open a PR from branch_name into main using the GitHub API."""
    try:
        if not GITHUB_TOKEN:
            return {"success": False, "error": "GITHUB_TOKEN not configured"}

        gh = Github(GITHUB_TOKEN)
        repo = gh.get_repo(f"{GITHUB_USERNAME}/{GITHUB_REPO}")

        pr = repo.create_pull(
            title=title,
            body=description,
            head=branch_name,
            base="main"
        )

        return {
            "success": True,
            "pr_url": pr.html_url,
            "pr_number": pr.number
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def git_status() -> dict:
    """Check current git status of the workspace."""
    if not GIT_WORKSPACE or not os.path.exists(GIT_WORKSPACE):
        return {"success": False, "error": "GIT_WORKSPACE not configured or path doesn't exist"}
    return _run_git(["status", "--short"])
