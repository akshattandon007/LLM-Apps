# Bookmatch 📚 — Your AI Book Matchmaker

> **Tell the AI about your reading tastes. Get 5 books you'll actually love.**

---

## What is this?

Bookmatch is a CLI tool that interviews you about your reading habits — favorite books, genres, what you're in the mood for — then uses AI (via OpenRouter) to recommend 5 personally-tailored books with detailed "why you'll love this" explanations.

No sign-up. No algorithms. No "people who bought this also bought." Just a thoughtful conversation with a literary matchmaker.

---

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Run
python bookmatch/main.py
```

The tool will ask you 8 questions about your reading tastes and generate personalized recommendations.

---

## Features

- 🎯 **Interactive interview** — 8 questions that build a real picture of your reading personality
- 📚 **5 personalized recommendations** — mixing well-known gems with hidden treasures
- 📝 **Save to markdown** — your recommendations are saved to `bookmatch-recs.md`
- 🎭 **Mood-aware** — tells the AI your current reading mood for better picks
- 🚫 **Dealbreaker-aware** — no books with things you hate
- 🔄 **Refineable** — re-run anytime with updated tastes

---

## Example

```
📚 BOOKMATCH — Your AI Book Matchmaker
============================================================

--- What are a few books you've absolutely LOVED? ---
  💡 e.g. The Martian, Project Hail Mary, Dune
> The Name of the Wind, Project Hail Mary, Piranesi

--- What are you looking for in your next read? ---
  1. Something that makes me THINK
  2. Pure escape — take me away!
  3. A good cry / emotional wallop
  ...
> 2
```

```
============================================================
  📖  Friend, here are your personalized book picks!
============================================================

  1. The House in the Cerulean Sea
     by TJ Klune  ·  Fantasy / Cozy Fiction
     → Similar to: Piranesi

     A warm, whimsical story about a caseworker who
     discovers a secret island where magical children
     live. If you loved the gentle wonder of Piranesi,
     this will wrap you in the same feeling.

     🎯 Perfect for a cozy evening when you want
     joy and heart with a side of magic.
```

---

## API

Bookmatch uses **OpenRouter** to access LLMs. Set your key:

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

Or it'll auto-detect the key from the Hermes environment.

---

## File Structure

```
bookmatch/
├── bookmatch/          # Package directory
│   └── main.py         # CLI entry point + all logic
├── Decisions.md        # Architecture decisions (15 entries)
├── Flow.md             # Execution trace + data flow
├── requirements.txt    # Dependencies (just httpx!)
└── README.md           # This file
```

---

## Why Bookmatch?

- **No more browsing paralysis** — staring at "1,000+ results" helps no one
- **Not an algorithm** — no "people who bought X also bought Y" cold calculation
- **Understands your mood** — book recommendations should match how you feel, not just what you read last
- **Real books** — no hallucinated titles (prompt-engineered against it)

---

Built for the **AI Apps** rota category. Part of the LLM-Apps daily build pipeline.