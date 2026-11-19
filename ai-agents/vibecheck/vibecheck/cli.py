"""
VibeCheck — Command-line interface.

Provides interactive and single-shot modes for analyzing text tone.
"""

import argparse
import sys
import os

from . import __version__
from .analyzer import analyze_text, compare_texts, setup_config


def _print_separator(char="─", width=60):
    print(char * width)


def _print_analysis(result, label="Analysis"):
    """Pretty-print a ToneAnalysis result."""
    print(f"\n  {label}")
    _print_separator()
    print(f"  Overall Tone:    {result.overall_tone}")
    print(f"  Clarity Score:   {result.clarity_score}/10")
    print(f"  Confidence:      {result.confidence_level}")
    print(f"  Formality:       {result.formality}")
    print(f"  Detected Mood:   {result.detected_mood}")

    if result.emotional_subtext:
        print(f"\n  🎭 Emotional Subtext:")
        for s in result.emotional_subtext:
            print(f"     • {s}")

    if result.key_strengths:
        print(f"\n  ✅ Key Strengths:")
        for s in result.key_strengths:
            print(f"     • {s}")

    if result.potential_misinterpretations:
        print(f"\n  ⚠️  Potential Misinterpretations:")
        for m in result.potential_misinterpretations:
            print(f"     • {m}")

    if result.rewrite_suggestions:
        print(f"\n  💡 Rewrite Suggestions:")
        for s in result.rewrite_suggestions:
            print(f"     • {s}")

    print()


def _print_comparison(result):
    """Pretty-print a ComparisonResult."""
    print("\n  📊 Comparison")
    _print_separator()

    print(f"\n  Original Tone:  {result.original.overall_tone}")
    print(f"  Rewritten Tone: {result.rewritten.overall_tone}")

    if result.differences:
        print(f"\n  🔄 Key Differences:")
        for d in result.differences:
            print(f"     • {d}")

    if result.improvement_areas:
        print(f"\n  📈 Improvement Areas:")
        for a in result.improvement_areas:
            print(f"     • {a}")

    print()
    _print_separator()
    print("  Original Analysis:")
    _print_analysis(result.original, label="")
    _print_separator()
    print("  Rewritten Analysis:")
    _print_analysis(result.rewritten, label="")


def _interactive_mode(args):
    """Run interactive analysis session."""
    print(f"\n  ╔══════════════════════════════════════╗")
    print(f"  ║      VibeCheck — Tone Analyzer v{__version__}     ║")
    print(f"  ╚══════════════════════════════════════╝")
    print(f"  Paste text to analyze. Type 'quit' to exit.")
    print(f"  Commands: /compare <text> to compare, /file <path>\n")

    while True:
        try:
            user_input = input("  vibecheck> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            break

        if user_input.startswith("/file "):
            filepath = user_input[6:].strip()
            if not os.path.exists(filepath):
                print(f"  ✗ File not found: {filepath}")
                continue
            with open(filepath) as f:
                text = f.read()
            print(f"  ✓ Read {len(text)} chars from {filepath}")
            result = analyze_text(text)
            _print_analysis(result)
            continue

        if user_input.startswith("/compare "):
            rest = user_input[9:].strip()
            parts = rest.split("|||")
            if len(parts) < 2:
                print("  ✗ Usage: /compare <original> ||| <rewritten>")
                continue
            original = parts[0].strip()
            rewritten = parts[1].strip()
            result = compare_texts(original, rewritten)
            _print_comparison(result)
            continue

        # Default: analyze single text
        result = analyze_text(user_input)
        _print_analysis(result)


def _single_shot_mode(args):
    """Analyze text from a single argument, stdin, or file."""
    text = ""

    if args.text:
        text = args.text
    elif args.file:
        filepath = os.path.expanduser(args.file)
        if not os.path.exists(filepath):
            print(f"✗ File not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        with open(filepath) as f:
            text = f.read()
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()

    if not text:
        print("✗ No text provided. Use --text, --file, or pipe input.", file=sys.stderr)
        sys.exit(1)

    if args.compare:
        parts = text.split("|||")
        if len(parts) < 2:
            print("✗ For comparison, separate original and rewritten with '|||'", file=sys.stderr)
            sys.exit(1)
        result = compare_texts(parts[0].strip(), parts[1].strip())
        _print_comparison(result)
    else:
        result = analyze_text(text)
        _print_analysis(result)


def main():
    parser = argparse.ArgumentParser(
        prog="vibecheck",
        description="Analyze any text for tone, subtext, and communication style.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--text", "-t", help="Text to analyze (inline)")
    parser.add_argument("--file", "-f", help="Path to a file containing text")
    parser.add_argument("--compare", "-c", action="store_true",
                        help="Compare original vs rewritten (separate with |||)")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Start interactive mode")
    parser.add_argument("--setup", help="Save OpenRouter API key for future use")

    args = parser.parse_args()

    if args.setup:
        path = setup_config(args.setup)
        print(f"✓ API key saved to {path}")
        return

    if args.interactive or not (args.text or args.file or not sys.stdin.isatty() or args.compare):
        _interactive_mode(args)
    else:
        _single_shot_mode(args)


if __name__ == "__main__":
    main()