"""OAuth 2.0 token management for the Gmail API.

Resolution order:
1. GMAIL_CLIENT_ID + GMAIL_CLIENT_SECRET + GMAIL_REFRESH_TOKEN from env/.env
2. token.json saved by a previous interactive auth run
3. Interactive InstalledAppFlow using credentials.json (run `python -m src.auth`)
"""

from __future__ import annotations

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOKEN_PATH = PROJECT_ROOT / "token.json"
CREDENTIALS_PATH = PROJECT_ROOT / "credentials.json"

# gmail.modify covers read + label/archive; gmail.send is required to send.
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]

TOKEN_URI = "https://oauth2.googleapis.com/token"


def _credentials_from_env() -> Credentials | None:
    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")
    if not (client_id and client_secret and refresh_token):
        return None
    return Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
        scopes=GMAIL_SCOPES,
    )


def _credentials_from_token_file() -> Credentials | None:
    if not TOKEN_PATH.exists():
        return None
    return Credentials.from_authorized_user_file(str(TOKEN_PATH), GMAIL_SCOPES)


def _refresh(creds: Credentials) -> None:
    """Refresh an expired token and persist it back to token.json when present."""
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        if TOKEN_PATH.exists():
            TOKEN_PATH.write_text(creds.to_json())


def get_credentials() -> Credentials:
    """Return a usable Gmail OAuth credentials object.

    Raises RuntimeError with setup instructions when nothing is configured.
    """
    creds = _credentials_from_env() or _credentials_from_token_file()
    if creds is None:
        raise RuntimeError(
            "No Gmail credentials found. Set GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET "
            "and GMAIL_REFRESH_TOKEN in .env, or drop credentials.json in the "
            "project root and run `python -m src.auth` once to generate token.json."
        )
    _refresh(creds)
    return creds


def run_interactive_auth() -> Credentials:
    """One-time interactive OAuth flow. Saves token.json to the project root."""
    if not CREDENTIALS_PATH.exists():
        raise RuntimeError(
            "credentials.json not found in the project root. Download it from "
            "Google Cloud Console (APIs & Services > Credentials > OAuth client, "
            "Desktop app) and retry."
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), GMAIL_SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")
    TOKEN_PATH.write_text(creds.to_json())
    print(f"Saved OAuth token to {TOKEN_PATH}")
    return creds


if __name__ == "__main__":
    run_interactive_auth()
