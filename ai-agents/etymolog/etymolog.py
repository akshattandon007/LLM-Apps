#!/usr/bin/env python3
"""
etymolog — word etymology journey explorer.

Type any English word and get its full journey:
- Origin language and first recorded use
- How meaning drifted over centuries
- Cousin words you didn't know were related
- Rhyming and semantically related words

APIs: Wiktionary (free, no auth), Datamuse (free, no auth)
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

# ── Datamuse API ──────────────────────────────────────────────────────────────

DATAMUSE_BASE = "https://api.datamuse.com/words"
UA = "etymolog/1.0 (LLM-Apps; +https://github.com/akshattandon007/LLM-Apps)"


def fetch_related_words(word: str, limit: int = 8) -> dict:
    """Fetch semantically related and rhyming words from Datamuse."""
    result = {"similar": [], "rhymes": [], "triggers": []}

    for key, param in [("similar", "ml"), ("rhymes", "rel_rhy"), ("triggers", "rel_trg")]:
        try:
            lim = limit if key != "triggers" else 5
            url = f"{DATAMUSE_BASE}?{param}={urllib.parse.quote(word)}&max={lim}"
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                result[key] = [{"word": d["word"], "score": d.get("score", 0)} for d in data]
        except Exception as e:
            result[f"{key}_error"] = str(e)

    return result


# ── Wiktionary API ────────────────────────────────────────────────────────────

WIKTIONARY_API = "https://en.wiktionary.org/w/api.php"


def _fetch_sections(word: str) -> list:
    """Get the section structure of a Wiktionary page."""
    params = {
        "action": "parse",
        "page": word,
        "prop": "sections",
        "format": "json",
    }
    url = f"{WIKTIONARY_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return data.get("parse", {}).get("sections", [])
    except Exception:
        return []


def _fetch_section_text(word: str, section_index: str) -> str:
    """Fetch the wikitext for a specific section by index."""
    params = {
        "action": "parse",
        "page": word,
        "prop": "text",
        "section": section_index,
        "format": "json",
    }
    url = f"{WIKTIONARY_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        html = data.get("parse", {}).get("text", {}).get("*", "")
        # Strip style/script blocks first (they crowd out real text)
        clean = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL)
        clean = re.sub(r"<script[^>]*>.*?</script>", " ", clean, flags=re.DOTALL)
        # Strip remaining HTML tags
        clean = re.sub(r"<[^>]+>", " ", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean[:2000]
    except Exception:
        return ""


def fetch_etymology(word: str) -> dict:
    """Fetch etymology data from Wiktionary."""
    result = {"etymology": "", "definitions": [], "language": "", "origin": ""}

    # Step 1: Get sections to find etymology
    sections = _fetch_sections(word)

    etymology_texts = []
    for s in sections:
        if "etymolog" in s.get("line", "").lower():
            text = _fetch_section_text(word, s["index"])
            if text:
                etymology_texts.append(text)

    result["etymology"] = "\n\n".join(etymology_texts)

    # Step 2: Try the REST API for structured definitions
    rest_url = f"https://en.wiktionary.org/api/rest_v1/page/definition/{urllib.parse.quote(word)}"
    try:
        req = urllib.request.Request(rest_url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        if "en" in data:
            defs = []
            for entry in data["en"]:
                d = entry.get("definition", "")
                if d and d != "...":
                    defs.append(d)
            result["definitions"] = defs[:5]
    except Exception:
        pass

    return result


# ── LLM Narrative (OpenRouter) ───────────────────────────────────────────────

def generate_narrative(word: str, etymology: dict, related: dict) -> str:
    """Use an LLM to weave etymology data into a narrative journey."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return _fallback_narrative(word, etymology, related)

    system_prompt = (
        "You are an engaging word-etymology guide. "
        "Given a word, its etymology, and related words, produce a 3-4 paragraph "
        "narrative about the word's journey through history. "
        "Include: (1) where it came from and what it originally meant, "
        "(2) how its meaning changed over time, "
        "(3) surprising cousin words in other languages, "
        "(4) a fun fact that makes the word memorable. "
        "Be conversational and fascinating — write like a podcast host, not a dictionary."
    )

    user_prompt = (
        f"Word: {word}\n\n"
        f"Etymology from Wiktionary: {etymology.get('etymology', 'Not found')[:1500]}\n\n"
        f"Definitions: {'; '.join(etymology.get('definitions', [])[:3])}\n\n"
        f"Similar words: {', '.join(w['word'] for w in related.get('similar', [])[:5])}\n"
        f"Rhyming words: {', '.join(w['word'] for w in related.get('rhymes', [])[:5])}\n"
        f"Associated words: {', '.join(w['word'] for w in related.get('triggers', [])[:5])}"
    )

    payload = json.dumps({
        "model": "deepseek/deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 800,
        "temperature": 0.7,
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/akshattandon007/LLM-Apps",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return _fallback_narrative(word, etymology, related) + (
            f"\n\n[Note: LLM narrative unavailable ({e}). Showing raw data above.]"
        )


def _fallback_narrative(word: str, etymology: dict, related: dict) -> str:
    """Generate a simple text-based report when LLM is unavailable."""
    lines = [f"📖 Word: {word}", ""]

    if etymology.get("etymology"):
        lines.append("── Origin ──")
        lines.append(etymology["etymology"][:500])
        lines.append("")

    if etymology.get("definitions"):
        lines.append("── Definitions ──")
        for i, d in enumerate(etymology["definitions"][:3], 1):
            lines.append(f"  {i}. {d}")
        lines.append("")

    if related.get("similar"):
        lines.append("── Similar Words ──")
        lines.append(", ".join(w["word"] for w in related["similar"][:8]))
        lines.append("")

    if related.get("rhymes"):
        lines.append("── Rhymes ──")
        lines.append(", ".join(w["word"] for w in related["rhymes"][:8]))
        lines.append("")

    if related.get("triggers"):
        lines.append("── Associated Words ──")
        lines.append(", ".join(w["word"] for w in related["triggers"][:5]))

    return "\n".join(lines)


# ── CLI Entry ─────────────────────────────────────────────────────────────────

def format_output(word: str, etymology: dict, related: dict, narrative: str) -> str:
    """Format the final output for display."""
    sep = "─" * 48
    lines = [
        f"  ╔══════════════════════════════════════════════╗",
        f"  ║           📖  e t y m o l o g                ║",
        f"  ║     The Word Journey Explorer                ║",
        f"  ╚══════════════════════════════════════════════╝",
        "",
        f"  ✦  {word.upper()}",
        sep,
        "",
        narrative,
        "",
        sep,
        "  Data sources: Wiktionary (CC-BY-SA) · Datamuse",
        "  LLM: OpenRouter (deepseek/deepseek-v4-flash)",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="etymolog — explore the journey of any English word",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  etymolog serendipity      # etymology of 'serendipity'\n"
            "  etymolog --json serendipity  # JSON output\n"
            "  echo serendipity | etymolog   # pipe mode"
        ),
    )
    parser.add_argument("word", nargs="?", help="Word to explore")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM narrative, show raw data")

    args = parser.parse_args()

    word = args.word
    if not word:
        word = sys.stdin.read().strip()
    if not word:
        parser.print_help()
        sys.exit(1)

    word = word.strip().lower()

    # Fetch data
    etymology = fetch_etymology(word)
    related = fetch_related_words(word)

    # Generate narrative (or use fallback for raw display)
    if args.no_llm:
        narrative = _fallback_narrative(word, etymology, related)
    else:
        narrative = generate_narrative(word, etymology, related)

    if args.json:
        output = {
            "word": word,
            "etymology": etymology,
            "related": related,
            "narrative": narrative,
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_output(word, etymology, related, narrative))


if __name__ == "__main__":
    main()