"""Command-line interface for Schoolsift.

Usage:
    python3 -m schoolsift index <folder> [--store PATH]
    python3 -m schoolsift ask  "when is the science fair?" [--store PATH]
    python3 -m schoolsift dates "when is the science fair?" [--store PATH]
    python3 -m schoolsift list [--store PATH]
    python3 -m schoolsift clear [--store PATH]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from . import ingest
from . import index as index_mod
from . import search
from . import answer
from . import dates as dates_mod

DEFAULT_STORE = Path.home() / ".schoolsift" / "index.json"


def _store_path(args) -> Path:
    return Path(args.store or os.environ.get("SCHOOLSIFT_STORE") or DEFAULT_STORE)


def _load_store(args):
    path = _store_path(args)
    if not path.exists():
        sys.stderr.write(
            f"No index found at {path}.\n"
            "Run first: python3 -m schoolsift index <folder>\n"
        )
        raise SystemExit(1)
    return index_mod.Store.load(path)


def cmd_index(args) -> None:
    folder = Path(args.folder)
    if not folder.is_dir():
        sys.stderr.write(f"Not a folder: {folder}\n")
        raise SystemExit(1)
    docs = ingest.ingest_folder(folder)
    chunks = [c for doc in docs for c in doc["chunks"]]
    store = index_mod.build(docs)
    path = _store_path(args)
    store.save(path)
    print(f"Indexed {len(docs)} document(s) → {len(chunks)} chunk(s) into {path}")


def cmd_ask(args) -> None:
    store = _load_store(args)
    hits = search.search(store, args.question, k=args.top)
    print(answer.build_answer(store, args.question, hits))


def cmd_dates(args) -> None:
    store = _load_store(args)
    hits = search.search(store, args.question, k=args.top)
    if not hits:
        print("No matching passages found.")
        return
    text = " ".join(h["chunk"]["text"] for h in hits)
    all_dates = dates_mod.extract_dates(text)
    if not all_dates:
        print("No dates found in the matching passages.")
        return
    print(f"Dates found in the {len(hits)} most relevant passages:")
    seen: set[str] = set()
    for d in all_dates:
        if d.iso in seen:
            continue
        seen.add(d.iso)
        tag = " (deadline)" if d.kind == "deadline" else ""
        print(f"- {d.iso}{tag} — {d.context[:140]}")


def cmd_list(args) -> None:
    store = _load_store(args)
    if not store.docs:
        print("Nothing indexed yet.")
        return
    print(
        f"{len(store.docs)} document(s), {len(store.chunks)} chunk(s), "
        f"built {store.built_at or 'unknown'}:"
    )
    for d in store.docs:
        print(
            f"- {d['title']} ({d['pages']} page(s), "
            f"{d['chunk_count']} chunk(s))"
        )


def cmd_clear(args) -> None:
    path = _store_path(args)
    if path.exists():
        path.unlink()
        print(f"Removed index at {path}")
    else:
        print("No index to remove.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="schoolsift",
        description=(
            "Search school PDFs in plain language and get cited answers "
            "with key dates. v" + __version__
        ),
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--store",
        default=None,
        help="Index file path (default: ~/.schoolsift/index.json or $SCHOOLSIFT_STORE)",
    )

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--store",
        default=argparse.SUPPRESS,
        help="Index file path (default: ~/.schoolsift/index.json or $SCHOOLSIFT_STORE)",
    )

    sub = parser.add_subparsers(dest="command", metavar="COMMAND", required=True)

    p_index = sub.add_parser(
        "index", parents=[common],
        help="Index a folder of school documents (.pdf/.txt/.md)",
    )
    p_index.add_argument("folder", help="Folder containing school documents")
    p_index.set_defaults(func=cmd_index)

    p_ask = sub.add_parser(
        "ask", parents=[common], help="Ask a plain-language question"
    )
    p_ask.add_argument("question", help="e.g. 'when is the science fair?'")
    p_ask.add_argument("--top", type=int, default=5, help="Passages to retrieve (default 5)")
    p_ask.set_defaults(func=cmd_ask)

    p_dates = sub.add_parser(
        "dates", parents=[common],
        help="List dates/deadlines in the most relevant passages",
    )
    p_dates.add_argument("question", help="e.g. 'permission slip'")
    p_dates.add_argument("--top", type=int, default=5, help="Passages to retrieve (default 5)")
    p_dates.set_defaults(func=cmd_dates)

    p_list = sub.add_parser(
        "list", parents=[common], help="List indexed documents"
    )
    p_list.set_defaults(func=cmd_list)

    p_clear = sub.add_parser(
        "clear", parents=[common], help="Delete the local index"
    )
    p_clear.set_defaults(func=cmd_clear)

    args = parser.parse_args(argv)
    args.func(args)