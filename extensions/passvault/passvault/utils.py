"""Utility functions for passvault CLI."""

import subprocess
import sys


def copy_to_clipboard(text: str) -> bool:
    """Try to copy text to system clipboard.

    Returns True if successful, False otherwise.
    """
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except (ImportError, Exception):
        pass

    # Fallback: try system commands
    system = sys.platform
    try:
        if system == "darwin":
            # macOS
            p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            p.communicate(input=text.encode("utf-8"))
            return p.returncode == 0
        elif system == "linux" or system == "linux2":
            # Linux — try xclip or wl-copy (Wayland)
            for cmd in (["xclip", "-selection", "clipboard"], ["wl-copy"]):
                try:
                    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                    p.communicate(input=text.encode("utf-8"))
                    if p.returncode == 0:
                        return True
                except FileNotFoundError:
                    continue
        elif system == "win32":
            # Windows
            p = subprocess.Popen(["clip"], stdin=subprocess.PIPE)
            p.communicate(input=text.encode("utf-8"))
            return p.returncode == 0
    except Exception:
        pass
    return False


def print_entry(entry: dict, show_password: bool = True) -> None:
    """Pretty-print a vault entry."""
    print(f"  Name:     {entry['name']}")
    if entry.get("url"):
        print(f"  URL:      {entry['url']}")
    print(f"  Username: {entry.get('username', '')}")
    if show_password:
        print(f"  Password: {entry['password']}")
    else:
        print(f"  Password: {'*' * len(entry['password'])}")
    if entry.get("notes"):
        print(f"  Notes:    {entry['notes']}")
    print(f"  Created:  {entry.get('created_at', '')}")
    print(f"  Updated:  {entry.get('updated_at', '')}")