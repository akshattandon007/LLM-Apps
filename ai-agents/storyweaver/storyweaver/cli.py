"""CLI entry point for StoryWeaver."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .models import StorySession, StoryNode
from .engine import StoryEngine


def _resolve_saves_dir() -> Path:
    """Get or create the saves directory."""
    saves_dir = Path.home() / ".storyweaver" / "saves"
    saves_dir.mkdir(parents=True, exist_ok=True)
    return saves_dir


def cmd_new(args: argparse.Namespace) -> None:
    """Create and start a new interactive story."""
    print("\n" + "=" * 60)
    print("  🎭 STORYWEAVER — Interactive Fiction Generator")
    print("=" * 60)

    title = args.title or input("\n📖 Story title: ").strip()
    genre = args.genre or input("🎭 Genre (fantasy/sci-fi/mystery/horror/romance/adventure): ").strip()
    setting = args.setting or input("🏰 Setting: ").strip()
    characters = args.characters or input("👥 Main characters: ").strip()
    premise = args.premise or input("📝 Premise / starting hook: ").strip()

    if not all([title, genre, setting, characters, premise]):
        print("ERROR: All fields are required.", file=sys.stderr)
        sys.exit(1)

    session = StorySession(
        title=title,
        genre=genre,
        setting=setting,
        characters=characters,
        premise=premise,
    )

    print("\n⚙️  Generating first chapter...")
    engine = _get_engine(args)
    node = engine.generate_first_chapter(session)
    session.add_node(node)

    _display_node(node)
    _save_and_continue(session, engine, args)


def cmd_continue(args: argparse.Namespace) -> None:
    """Resume a saved story session."""
    saves_dir = _resolve_saves_dir()
    save_path = Path(args.path) if args.path else saves_dir / f"{args.story_id}.json"

    if not save_path.exists():
        print(f"ERROR: Save file not found: {save_path}", file=sys.stderr)
        sys.exit(1)

    session = StorySession.load(str(save_path))
    engine = _get_engine(args)
    print(f"\n📖 Resuming: {session.title}\n")

    while True:
        current = session.get_current_node()
        if not current or not current.choices:
            print("\n✨ The story has reached its end.\n")
            epilogue = engine.generate_epilogue(session)
            print(epilogue)
            break

        _display_node(current)
        choice = _get_choice(current)
        if choice is None:
            print("\n👋 Goodbye! Your story is saved.")
            session.save(str(save_path))
            return

        chosen = current.choices[choice]
        print(f"\n➡️  You chose: {chosen.text}\n")

        # Check if we already generated this node
        next_node = _find_node_by_id(session, chosen.next_node_id)
        if next_node:
            session.current_node_id = chosen.next_node_id
            continue

        print("⚙️  Generating next chapter...")
        node = engine.generate_next_chapter(session, chosen.text)
        session.add_node(node)
        session.save(str(save_path))


def cmd_list(args: argparse.Namespace) -> None:
    """List saved stories."""
    saves_dir = _resolve_saves_dir()
    saves = sorted(saves_dir.glob("*.json"))

    if not saves:
        print("No saved stories found.")
        return

    print(f"\n📚 Saved stories ({len(saves)}):\n")
    for sp in saves:
        try:
            session = StorySession.load(str(sp))
            print(f"  [{sp.stem}] {session.title} ({session.genre})")
            print(f"       Chapters: {len(session.nodes)}  |  Created: {session.created_at[:10]}")
        except Exception:
            print(f"  [{sp.stem}] <corrupt save>")


def _get_engine(args: argparse.Namespace) -> StoryEngine:
    """Build the engine from CLI args."""
    return StoryEngine(
        api_key=args.api_key,
        api_base=args.api_base,
        model=args.model,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
    )


def _display_node(node: StoryNode) -> None:
    """Print a story node to the terminal."""
    print("\n" + "-" * 60)
    print(node.narrative)
    print("-" * 60)

    if node.choices:
        print("\nYour choices:\n")
        for i, choice in enumerate(node.choices):
            print(f"  [{i + 1}] {choice.text}")
        print()


def _get_choice(node: StoryNode) -> int | None:
    """Prompt the user to pick a choice. Returns index or None for save & quit."""
    while True:
        try:
            raw = input(f"Enter choice (1-{len(node.choices)}, 's' to save & quit): ").strip().lower()
            if raw == "s":
                return None
            choice = int(raw) - 1
            if 0 <= choice < len(node.choices):
                return choice
            print(f"Please enter a number between 1 and {len(node.choices)}.")
        except (ValueError, EOFError, KeyboardInterrupt):
            return None


def _find_node_by_id(session: StorySession, node_id: int) -> StoryNode | None:
    """Look up a node by ID."""
    for n in session.nodes:
        if n.id == node_id:
            return n
    return None


def _save_and_continue(session: StorySession, engine: StoryEngine, args: argparse.Namespace) -> None:
    """Save the session and loop through the story."""
    saves_dir = _resolve_saves_dir()
    save_path = saves_dir / f"{session.title.lower().replace(' ', '-')[:40]}.json"

    session.save(str(save_path))
    print(f"\n💾 Saved to {save_path}")

    while True:
        current = session.get_current_node()
        if not current or not current.choices:
            print("\n✨ The story has reached its end.\n")
            epilogue = engine.generate_epilogue(session)
            print(epilogue)
            break

        choice = _get_choice(current)
        if choice is None:
            print("\n👋 Goodbye! Your story is saved.")
            session.save(str(save_path))
            return

        chosen = current.choices[choice]
        print(f"\n➡️  You chose: {chosen.text}\n")

        next_node = _find_node_by_id(session, chosen.next_node_id)
        if next_node:
            session.current_node_id = chosen.next_node_id
            continue

        print("⚙️  Generating next chapter...")
        node = engine.generate_next_chapter(session, chosen.text)
        session.add_node(node)
        session.save(str(save_path))
        _display_node(node)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="StoryWeaver — Interactive fiction powered by AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  storyweaver new                          # Interactive setup
  storyweaver new --title "Dragon's Peak" --genre fantasy  # Quick setup
  storyweaver continue --story-id dragons-peak             # Resume
  storyweaver list                         # Show saved stories
        """,
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # New story
    new_p = sub.add_parser("new", help="Start a new story")
    new_p.add_argument("--title", help="Story title")
    new_p.add_argument("--genre", help="Genre (fantasy, sci-fi, mystery, etc.)")
    new_p.add_argument("--setting", help="Story setting")
    new_p.add_argument("--characters", help="Main characters")
    new_p.add_argument("--premise", help="Starting premise/hook")
    new_p.set_defaults(func=cmd_new)

    # Continue
    cont_p = sub.add_parser("continue", help="Resume a saved story")
    cont_p.add_argument("--story-id", help="Story ID (filename without .json)")
    cont_p.add_argument("--path", help="Full path to save file")
    cont_p.set_defaults(func=cmd_continue)

    # List
    list_p = sub.add_parser("list", help="List saved stories")
    list_p.set_defaults(func=cmd_list)

    # Shared engine options
    for p in [new_p, cont_p]:
        p.add_argument("--api-key", help="LLM API key (default: $LLM_API_KEY)")
        p.add_argument("--api-base", default="https://openrouter.ai/api/v1", help="API base URL")
        p.add_argument("--model", default="openai/gpt-4o-mini", help="Model name")
        p.add_argument("--max-tokens", type=int, default=2048, help="Max tokens per chapter")
        p.add_argument("--temperature", type=float, default=0.9, help="Generation temperature (0-2)")

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
