"""CLI entry point for NameSage — name analytics from the terminal."""

import argparse
import asyncio
import sys

from namesage.api import fetch_all
from namesage.formatter import print_profile
from namesage.llm import generate_profile


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="namesage",
        description="NameSage — AI-powered name analytics. "
        "Enter any first name and get age, gender, nationality predictions, "
        "rhyming words, and an LLM-synthesised name profile.",
    )
    parser.add_argument(
        "name",
        type=str,
        nargs="?",
        help="The first name to analyse.",
    )
    parser.add_argument(
        "--name",
        dest="name_flag",
        type=str,
        help="Alternative: pass name via --name <name>.",
    )
    args = parser.parse_args()

    name = args.name or args.name_flag
    if not name:
        parser.print_help()
        sys.exit(1)

    name = name.strip().lower()
    print(f"🔍  Analysing: {name.capitalize()}...")

    try:
        data = asyncio.run(fetch_all(name))
    except Exception as exc:
        print(f"❌ Error fetching data: {exc}", file=sys.stderr)
        sys.exit(1)

    # Generate LLM profile
    llm_profile = asyncio.run(
        generate_profile(
            name=name,
            age_data=data.get("age", {}),
            gender_data=data.get("gender", {}),
            nationality_data=data.get("nationality", {}),
            rhymes=data.get("rhymes", []),
        )
    )
    data["llm_profile"] = llm_profile

    print_profile(name, data)


if __name__ == "__main__":
    main()