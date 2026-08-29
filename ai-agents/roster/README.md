# 🔥 Roster — AI Group Photo Roaster

> *Upload a photo. Get roasted by AI. Best served cold with friends.*

**Roster** analyzes group photos — expression, outfit, vibe, arrangement — and generates comedy roasts. Pick your tone: **Siblings** (playful), **Coworkers** (polite but cutting), **Old Friends** (nostalgic jabs), or **Merciless** (no holds barred). Output is a shareable roast card.

## Roast Tones

| Tone | Vibe | Intensity |
|------|------|-----------|
| 👨‍👩‍👧‍👦 Siblings | *"You're adopted" energy — playful, affectionate | 4/10 |
| 💼 Coworkers | *"This meeting could've been an email" — polite but cutting | 6/10 |
| 🫂 Old Friends | *"Remember when you..." — nostalgic inside jabs | 5/10 |
| 💀 Merciless | *Read for filth — brutal, no holds barred | 9/10 |

## Usage

```bash
# Simulated demo with preset groups
python main.py --simulate

# Describe your own group
python main.py --roast --tone merciless --group "The Brunch Crew"

# List available tones
python main.py --list-tones
```

## Quick Start

```bash
pip install -r requirements.txt
python main.py --simulate
```

## Testing

```bash
pytest tests/ -v
```

## Project Files

| File | Purpose |
|------|---------|
| `Decisions.md` | Why every architectural choice was made |
| `Flow.md` | Execution trace through files and functions |
| `README.md` | Getting started guide |