#!/usr/bin/env python3
"""bookmatch — AI Book Matchmaker

A CLI tool that interviews you about your reading habits, tastes, and goals,
then recommends books you'll actually enjoy using an LLM via OpenRouter.
"""

import os
import sys
import json
from typing import Optional
from dataclasses import dataclass, field

import httpx

# ── Config ──────────────────────────────────────────────────────────────

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"  # fast + cheap

# ── Data types ──────────────────────────────────────────────────────────

@dataclass
class ReaderProfile:
    name: str = ""
    favorite_books: list[str] = field(default_factory=list)
    disliked_books: list[str] = field(default_factory=list)
    genres_liked: list[str] = field(default_factory=list)
    recently_read: list[str] = field(default_factory=list)
    reading_goal: str = ""
    preferred_length: str = ""
    mood: str = ""
    dealbreakers: list[str] = field(default_factory=list)

@dataclass
class BookRec:
    title: str
    author: str
    why: str
    genre: str
    perfect_for: str
    similar_to: str = ""

# ── LLM caller ──────────────────────────────────────────────────────────

def call_llm(system: str, user: str, temp: float = 0.7) -> str:
    """Call OpenRouter chat completion, return text."""
    if not OPENROUTER_KEY:
        return "⚠️  OPENROUTER_API_KEY not set in environment. Please set it and try again."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temp,
        "max_tokens": 2000,
    }

    try:
        resp = httpx.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error talking to LLM: {e}"

# ── Interview engine ────────────────────────────────────────────────────

QUESTIONS = [
    {
        "key": "favorite_books",
        "ask": "What are a few books you've absolutely LOVED? (comma-separated titles)",
        "hint": "e.g. The Martian, Project Hail Mary, Dune",
    },
    {
        "key": "disliked_books",
        "ask": "Any books you really DIDN'T enjoy? What didn't click? (comma-separated titles)",
        "hint": "e.g. Fifty Shades of Grey, The Alchemist",
    },
    {
        "key": "genres_liked",
        "ask": "Which genres do you usually enjoy?",
        "hint": "e.g. sci-fi, fantasy, literary fiction, thriller, romance, memoir",
    },
    {
        "key": "recently_read",
        "ask": "What have you read recently (last 3 books)?",
        "hint": "e.g. Project Hail Mary, The Name of the Wind, Thinking Fast and Slow",
    },
    {
        "key": "reading_goal",
        "ask": "What are you looking for in your next read?",
        "choices": [
            "Something that makes me THINK",
            "Pure escape — take me away!",
            "A good cry / emotional wallop",
            "Laugh-out-loud funny",
            "Edge-of-my-seat thriller",
            "Beautiful writing / prose",
            "Learn something new",
            "I don't know — surprise me!",
        ],
    },
    {
        "key": "preferred_length",
        "ask": "Book length preference?",
        "choices": ["Quick read (< 300 pages)", "Medium (300–450)", "Epic (450+)", "No preference"],
    },
    {
        "key": "mood",
        "ask": "What's your current mood?",
        "choices": [
            "Cozy & comfort-seeking",
            "Adventurous & curious",
            "Melancholy & reflective",
            "Energized & ambitious",
            "Tired & need something light",
            "Focused & want depth",
        ],
    },
    {
        "key": "dealbreakers",
        "ask": "Any dealbreakers? Things you never want to see in a book?",
        "hint": "e.g. animal death, sexual violence, slow pacing, unreliable narrator, love triangles",
    },
]

def run_interview() -> ReaderProfile:
    """Interactive CLI interview. Returns a ReaderProfile."""
    print("\n" + "=" * 60)
    print("  📚  BOOKMATCH — Find Your Next Favorite Book")
    print("=" * 60)
    print("\nLet's get to know you as a reader. I'll ask a few questions...\n")

    profile = ReaderProfile()

    for q in QUESTIONS:
        key = q["key"]
        answer = ""
        print(f"\n--- {q['ask']} ---")
        if "choices" in q:
            for i, choice in enumerate(q["choices"], 1):
                print(f"  {i}. {choice}")
            print("  (enter number or type your own)")
            answer = input("> ").strip()
            if answer.isdigit():
                idx = int(answer) - 1
                if 0 <= idx < len(q["choices"]):
                    answer = q["choices"][idx]
        elif "hint" in q:
            print(f"  💡 {q['hint']}")
            answer = input("> ").strip()

        if not answer:
            answer = ""

        if key in ("favorite_books", "disliked_books", "genres_liked", "recently_read", "dealbreakers"):
            setattr(profile, key, [s.strip() for s in answer.split(",") if s.strip()])
        else:
            setattr(profile, key, answer)

    # Name
    print("\n--- Last thing — what should I call you? ---")
    profile.name = input("> ").strip() or "Friend"

    return profile


def build_recommendation_prompt(profile: ReaderProfile) -> tuple[str, str]:
    """Build the LLM system and user prompt from the reader profile."""

    favs = ", ".join(profile.favorite_books) or "None specified"
    dislikes = ", ".join(profile.disliked_books) or "None specified"
    genres = ", ".join(profile.genres_liked) or "Various"
    recent = ", ".join(profile.recently_read) or "Not specified"
    deal = ", ".join(profile.dealbreakers) if profile.dealbreakers else "None"

    system = """You are an expert literary matchmaker — a combination of a passionate bookseller, a perceptive reading therapist, and a librarian who has read everything. Your job is to recommend books that feel PERSONALLY tailored to the reader.

Rules for recommendations:
1. Recommend EXACTLY 5 books — no more, no less
2. Every book must be a real, published book (never hallucinate titles)
3. Mix reasonably well-known and slightly off-the-beaten-path
4. Each recommendation MUST include: title, author, genre, a 2-3 sentence WHY this book fits the reader, and a "perfect for when you're in the mood for..." description
5. Avoid books the reader has already read (check their favorites/recent list)
6. Avoid dealbreakers
7. Include at least one unexpected/stretch recommendation that still fits
8. Format your response as a JSON array with these fields: title, author, genre, why, perfect_for, similar_to (a book they mentioned that this is similar to, or empty string)
"""

    user = f"""Here's the reader profile:

Name: {profile.name}
Favorite books: {favs}
Disliked books: {dislikes}
Genres they like: {genres}
Recently read: {recent}
Reading goal: {profile.reading_goal}
Preferred length: {profile.preferred_length}
Current mood: {profile.mood}
Dealbreakers: {deal}

Based on this profile, recommend 5 books {profile.name} will love. Return ONLY a valid JSON array — no markdown, no code fences, no extra text."""

    return system, user


def parse_recommendations(raw: str) -> list[BookRec]:
    """Parse LLM output into BookRec objects."""
    # Strip code fences if present
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        if "```" in raw:
            raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Try to find a JSON array in the text
        import re
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                return []
        else:
            return []

    recs = []
    for item in data:
        if isinstance(item, dict):
            recs.append(BookRec(
                title=item.get("title", "Unknown"),
                author=item.get("author", "Unknown"),
                why=item.get("why", ""),
                genre=item.get("genre", ""),
                perfect_for=item.get("perfect_for", ""),
                similar_to=item.get("similar_to", ""),
            ))
    return recs


def display_recommendations(recs: list[BookRec], name: str):
    """Pretty-print recommendations."""
    if not recs:
        print("\n😕 I couldn't parse the recommendations. Let me try again...")
        return

    print("\n" + "=" * 60)
    print(f"  📖  {name}, here are your personalized book picks!")
    print("=" * 60)

    for i, rec in enumerate(recs, 1):
        print(f"\n{'─' * 50}")
        print(f"  {i}. {rec.title}")
        print(f"     by {rec.author}  ·  {rec.genre}")
        if rec.similar_to:
            print(f"     → Similar to: {rec.similar_to}")
        print(f"\n     {rec.why}")
        print(f"\n     🎯 {rec.perfect_for}")

    print(f"\n{'=' * 60}")
    print("  Happy reading! 📚")


def save_recommendations(recs: list[BookRec], name: str, filepath: str = "bookmatch-recs.md"):
    """Save recommendations to a markdown file."""
    with open(filepath, "w") as f:
        f.write(f"# 📚 Book Recommendations for {name}\n\n")
        f.write(f"Generated by **bookmatch** — your AI book matchmaker.\n\n")
        f.write("---\n\n")
        for i, rec in enumerate(recs, 1):
            f.write(f"## {i}. {rec.title}\n\n")
            f.write(f"- **Author:** {rec.author}\n")
            f.write(f"- **Genre:** {rec.genre}\n")
            if rec.similar_to:
                f.write(f"- **Similar to:** {rec.similar_to}\n")
            f.write(f"\n{rec.why}\n\n")
            f.write(f"> 🎯 {rec.perfect_for}\n\n")
            f.write("---\n\n")

    return filepath


def main():
    """Main entry point."""
    print("📚 BOOKMATCH — Your AI Book Matchmaker")
    print("=" * 50)

    if not OPENROUTER_KEY:
        print("\n⚠️  OPENROUTER_API_KEY not found in environment.")
        print("   Set it and try again.")
        sys.exit(1)

    # STEP 1: Interview the reader
    profile = run_interview()

    # STEP 2: Generate recommendations
    print(f"\nThanks, {profile.name}! Let me think about what you'd love...\n")
    system, user = build_recommendation_prompt(profile)
    raw_result = call_llm(system, user)

    if raw_result.startswith("Error") or raw_result.startswith("⚠️"):
        print(raw_result)
        sys.exit(1)

    # STEP 3: Parse and display
    recs = parse_recommendations(raw_result)

    if not recs:
        print("\nHmm, I got an unexpected response. Let me try with a simpler format...")
        system2 = "You recommend books. Respond with a JSON array of objects with fields: title, author, genre, why, perfect_for, similar_to. Valid JSON only, no extra text."
        raw2 = call_llm(system2, user)
        recs = parse_recommendations(raw2)

    if recs:
        display_recommendations(recs, profile.name)
        out = save_recommendations(recs, profile.name)
        print(f"\n📝 Saved to: {out}")
    else:
        print("\nCouldn't generate recommendations. The LLM response was unexpected.")
        print(f"Raw: {raw_result[:500]}")


if __name__ == "__main__":
    main()