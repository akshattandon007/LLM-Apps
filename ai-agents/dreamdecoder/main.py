#!/usr/bin/env python3
"""DreamDecoder — AI-powered dream journal with symbolic interpretation.

Usage:
    python main.py log "I was flying over mountains" --tag flying --tag peaceful
    python main.py list
    python main.py view <entry-id>
    python main.py search "water"
    python main.py stats
    python main.py delete <entry-id>
    python main.py clear
"""

from src.cli import main

if __name__ == "__main__":
    main()