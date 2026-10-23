"""
triallight — Plain-language clinical trial assistant.

CLI entry point.

Usage:
  python main.py "type 2 diabetes"
  python main.py "multiple sclerosis" --city "San Francisco"
  python main.py "lung cancer" --city "Houston" --trials 8 --no-pubmed
  python main.py "asthma" --model "gpt-4o"
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Ensure project root is on path so src.* imports work as a package
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from src.clinicaltrials import parse_studies, search_studies
from src.geo import geocode_city, format_location_query
from src.llm import generate_search_summary, generate_study_digest
from src.models import SearchResult as SR
from src.pubmed import search_articles

load_dotenv()
console = Console()


def run_triallight(args: argparse.Namespace) -> int:
    """Execute the triallight pipeline."""
    condition = args.condition.strip()
    city = args.city
    max_trials = args.trials
    use_pubmed = args.pubmed
    model = args.model

    console.print(Panel.fit(
        f"[bold cyan]🔬 triallight[/] — Plain-Language Clinical Trial Search",
        border_style="cyan",
    ))
    console.print(f"[dim]Searching for[/] [bold]{condition}[/][dim]...[/]")

    # ── Step 1: Geocode city (optional) ─────────────────────────────────
    location_str = None
    if city:
        geo = geocode_city(city)
        if geo:
            location_str = f"{geo['name']}, {geo['region']}, {geo['country']}"
            console.print(f"  📍 Location: [green]{location_str}[/]")
        else:
            console.print(f"  ⚠️  Could not geocode [yellow]{city}[/]; searching nationwide.")

    # ── Step 2: Search ClinicalTrials.gov ───────────────────────────────
    loc_query = format_location_query(city) if city else None
    api_response = search_studies(condition, page_size=max_trials, location_query=loc_query)
    studies = parse_studies(api_response)

    total_matched = api_response.get("totalCount", len(studies))
    console.print(f"  📋 Found [bold]{total_matched}[/] active study/studies.")
    if not studies:
        console.print("\n[yellow]No active studies found matching your search.[/]")
        return 0

    # ── Step 3: Fetch PubMed articles (optional) ────────────────────────
    articles = []
    if use_pubmed:
        console.print("  📄 Fetching recent PubMed articles...")
        try:
            articles = search_articles(condition, max_results=3)
            console.print(f"     Found [bold]{len(articles)}[/] recent publications.")
        except Exception as e:
            console.print(f"     ⚠️ PubMed fetch failed: {e}")

    # ── Step 4: Generate search summary ─────────────────────────────────
    result_obj = SR(
        query=condition,
        location=location_str,
        studies=studies,
        recent_articles=articles,
    )

    if args.api_key:
        console.print("\n[bold]Generating search overview...[/]")
        try:
            summary = generate_search_summary(result_obj, model=model)
            console.print(Markdown(summary))
        except Exception as e:
            console.print(f"  ⚠️ Summary generation failed: {e}")

    # ── Step 5: Generate per-study digests ──────────────────────────────
    for i, study in enumerate(studies[:max_trials]):
        console.print()
        console.print(Rule(f"[bold]Study {i+1} of {min(len(studies), max_trials)}[/]"))

        if args.api_key:
            try:
                digest = generate_study_digest(study, articles, model=model)
                console.print(Markdown(digest))
            except Exception as e:
                console.print(f"  ⚠️ Digest generation failed: {e}")
                # Fallback: show raw study info
                _show_raw_study(study)
        else:
            _show_raw_study(study)

    console.print()
    console.print(Rule(style="dim"))
    console.print(
        "[dim]💡 Run with[/] [bold]--model[/] [dim]to change the LLM, "
        "[bold]--no-pubmed[/] to skip research context, "
        "or set [bold]OPENAI_API_KEY[/] in .env to enable AI digests.[/]"
    )
    return 0


def _show_raw_study(study) -> None:
    """Show a compact raw view of a study (non-LLM fallback)."""
    console.print(f"[bold]{study.brief_title or study.official_title}[/]")
    console.print(f"  📋 NCT ID: {study.nct_id}")
    console.print(f"  🏥 Sponsor: {study.lead_sponsor or 'N/A'}")
    console.print(f"  📍 Phase: {study.phase or 'N/A'}  |  👥 Enrolled: {study.enrollment_count or 'N/A'}")
    if study.locations:
        cities = set(f"{l.city}, {l.state}" for l in study.locations if l.city)
        if cities:
            console.print(f"  📌 Locations: {', '.join(sorted(cities)[:5])}")
    if study.brief_summary:
        console.print(f"  📝 {study.brief_summary[:300]}...")
    if study.eligibility_criteria:
        inc = [c.text for c in study.eligibility_criteria if c.category == "INCLUSION"][:3]
        exc = [c.text for c in study.eligibility_criteria if c.category == "EXCLUSION"][:3]
        if inc:
            console.print(f"  ✅ Inclusion (sample): {' | '.join(inc)}")
        if exc:
            console.print(f"  ❌ Exclusion (sample): {' | '.join(exc)}")
    console.print(f"  🔗 [link={study.url}]{study.url}[/]")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="triallight — Plain-language clinical trial assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python main.py "type 2 diabetes"\n'
            '  python main.py "multiple sclerosis" --city "San Francisco"\n'
            '  python main.py "lung cancer" --trials 5 --model "gpt-4o-mini"\n'
            "\nEnvironment variables:\n"
            "  OPENAI_API_KEY   (required for AI-powered digests)\n"
            "  OPENAI_BASE_URL  (optional, for OpenRouter etc.)\n"
            "  OPENROUTER_API_KEY (fallback if OPENAI_API_KEY not set)\n"
        ),
    )
    parser.add_argument("condition", type=str, help="Medical condition to search for (e.g., 'type 2 diabetes')")
    parser.add_argument("--city", "-c", type=str, default="", help="City name for location-based results")
    parser.add_argument("--trials", "-t", type=int, default=5, help="Max trials to display (default: 5)")
    parser.add_argument("--model", "-m", type=str, default="gpt-4o-mini", help="LLM model (default: gpt-4o-mini)")
    parser.add_argument("--pubmed", action="store_true", default=True, help="Include PubMed context (default: on)")
    parser.add_argument("--no-pubmed", action="store_false", dest="pubmed", help="Skip PubMed fetch")
    parser.add_argument("--api-key", action="store_true", default=True, help="Use LLM for digests (default: on)")
    parser.add_argument("--raw", action="store_false", dest="api_key", help="Show raw study data only (no LLM)")

    args = parser.parse_args()

    # Check for API key
    has_key = bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY"))
    if args.api_key and not has_key:
        console.print("[yellow]⚠️  No API key found. Set OPENAI_API_KEY in .env or use --raw.[/]")
        args.api_key = False

    try:
        return run_triallight(args)
    except KeyboardInterrupt:
        console.print("\n[yellow]Aborted.[/]")
        return 130
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/]")
        return 1


if __name__ == "__main__":
    sys.exit(main())