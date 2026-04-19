"""Command-line interface for the Notion Agent.

Subcommands
-----------
- `index`   Crawl the workspace and build/refresh the local vector index.
- `ask`     One-shot natural-language query. Claude picks the tools.
- `read`    Print the content of a specific page (bypasses the agent).
- `append`  Append a section to a page (bypasses the agent).
- `stats`   Show info about the current local index.
- `chat`    Interactive REPL that shares conversation history across turns.

Examples
--------
    notion-agent index
    notion-agent ask "What are the top risks for Project Phoenix?"
    notion-agent read --page 1a2b3c...
    notion-agent append --page <id> --heading "Next Steps" --body "Ship v1."
    notion-agent chat
"""
from __future__ import annotations

import argparse
import logging
import sys

from .agent import NotionAgent
from .config import Settings
from .indexer import build_index
from .notion_client_wrapper import NotionClientWrapper
from .tools import ToolRunner
from .vector_store import VectorStore


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Quiet httpx — it's noisy at INFO.
    logging.getLogger("httpx").setLevel(logging.WARNING)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="notion-agent",
        description="A Claude-powered agent for reading, writing, and searching Notion.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging.")
    sub = parser.add_subparsers(dest="command", required=True)

    # index
    sub.add_parser("index", help="Crawl the workspace and (re)build the local vector index.")

    # stats
    sub.add_parser("stats", help="Show current index statistics.")

    # ask
    p_ask = sub.add_parser("ask", help="Ask a natural-language question.")
    p_ask.add_argument("question", nargs="+", help="The question to ask.")

    # chat
    sub.add_parser("chat", help="Interactive REPL with the agent.")

    # read
    p_read = sub.add_parser("read", help="Print the content of a specific page.")
    p_read.add_argument("--page", required=True, help="Notion page ID or URL.")

    # append
    p_app = sub.add_parser("append", help="Append a section to a page.")
    p_app.add_argument("--page", required=True, help="Notion page ID or URL.")
    p_app.add_argument("--heading", required=True, help="Heading for the new section.")
    p_app.add_argument("--body", default=None, help="Optional paragraph body under the heading.")

    return parser


# ----------------------------------------------------------------- commands


def cmd_index(settings: Settings) -> int:
    notion = NotionClientWrapper(settings.notion_token)
    store = VectorStore(settings.index_dir, model_name=settings.embedding_model)
    summary = build_index(
        notion,
        store,
        chunk_size=settings.chunk_size_chars,
        overlap=settings.chunk_overlap_chars,
    )
    print(f"Indexed {summary['pages']} pages into {summary['chunks']} chunks.")
    print(f"Stored at: {settings.index_dir}")
    return 0


def cmd_stats(settings: Settings) -> int:
    store = VectorStore(settings.index_dir, model_name=settings.embedding_model)
    if not store.load():
        print(f"No index found at {settings.index_dir}. Run `notion-agent index` first.")
        return 1
    stats = store.stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    return 0


def cmd_ask(settings: Settings, question: str, verbose: bool) -> int:
    notion = NotionClientWrapper(settings.notion_token)
    store = VectorStore(settings.index_dir, model_name=settings.embedding_model)
    if not store.load():
        print(
            "⚠  No vector index found. Semantic search will return nothing until you run "
            "`notion-agent index`. Proceeding anyway — read_page and append_section still work.",
            file=sys.stderr,
        )
    runner = ToolRunner(notion, store, top_k=settings.top_k)
    agent = NotionAgent(
        api_key=settings.anthropic_api_key,
        model=settings.claude_model,
        tool_runner=runner,
        max_turns=settings.max_agent_turns,
        max_tokens=settings.max_tokens_per_turn,
    )
    result = agent.run(question, verbose=verbose)
    print(result.text)
    if verbose:
        print(f"\n[{result.turns} turn(s), {len(result.tool_calls)} tool call(s)]")
    return 0


def cmd_chat(settings: Settings, verbose: bool) -> int:
    """Interactive REPL. Each turn is a new agent run — we don't thread history
    through Claude's `messages` across prompts for simplicity and cost control.
    Users who want multi-turn memory can feed prior answers back in themselves.
    """
    notion = NotionClientWrapper(settings.notion_token)
    store = VectorStore(settings.index_dir, model_name=settings.embedding_model)
    store.load()
    runner = ToolRunner(notion, store, top_k=settings.top_k)
    agent = NotionAgent(
        api_key=settings.anthropic_api_key,
        model=settings.claude_model,
        tool_runner=runner,
        max_turns=settings.max_agent_turns,
        max_tokens=settings.max_tokens_per_turn,
    )
    print("Notion Agent — interactive mode. Ctrl-D or 'exit' to quit.\n")
    while True:
        try:
            question = input("you > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            return 0
        result = agent.run(question, verbose=verbose)
        print(f"\nclaude > {result.text}\n")


def cmd_read(settings: Settings, page_id: str) -> int:
    notion = NotionClientWrapper(settings.notion_token)
    page = notion.get_page(page_id)
    print(f"# {page.title}")
    print(f"URL: {page.url}")
    print(f"ID:  {page.page_id}")
    print()
    print(page.text or "(page is empty)")
    return 0


def cmd_append(settings: Settings, page_id: str, heading: str, body: str | None) -> int:
    notion = NotionClientWrapper(settings.notion_token)
    notion.append_section(page_id=page_id, heading=heading, body=body)
    print(f"Appended section '{heading}' to page {page_id}.")
    return 0


# -------------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    try:
        settings = Settings.from_env()
    except RuntimeError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 2

    if args.command == "index":
        return cmd_index(settings)
    if args.command == "stats":
        return cmd_stats(settings)
    if args.command == "ask":
        return cmd_ask(settings, " ".join(args.question), verbose=args.verbose)
    if args.command == "chat":
        return cmd_chat(settings, verbose=args.verbose)
    if args.command == "read":
        return cmd_read(settings, args.page)
    if args.command == "append":
        return cmd_append(settings, args.page, args.heading, args.body)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
