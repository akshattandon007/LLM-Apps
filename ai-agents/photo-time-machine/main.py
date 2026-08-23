#!/usr/bin/env python3
"""Photo Time Machine — See yourself through every decade.

Usage
-----
    python main.py --simulate        # Run with a mock photo (MVP mode)
    python main.py --upload selfie.jpg --simulate
    python main.py --upload selfie.jpg   # (future: real image gen)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the project root is on sys.path for direct `python main.py` usage.
_PROJECT_ROOT = Path(__file__).parent.resolve()
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.transformer import transform_photo
from src.gallery import build_gallery, build_photo_time_machine_output


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Photo Time Machine — see yourself through every decade.",
    )
    parser.add_argument(
        "--upload",
        type=str,
        default=None,
        help="Path to a photo file (JPEG/PNG).",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        default=False,
        help="Simulate era transformations with text descriptions (MVP mode).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    # Determine the photo path
    if args.upload:
        photo_path = args.upload
        p = Path(photo_path)
        if not p.exists():
            print(f"Error: file not found — {photo_path}", file=sys.stderr)
            sys.exit(1)
    else:
        # Use a synthetic mock photo path when no real file is given
        photo_path = "selfie.jpg  (mock)"

    # Transform
    print("⏳ Transforming your photo through time...\n")
    transformations = transform_photo(photo_path, simulate=args.simulate)
    output = build_photo_time_machine_output(photo_path, transformations)
    gallery = build_gallery(output)
    print(gallery)


if __name__ == "__main__":
    main()