"""CommuteCrafter — fit content to your exact commute window."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from . import __version__
from .models import ContentItem
from .render import plan_json, render_history, render_items, render_plan
from .store import Store

# ── helpers ─────────────────────────────────────────────────────────────────


def _parse_topics(txt: str) -> list[str]:
    if not txt:
        return ["curious"]
    return [t.strip() for t in txt.split(",") if t.strip()] or ["curious"]


def _gather(topic: str, offline: bool) -> list[ContentItem]:
    """Collect content items from all keyless sources for a single topic."""
    if offline:
        return _load_offline(topic)

    from .sources import build_sources

    sources = build_sources()
    all_items: list[ContentItem] = []
    warnings: list[str] = []
    for src in sources:
        try:
            fetched = src.fetch(topic)
            all_items.extend(fetched)
        except Exception as exc:  # noqa: BLE001 - sources are best-effort
            warnings.append(f"{src.name}: {type(exc).__name__}")

    # Dedupe across sources (same URL may appear from different services)
    seen_urls: set[str] = set()
    deduped: list[ContentItem] = []
    for item in all_items:
        key = item.url.strip().lower()
        if not key or key in seen_urls:
            continue
        seen_urls.add(key)
        deduped.append(item)

    if not deduped:
        print(f"[dim]Live sources returned nothing for '{topic}' — trying offline corpus.[/dim]")
        return _load_offline(topic)

    if warnings:
        print(f"[dim]Source warnings: {'; '.join(warnings)}[/dim]", file=sys.stderr)
    return deduped


def _load_offline(topic: str) -> list[ContentItem]:
    """Filter the bundled sample corpus by tag/title match on ``topic``."""
    import importlib.resources

    # We are inside the package, so "data" is a package sibling. Use importlib.
    try:
        text = importlib.resources.read_text("commutecrafter.data", "sample_corpus.json")
    except (FileNotFoundError, ModuleNotFoundError, ImportError, OSError):
        pkg_dir = os.path.join(os.path.dirname(__file__), "data")
        with open(os.path.join(pkg_dir, "sample_corpus.json"), "r", encoding="utf-8") as fh:
            text = fh.read()

    import re

    records: list[dict] = json.loads(text)
    terms = {t.lower() for t in re.split(r"[^a-z0-9]+", topic.lower()) if len(t) > 2}
    matched: list[ContentItem] = []
    for rec in records:
        tags = {str(t).lower() for t in rec.get("tags", [])}
        title_words = {
            w.lower()
            for w in re.split(r"[^a-z0-9]+", (rec.get("title", "") or ""))
            if len(w) > 2
        }
        if terms & (tags | title_words):
            matched.append(
                ContentItem(
                    title=rec["title"],
                    source=rec.get("source", "offline"),
                    url=rec.get("url", ""),
                    words=int(rec.get("words", 500)),
                    summary=rec.get("summary", ""),
                    category=rec.get("category", "general"),
                )
            )
    return matched or [
        ContentItem(
            title=f"Reading list for {topic}",
            source="offline",
            url="",
            words=1200,
            summary="A fallback item from the offline corpus.",
            category="general",
        )
    ]


def _gather_multi(
    topics: list[str], offline: bool, per_topic: int = 4
) -> list[ContentItem]:
    all_items: list[ContentItem] = []
    for topic in topics[:5]:
        items = _gather(topic, offline)
        all_items.extend(items[:per_topic])
    from .sources.base import dedupe

    return dedupe(all_items)


# ── commands ────────────────────────────────────────────────────────────────


def cmd_plan(args: argparse.Namespace) -> int:
    from .planner import build_plan
    from .timing import clamp_minutes
    from .weather import recommend_mode, weather_for_city
    from .llm import apply_template_reasons, enrich_plan

    topics = _parse_topics(args.interests)
    items = _gather_multi(topics, offline=args.offline, per_topic=10)
    if not items:
        print("[red]Error: no items could be gathered from any source.[/red]", file=sys.stderr)
        return 1

    store = None if args.no_cache else Store()

    # Weather
    weather = None
    if args.city and not args.no_weather:
        weather = weather_for_city(args.city)
        if weather is None:
            print(f"Could not resolve weather for '{args.city}'.", file=sys.stderr)

    # Mode: explicit flag wins, otherwise transport/weather decide.
    mode = args.mode
    reason = ""
    if mode is None:
        if weather or args.transport:
            mode, reason = recommend_mode(weather, args.transport)
        else:
            mode = "read"
    if mode == "either":
        mode = "read"
    if reason:
        print(f"mode {mode}: {reason}", file=sys.stderr)

    exclude = store.recently_served() if store and not args.no_cache else set()
    plan = build_plan(
        items,
        minutes=clamp_minutes(args.minutes),
        mode=mode,
        tolerance=args.tolerance,
        exclude_urls=exclude,
        transport=args.transport,
        weather=weather,
    )

    # Enrich reasons
    if args.explain:
        enriched = enrich_plan(plan)
        if enriched == 0:
            apply_template_reasons(plan)
    else:
        apply_template_reasons(plan)

    # Persist
    if store and not args.dry_run:
        plan_id = store.record_plan(plan)
        if plan.scheduled_items:
            urls = [(s.item.url, s.item.title, s.item.source) for s in plan.scheduled_items]
            store.mark_served(urls)

    # Output
    if args.json:
        print(plan_json(plan))
    else:
        from rich.console import Console

        console = Console()
        render_plan(plan, console=console)

    return 0


def cmd_search(args: argparse.Namespace) -> int:
    from rich.console import Console

    topics = _parse_topics(args.query)
    items = _gather_multi(topics, offline=args.offline, per_topic=8)
    if args.source:
        items = [i for i in items if i.source == args.source]
    if args.limit:
        items = items[: args.limit]
    console = args.console or Console()
    if args.json:
        print(json.dumps([i.to_dict() for i in items], indent=2, ensure_ascii=False))
    else:
        render_items(items, console=console)
    return 0


def cmd_sources(args: argparse.Namespace) -> int:
    from .sources import SOURCE_NAMES

    from rich.console import Console

    console = args.console or Console()
    from rich.table import Table

    table = Table(title="Content sources", title_justify="left")
    table.add_column("source")
    table.add_column("key?")
    table.add_column("category")
    for name in SOURCE_NAMES:
        table.add_row(name, "no key", {"wikipedia": "culture", "arxiv": "deep", "hackernews": "news", "gutenberg": "reflective"}.get(name, "?"))
    console.print(table)
    console.print("All sources are keyless and public.")
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    from rich.console import Console

    store = Store()
    rows = store.history(args.limit)
    console = args.console or Console()
    render_history(rows, console=console)
    return 0


def cmd_clear(args: argparse.Namespace) -> int:
    Store().clear()
    print("Cache cleared.")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    stats = Store().stats()
    print(f"Saved plans:   {stats['plans']}")
    print(f"Served items:  {stats['served_items']}")
    print(f"Database:      {stats['db']}")
    return 0


# ── argument parser ─────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="commutecrafter",
        description="Fit content to your exact commute window.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    # plan
    pp = sub.add_parser("plan", help="Build a commute plan")
    pp.add_argument("-m", "--minutes", type=float, default=22.0, help="Commute window in minutes (default 22)")
    pp.add_argument("-i", "--interests", default="curious", help="Comma-separated topics (default 'curious')")
    pp.add_argument("--mode", choices=["read", "listen", "either"], default=None, help="Force a consumption mode")
    pp.add_argument("--no-weather", dest="no_weather", action="store_true", help="Ignore weather even if --city is given")
    pp.add_argument("-t", "--transport", default=None, help="Transport mode (walk, drive, train…)")
    pp.add_argument("-c", "--city", default=None, help="Your city for weather‑aware mode selection")
    pp.add_argument("--tolerance", type=int, default=90, help="Acceptable overshoot/undershoot in seconds (default 90)")
    pp.add_argument("--offline", action="store_true", help="Use bundled sample corpus instead of live APIs")
    pp.add_argument("--explain", action="store_true", default=True, help="LLM enrichment (default on, falls back to template)")
    pp.add_argument("--no-explain", dest="explain", action="store_false", help="Skip LLM enrichment even when key set")
    pp.add_argument("--no-cache", action="store_true", help="Skip reading/writing the server-URL cache")
    pp.add_argument("--dry-run", action="store_true", help="Don't persist the plan")
    pp.add_argument("-j", "--json", action="store_true", help="Output as JSON")
    pp.set_defaults(func=cmd_plan)

    # search
    sp = sub.add_parser("search", help="List available content for a topic")
    sp.add_argument("query", nargs="?", default="curious", help="Topic to search for")
    sp.add_argument("-s", "--source", default=None, help="Filter by source name")
    sp.add_argument("-l", "--limit", type=int, default=10, help="Max results")
    sp.add_argument("--offline", action="store_true")
    sp.add_argument("-j", "--json", action="store_true")
    sp.set_defaults(func=cmd_search)

    # sources
    sub.add_parser("sources", help="Show available content sources").set_defaults(func=cmd_sources)

    # history
    hp = sub.add_parser("history", help="Show recent plans")
    hp.add_argument("-l", "--limit", type=int, default=10)
    hp.set_defaults(func=cmd_history)

    # clear
    sub.add_parser("clear", help="Delete all cached served URLs and history").set_defaults(func=cmd_clear)

    # stats
    sub.add_parser("stats", help="Show database stats").set_defaults(func=cmd_stats)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    # Attach a reusable Console reference so tests can override it.
    args.console = getattr(args, "console", None)
    return args.func(args)