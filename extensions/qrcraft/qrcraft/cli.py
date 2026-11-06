"""qrcraft CLI — command-line entry point."""

import argparse
import sys
from pathlib import Path

from qrcraft import __version__
from qrcraft.encode import encode, encode_many
from qrcraft.decode import decode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qrcraft",
        description="QR code toolkit — generate and decode QR codes.",
        epilog="Examples:\n"
               "  qrcraft encode 'https://example.com' -o qr.png\n"
               "  qrcraft e 'hello world' --ascii\n"
               "  qrcraft decode qr.png\n"
               "  qrcraft d screenshot.png --json\n"
               "  echo 'https://example.com' | qrcraft encode -o pipe.png",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"qrcraft v{__version__}")

    sub = parser.add_subparsers(dest="command", required=True)

    # ── encode ──────────────────────────────────────────────────────────
    enc = sub.add_parser("encode", aliases=["e"],
                         help="Generate a QR code from text or URL")
    enc.add_argument("data", nargs="?", default=None,
                     help="Text or URL to encode (reads stdin if omitted)")
    enc.add_argument("-o", "--output", default=None,
                     help="Output image path (e.g. qr.png, qr.svg)")
    enc.add_argument("--ascii", action="store_true",
                     help="Render as ASCII art in terminal instead of image")
    enc.add_argument("--box-size", type=int, default=10, dest="box_size",
                     help="QR module size in pixels (default 10)")
    enc.add_argument("--border", type=int, default=4,
                     help="Quiet-zone border width (default 4)")
    enc.add_argument("--error", choices=["L", "M", "Q", "H"], default="M",
                     help="Error correction level (default M)")
    enc.add_argument("--fill", default="#000000",
                     help="Foreground colour (hex, default #000000)")
    enc.add_argument("--back", default="#FFFFFF",
                     help="Background colour (hex, default #FFFFFF)")
    enc.add_argument("--batch", nargs="*", default=None,
                     help="Multiple items to encode (batch mode)")
    enc.add_argument("--output-dir", default=".",
                     help="Directory for batch mode (default current dir)")

    # ── decode ──────────────────────────────────────────────────────────
    dec = sub.add_parser("decode", aliases=["d"],
                         help="Read a QR code from an image file or URL")
    dec.add_argument("image", help="Path to image containing a QR code (PNG, JPG, etc.)")
    dec.add_argument("--json", action="store_true",
                     help="Output as JSON for scripting")
    dec.add_argument("--timeout", type=int, default=15,
                     help="Timeout in seconds for online decode (default 15)")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in ("encode", "e"):
        return _handle_encode(args)
    elif args.command in ("decode", "d"):
        return _handle_decode(args)
    return 1


def _handle_encode(args) -> int:
    data = args.data

    # Read from stdin if no positional data given
    if data is None and not sys.stdin.isatty():
        data = sys.stdin.read().strip()

    if not data:
        print("error: no input data provided (use positional arg or pipe to stdin)",
              file=sys.stderr)
        return 1

    # Batch mode
    if args.batch is not None:
        items = [data] + list(args.batch)
        paths = encode_many(items, output_dir=args.output_dir,
                            box_size=args.box_size, border=args.border,
                            error_correction=args.error,
                            fill_color=args.fill, back_color=args.back)
        print(f"Generated {len(paths)} QR codes:")
        for p in paths:
            print(f"  {p}")
        return 0

    # Single mode
    result = encode(
        data,
        output=args.output,
        box_size=args.box_size,
        border=args.border,
        error_correction=args.error,
        ascii=args.ascii,
        fill_color=args.fill,
        back_color=args.back,
    )
    if result == "(stdout)":
        if not args.ascii:
            print("  (PNG data written to stdout)", file=sys.stderr)
    else:
        print(f"QR code saved → {result}")
    return 0


def _handle_decode(args) -> int:
    try:
        results = decode(args.image, timeout=args.timeout)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if not results:
        print("No QR code found in the image.", file=sys.stderr)
        return 1

    if args.json:
        import json as j
        print(j.dumps(results, indent=2))
    else:
        for item in results:
            print(item["data"])
    return 0


if __name__ == "__main__":
    sys.exit(main())