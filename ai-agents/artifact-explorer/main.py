#!/usr/bin/env python3
"""Artifact Explorer — CLI entry point.

Usage:
    python main.py --describe "aloe vera plant"
    python main.py --snap photo.jpg
    python main.py --simulate
    python main.py --list
"""

import argparse
import sys

from dotenv import load_dotenv

from src.identifier import identify_from_text, identify_from_image, ARTIFACT_LIBRARY
from src.historian import generate_story
from src.gallery import print_card

load_dotenv()


def cmd_simulate() -> None:
    """Run through all artifacts in the library for demonstration."""
    for key, data in ARTIFACT_LIBRARY.items():
        from src.models import IdentificationResult

        ident = IdentificationResult(
            name=data["name"],
            category=data["category"],
            description=data["description"],
        )
        artifact = generate_story(ident)
        print_card(artifact)
        print("\n" + "=" * 78 + "\n")


def cmd_describe(query: str) -> None:
    """Identify and enrich from a text description."""
    ident = identify_from_text(query)
    if ident is None:
        print(f"❌  Could not identify '{query}'.")
        print("    Try --list to see supported artifacts, or be more specific.")
        sys.exit(1)
    artifact = generate_story(ident)
    print_card(artifact)


def cmd_snap(path: str) -> None:
    """Identify and enrich from an image file."""
    ident = identify_from_image(path)
    if ident is None:
        print(f"❌  Could not read or identify '{path}'.")
        print("    Ensure the file exists and is a supported image format.")
        sys.exit(1)
    artifact = generate_story(ident)
    print_card(artifact)


def cmd_list() -> None:
    """List all artifacts in the library."""
    print("\n📚  ARTIFACT EXPLORER — Library\n")
    for i, (key, data) in enumerate(ARTIFACT_LIBRARY.items(), 1):
        print(f"  {i:2d}. {data['name']:40s}  [{data['category']}]")
    print(f"\n  Total: {len(ARTIFACT_LIBRARY)} artifacts loaded.\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Artifact Explorer — identify objects and discover their story.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--describe",
        type=str,
        metavar="QUERY",
        help="Identify an object from a text description",
    )
    mode.add_argument(
        "--snap",
        type=str,
        metavar="IMAGE_PATH",
        help="Identify an object from an image file",
    )
    mode.add_argument(
        "--simulate",
        action="store_true",
        help="Run the full pipeline for every artifact in the library",
    )
    mode.add_argument(
        "--list",
        action="store_true",
        help="List all supported artifacts",
    )
    args = parser.parse_args()

    if args.describe:
        cmd_describe(args.describe)
    elif args.snap:
        cmd_snap(args.snap)
    elif args.simulate:
        cmd_simulate()
    elif args.list:
        cmd_list()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()