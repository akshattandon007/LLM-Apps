#!/usr/bin/env python3
"""sugarcoat - AI-powered message rephraser for difficult conversations."""

import os
import sys
import json
import argparse
from pathlib import Path

from sugarcoat_engine import rephrase_message, get_supported_tones, get_supported_styles


def load_api_key() -> str:
    """Load the OpenRouter API key from env or .env file."""
    # Check environment first
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if key:
        return key

    # Check .env files
    for dotenv in [Path(".env"), Path.home() / ".env", Path("/data/profiles/chief/.env")]:
        if dotenv.exists():
            with open(dotenv) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("OPENROUTER_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
                    if line.startswith("OPENAI_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sugarcoat",
        description="Rephrase difficult messages with kindness and clarity.",
        epilog="Example: sugarcoat \"I can't make it to your party\" --style apologetic"
    )

    parser.add_argument(
        "message",
        nargs="?",
        help="The difficult message you want to rephrase"
    )

    parser.add_argument(
        "-t", "--tone",
        default="gentle",
        choices=get_supported_tones(),
        help="Desired tone for the rephrased message (default: gentle)"
    )

    parser.add_argument(
        "-s", "--style",
        default="diplomatic",
        choices=get_supported_styles(),
        help="Communication style (default: diplomatic)"
    )

    parser.add_argument(
        "--context",
        default="",
        help="Optional context about the situation (e.g. 'This is my boss', 'Friend of 10 years')"
    )

    parser.add_argument(
        "--api-key",
        default="",
        help="OpenRouter API key (overrides .env and env vars)"
    )

    parser.add_argument(
        "--model",
        default="deepseek/deepseek-chat",
        help="OpenRouter model to use (default: deepseek/deepseek-chat)"
    )

    parser.add_argument(
        "--list-tones",
        action="store_true",
        help="List available tones and exit"
    )

    parser.add_argument(
        "--list-styles",
        action="store_true",
        help="List available styles and exit"
    )

    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Interactive mode — input message via prompt"
    )

    parser.add_argument(
        "--history",
        default="",
        help="JSON file path with previous messages for context"
    )

    args = parser.parse_args()

    # List flags
    if args.list_tones:
        print("Available tones:")
        for t in get_supported_tones():
            print(f"  • {t}")
        sys.exit(0)

    if args.list_styles:
        print("Available styles:")
        for s in get_supported_styles():
            print(f"  • {s}")
        sys.exit(0)

    # Get message
    message = args.message
    if args.interactive or not message:
        if not message:
            print("📝 Enter the difficult message (Ctrl+D to finish):")
            try:
                message = sys.stdin.read().strip()
            except KeyboardInterrupt:
                print("\nCancelled.")
                sys.exit(1)
            if not message:
                print("No message provided. Run with --help for usage.")
                sys.exit(1)

    # Load API key
    api_key = args.api_key or load_api_key()
    if not api_key:
        print(
            "❌ No API key found. Set OPENROUTER_API_KEY in your .env or pass --api-key.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Load history if provided
    history = []
    if args.history:
        try:
            with open(args.history) as f:
                history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"⚠️  Could not load history file: {e}", file=sys.stderr)

    # Run the rephrasing
    print(f"🔮 Rephrasing with {args.tone} tone, {args.style} style...\n")
    try:
        result = rephrase_message(
            message=message,
            tone=args.tone,
            style=args.style,
            context=args.context,
            api_key=api_key,
            model=args.model,
            history=history,
        )

        print("=" * 60)
        print(result["rephrased"])
        print("=" * 60)

        if result.get("explanation"):
            print(f"\n💡 Why this works: {result['explanation']}")

        if result.get("alternatives"):
            print("\n🔄 Alternatives:")
            for i, alt in enumerate(result["alternatives"], 1):
                print(f"  {i}. {alt}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()