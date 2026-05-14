#!/usr/bin/env python3
"""
One-time Spotify authentication setup.

Run this before using the mood agent:
    python scripts/authenticate.py

Opens a browser for Spotify OAuth authorisation.
Saves the token to .spotify_token_cache for future use.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from rich.console import Console

load_dotenv()
console = Console()


def main():
    console.print()
    console.print("[bold cyan]Spotify Mood Agent — Authentication Setup[/bold cyan]")
    console.print()

    # Check env vars
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        console.print("[red]❌ Missing credentials in .env file[/red]")
        console.print()
        console.print("Steps:")
        console.print("  1. Copy .env.example to .env")
        console.print("  2. Add your SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")
        console.print("  3. Get credentials at: [link]https://developer.spotify.com/dashboard[/link]")
        sys.exit(1)

    console.print("  [dim]Client ID found:[/dim] " + client_id[:8] + "...")
    console.print()
    console.print("Opening browser for Spotify authorisation...")
    console.print("[dim](A browser window should open. If not, check for pop-up blockers.)[/dim]")
    console.print()

    try:
        from src.spotify.auth import check_auth_status, get_spotify_client
        sp = get_spotify_client()
        user = check_auth_status(sp)

        console.print(f"[green]✅ Authenticated successfully![/green]")
        console.print()
        console.print(f"  User:     [bold]{user['display_name']}[/bold]")
        console.print(f"  Account:  {user['product'].title()}")
        console.print(f"  Country:  {user['country']}")
        console.print()
        console.print("[dim]Token cached to .spotify_token_cache[/dim]")
        console.print()
        console.print("You can now run the mood agent:")
        console.print("[bold]  python -m src.main[/bold]")

    except EnvironmentError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Authentication failed:[/red] {e}")
        console.print()
        console.print("Common issues:")
        console.print("  • Redirect URI mismatch — ensure your Spotify app has:")
        console.print("    http://localhost:8888/callback")
        console.print("  • Invalid client credentials")
        sys.exit(1)


if __name__ == "__main__":
    main()
