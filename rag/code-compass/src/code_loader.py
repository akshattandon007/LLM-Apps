"""Walk a directory and collect all source code files."""

from __future__ import annotations

import os
from pathlib import Path

SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx"}

# File size limit: 1 MB
MAX_FILE_SIZE = 1 * 1024 * 1024

IGNORE_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    ".next",
    "dist",
    "build",
    ".ruff_cache",
}


def walk_directory(
    directory_path: str,
    extensions: list[str] | None = None,
) -> list[dict]:
    """Walk a directory recursively and return all matching source files.

    Returns a list of dicts with keys: path, language, content, relative_path.
    """
    base = Path(directory_path).resolve()
    if not base.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    if not base.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory_path}")

    exts = set(extensions or list(SUPPORTED_EXTENSIONS))

    files: list[dict] = []
    for root, dirs, filenames in os.walk(base):
        # Prune ignored dirs in-place
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in exts:
                continue

            full_path = os.path.join(root, fname)
            try:
                size = os.path.getsize(full_path)
            except OSError:
                continue
            if size > MAX_FILE_SIZE:
                continue
            if size == 0:
                continue

            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
            except Exception:
                continue

            relative_path = os.path.relpath(full_path, base)
            language = _ext_to_lang(ext)

            files.append(
                {
                    "path": str(full_path),
                    "relative_path": relative_path,
                    "language": language,
                    "content": content,
                }
            )

    return files


def _ext_to_lang(ext: str) -> str:
    return {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
    }.get(ext, "unknown")
