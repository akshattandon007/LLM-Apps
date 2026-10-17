"""Command-line interface for pocketdiet.

Usage:
  python -m pocketdiet "greek yogurt"
  python -m pocketdiet --barcode 3017620422003
  python -m pocketdiet "almond milk" --servings 2 --json
"""

import argparse
import json
import sys
from typing import Optional

from pocketdiet.api import search_foods, lookup_barcode
from pocketdiet.nutrition import (
    generate_verdicts,
    format_verdicts,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pocketdiet",
        description="Look up nutrition info for any food product "
                    "using the Open Food Facts database.",
    )
    parser.add_argument(
        "food",
        nargs="?",
        help="Food name to search for (e.g. 'greek yogurt')",
    )
    parser.add_argument(
        "--barcode", "-b",
        help="Look up product by barcode instead of name",
    )
    parser.add_argument(
        "--servings", "-s",
        type=float,
        default=1.0,
        help="Number of servings (default: 1)",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output raw JSON instead of coloured verdicts",
    )
    parser.add_argument(
        "--top", "-t",
        type=int,
        default=1,
        help="Number of top results to show (default: 1)",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.barcode:
        _handle_barcode(args)
    elif args.food:
        _handle_search(args)
    else:
        parser.print_help()
        sys.exit(1)


def _handle_barcode(args: argparse.Namespace) -> None:
    product = lookup_barcode(args.barcode)
    if product is None:
        print(f"Product not found for barcode: {args.barcode}")
        sys.exit(1)

    if args.json:
        print(json.dumps(product, indent=2))
        return

    _print_product(product, args.servings)


def _handle_search(args: argparse.Namespace) -> None:
    products = search_foods(args.food, page_size=args.top)
    if not products:
        print(f"No products found for '{args.food}'.")
        sys.exit(1)

    if args.json:
        print(json.dumps(products, indent=2))
        return

    for i, product in enumerate(products):
        if i > 0:
            print()
        _print_product(product, args.servings)


def _print_product(product: dict, servings: float) -> None:
    name = product.get("product_name", "Unknown product")
    brand = product.get("brands", "")
    barcode = product.get("code", "")

    print(f"\033[1m{name}\033[0m")
    if brand:
        print(f"  Brand: {brand}")
    if barcode:
        print(f"  Barcode: {barcode}")
    print()

    nutriments = product.get("nutriments", {})
    verdicts = generate_verdicts(nutriments, servings)
    print(format_verdicts(verdicts))