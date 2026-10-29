#!/usr/bin/env python3
"""
Ingenius — Smart Ingredient Substitutions.

A CLI tool that takes a missing ingredient (and optional recipe context)
and returns 3 viable substitutes with exact replacement ratios and
a brief chemistry note explaining why they work.

Usage:
    python ingenius.py "buttermilk"
    python ingenius.py "fish sauce" --recipe "pad thai"
    python ingenius.py "sourdough starter" --mood quick
"""

import argparse
import json
import os
import sys

try:
    import requests
except ImportError:
    print("Error: 'requests' is required. Install with: pip install requests")
    sys.exit(1)


DEFAULT_MODEL = "google/gemini-2.0-flash-001"  # works on OpenRouter free tier
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
SITE_URL = os.environ.get("SITE_URL", "https://github.com/akshattandon007/LLM-Apps")
SITE_NAME = "Ingenius"


def build_prompt(ingredient: str, recipe: str | None, mood: str | None) -> str:
    """Build a structured substitution prompt for the LLM."""

    system = (
        "You are a professional chef and food scientist. "
        "Given a missing ingredient, suggest exactly 3 substitutes ranked by how well "
        "they work in the intended context. For each substitute provide:\n"
        "1. The substitute ingredient name\n"
        "2. The exact replacement ratio (e.g. '1 cup replaces 1 cup' or '1 tbsp replaces 2 tsp')\n"
        "3. A one-sentence chemistry note explaining why the substitute works "
        "(e.g. 'Yogurt has the same lactic acid profile as buttermilk for tenderising')\n"
        "4. A one-sentence usage tip (e.g. 'Add 1/4 tsp baking soda to mimic buttermilk's lift')\n"
        "Format: return ONLY valid JSON with this exact structure, no other text:\n"
        '{"substitutes": [{"name": "...", "ratio": "...", "chemistry": "...", "tip": "..."}, ...]}'
    )

    user = f"I'm cooking a recipe that calls for '{ingredient}' but I don't have it."
    if recipe:
        user += f"\nThe recipe is: {recipe}"
    if mood == "quick":
        user += "\nI want the fastest option — minimal extra ingredients or prep."
    elif mood == "pantry":
        user += "\nI can only use common pantry staples (no specialty items)."
    elif mood == "gourmet":
        user += "\nI'm open to specialty ingredients for the best flavour match."

    user += "\n\nReturn ONLY valid JSON matching the schema above — no other text."

    return system, user


def call_llm(system: str, user: str) -> dict:
    """Call OpenRouter API and return parsed JSON."""
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY environment variable not set.", file=sys.stderr)
        print("Get a free key at https://openrouter.ai/keys", file=sys.stderr)
        sys.exit(1)

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": SITE_URL,
            "X-Title": SITE_NAME,
        },
        json={
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.3,
            "max_tokens": 1024,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()

    # Strip markdown code fence if present
    if content.startswith("```"):
        lines = content.splitlines()
        content = "\n".join(
            line for line in lines if not line.startswith("```")
        ).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print("Error: LLM returned malformed JSON.", file=sys.stderr)
        print(f"Raw response:\n{content}", file=sys.stderr)
        sys.exit(1)


def format_output(result: dict, ingredient: str) -> str:
    """Pretty-print the substitution results."""
    subs = result.get("substitutes", [])
    if not subs:
        return "No substitutes suggested. Try a different ingredient."

    lines = [f"🧪 Ingenius — Substitutes for '{ingredient}'\n"]
    for i, sub in enumerate(subs, 1):
        lines.append(f"  {i}. {sub.get('name', '?')}")
        lines.append(f"     Ratio:    {sub.get('ratio', '?')}")
        lines.append(f"     Why:      {sub.get('chemistry', '?')}")
        lines.append(f"     Tip:      {sub.get('tip', '?')}")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Ingenius — Smart Ingredient Substitutions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python ingenius.py buttermilk\n"
            "  python ingenius.py 'fish sauce' --recipe 'pad thai'\n"
            "  python ingenius.py 'sourdough starter' --mood quick\n"
            "\nSet OPENROUTER_API_KEY in your environment to use."
        ),
    )
    parser.add_argument("ingredient", help="The missing ingredient (e.g. 'buttermilk')")
    parser.add_argument("--recipe", "-r", help="Optional recipe context for better suggestions")
    parser.add_argument(
        "--mood", "-m",
        choices=["quick", "pantry", "gourmet"],
        help="Substitution style: quick (fastest), pantry (staples only), gourmet (best flavour)"
    )
    args = parser.parse_args()

    system, user = build_prompt(args.ingredient, args.recipe, args.mood)
    result = call_llm(system, user)
    print(format_output(result, args.ingredient))


if __name__ == "__main__":
    main()