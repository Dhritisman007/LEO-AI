import os
import json
import re
from typing import Optional

WORKSPACE_BASE = "/tmp/leo_workspace"

# File types LEO should read and understand
READABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".java", ".cpp", ".c", ".go", ".rs",
    ".json", ".yaml", ".yml", ".toml",
    ".md", ".txt", ".env.example",
    ".html", ".css"
}

# Files to always skip
SKIP_PATTERNS = {
    "node_modules", "__pycache__", ".git",
    "venv", ".next", "dist", "build",
    ".pyc", ".pyo", ".class"
}

MAX_FILE_SIZE = 50_000   # 50KB per file
MAX_TOTAL_SIZE = 200_000 # 200KB total context


def should_skip(path: str) -> bool:
    for pattern in SKIP_PATTERNS:
        if pattern in path:
            return True
    return False


def get_file_summary(filepath: str, content: str, language: str) -> str:
    """Extract key info from a file without sending the whole thing."""
    lines = content.split("\n")
    summary_lines = []

    if language == "python":
        for line in lines:
            stripped = line.strip()
            # Capture imports, class defs, function defs, top-level vars
            if (stripped.startswith("import ") or
                stripped.startswith("from ") or
                stripped.startswith("class ") or
                stripped.startswith("def ") or
                re.match(r'^[A-Z_]+\s*=', stripped)):
                summary_lines.append(line)

    elif language in ("javascript", "typescript"):
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith("import ") or
                stripped.startswith("export ") or
                stripped.startswith("const ") or
                stripped.startswith("function ") or
                stripped.startswith("class ") or
                stripped.startswith("interface ") or
                stripped.startswith("type ")):
                summary_lines.append(line)

    elif language == "java":
        for line in lines:
            stripped = line.strip()
            if ("class " in stripped or
                "interface " in stripped or
                "public " in stripped or
                "private " in stripped or
                "import " in stripped):
                summary_lines.append(line)

    # For small files just return full content
    if len(content) < 2000:
        return content

    return "\n".join(summary_lines[:50]) if summary_lines else content[:1000]


def get_language(filename: str) -> str:
    ext_map = {
        ".py": "python", ".js": "javascript",
        ".ts": "typescript", ".tsx": "typescript",
        ".jsx": "javascript", ".java": "java",
        ".cpp": "cpp", ".c": "c",
        ".go": "go", ".rs": "rust",
        ".json": "json", ".md": "markdown",
        ".yaml": "yaml", ".yml": "yaml",
    }
    ext = os.path.splitext(filename)[1].lower()
    return ext_map.get(ext, "text")


def build_context(user_id: str = "anonymous", full: bool = False) -> dict:
    """
    Scan the workspace and build a rich context object.
    full=True returns full file contents (for small workspaces)
    full=False returns summaries (for large workspaces)
    """
    workspace = os.path.join(WORKSPACE_BASE, user_id)
    if not os.path.exists(workspace):
        return {"files": [], "summary": "Empty workspace — no files yet.", "total_size": 0}

    files = []
    total_size = 0
    skipped = []

    for root, dirs, filenames in os.walk(workspace):
        # Skip hidden and build dirs in-place
        dirs[:] = [d for d in dirs if not should_skip(d)]

        for fname in sorted(filenames):
            filepath = os.path.join(root, fname)
            rel_path = os.path.relpath(filepath, workspace)

            if should_skip(rel_path):
                continue

            ext = os.path.splitext(fname)[1].lower()
            if ext not in READABLE_EXTENSIONS:
                skipped.append(rel_path)
                continue

            try:
                size = os.path.getsize(filepath)
                if size > MAX_FILE_SIZE:
                    skipped.append(f"{rel_path} (too large: {size//1000}KB)")
                    continue

                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                language = get_language(fname)
                summary = content if (full or len(content) < 500) else get_file_summary(filepath, content, language)

                files.append({
                    "path": rel_path,
                    "language": language,
                    "size": size,
                    "lines": len(content.split("\n")),
                    "content": content if full else None,
                    "summary": summary,
                })
                total_size += len(summary)

                if total_size > MAX_TOTAL_SIZE:
                    break

            except Exception:
                continue

    # Build a high-level summary string for the prompt
    if not files:
        summary_str = "Workspace is empty — no readable files found."
    else:
        file_list = "\n".join(
            f"  - {f['path']} ({f['language']}, {f['lines']} lines)"
            for f in files
        )
        summary_str = f"Workspace contains {len(files)} file(s):\n{file_list}"
        if skipped:
            summary_str += f"\n  (skipped {len(skipped)} binary/large files)"

    return {
        "files": files,
        "summary": summary_str,
        "total_size": total_size,
        "file_count": len(files),
    }


def format_context_for_prompt(user_id: str = "anonymous") -> str:
    """
    Returns a formatted string to inject into the agent prompt
    giving LEO awareness of the current workspace state.
    """
    ctx = build_context(user_id)

    if not ctx["files"]:
        return "WORKSPACE: Empty — no files exist yet."

    parts = [f"WORKSPACE CONTEXT ({ctx['file_count']} files):"]
    parts.append(ctx["summary"])
    parts.append("\nKEY FILE CONTENTS / SIGNATURES:")

    for f in ctx["files"]:
        parts.append(f"\n### {f['path']} ({f['language']})")
        parts.append(f["summary"] or "(empty)")

    return "\n".join(parts)
