"""File type categories and configuration for FolderMate."""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List

# Default categories with file extension mappings
CATEGORY_EXTENSIONS: Dict[str, List[str]] = {
    "Documents": [
        ".pdf", ".doc", ".docx", ".odt", ".rtf", ".tex", ".wpd",
        ".txt", ".md", ".rst", ".log",
        ".csv", ".xls", ".xlsx", ".ods",
        ".ppt", ".pptx", ".odp", ".key", ".pps",
    ],
    "Images": [
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp",
        ".tiff", ".tif", ".ico", ".heic", ".heif", ".raw", ".cr2",
        ".nef", ".orf", ".arw", ".psd", ".ai", ".eps",
    ],
    "Audio": [
        ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma",
        ".opus", ".aiff", ".alac", ".mid", ".midi",
    ],
    "Video": [
        ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".webm", ".flv",
        ".m4v", ".mpg", ".mpeg", ".3gp", ".ogv", ".ts",
    ],
    "Archives": [
        ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar", ".xz",
        ".zst", ".tgz", ".tbz2", ".tar.gz", ".tar.bz2",
    ],
    "Code": [
        ".py", ".js", ".ts", ".html", ".css", ".scss", ".less",
        ".json", ".yaml", ".yml", ".xml", ".toml", ".ini", ".cfg",
        ".sh", ".bash", ".zsh", ".bat", ".cmd", ".ps1",
        ".sql", ".rb", ".go", ".rs", ".java", ".c", ".cpp", ".h",
        ".swift", ".kt", ".scala", ".lua", ".r", ".m",
        ".env", ".dockerfile", ".makefile", ".gradle",
    ],
    "Installers": [
        ".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm",
        ".AppImage", ".apk", ".run", ".bin",
    ],
    "Fonts": [
        ".ttf", ".otf", ".woff", ".woff2", ".eot",
    ],
    "Torrents": [
        ".torrent", ".magnet",
    ],
}


@dataclass
class FolderMateConfig:
    """Configuration for a FolderMate run."""

    source_dir: Path = Path(".")
    mode: str = "dry-run"  # "dry-run" or "execute"
    strategy: str = "by-type"  # "by-type", "by-date", or "both"
    include_hidden: bool = False
    recursive: bool = True
    verbose: bool = False
    undo_log: Path = field(default_factory=lambda: Path.home() / ".foldermate" / "undo.log")
    date_format: str = "%Y-%m"  # used for by-date subfolders

    # Directories to skip
    skip_dirs: List[str] = field(default_factory=lambda: [
        "Documents", "Images", "Audio", "Video", "Archives",
        "Code", "Installers", "Fonts", "Torrents", "Others",
    ])


# Default extensions list for quick lookup
ALL_EXTENSIONS: List[str] = []
for exts in CATEGORY_EXTENSIONS.values():
    ALL_EXTENSIONS.extend(exts)
ALL_EXTENSIONS = sorted(set(ALL_EXTENSIONS))