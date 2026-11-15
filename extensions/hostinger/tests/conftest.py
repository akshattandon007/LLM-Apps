"""pytest configuration — ensures the project root is on sys.path."""

import sys
from pathlib import Path

_proj_root = str(Path(__file__).resolve().parent.parent.parent)  # /data/LLM-Apps/extensions
if _proj_root not in sys.path:
    sys.path.insert(0, _proj_root)
