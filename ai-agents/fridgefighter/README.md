# 🥊 FridgeFighter — Gamify Your Fridge Before the Food Goes Bad

> *Snap a photo of your fridge. AI identifies every item and its expiry. Get daily challenges to use expiring food. Earn badges for your zero-waste streak.*

**FridgeFighter** turns food waste into a game. Take a photo of your fridge → the AI recognizes your items and estimates expiry → you get a daily challenge ("Use 3 items expiring in 48 hours — bonus points if you combine them in one meal!") → track your waste-free streak and earn badges.

## Usage

```bash
# Simulated mode (no camera needed)
python main.py --simulate

# Take a photo and scan
python main.py --scan

# View your current streak and badges
python main.py --status

# Record that you used an item
python main.py --use "broccoli"
```

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
python main.py --simulate
```

## Features

- **Smart Scan** — Simulated vision identifies items and estimates expiry dates
- **Daily Challenges** — "Use 3 items before they expire this weekend" with bonus combos
- **Zero-Waste Streak** — Track consecutive waste-free days
- **Badges** — Earn badges like "7-Day Streak", "Sous Chef" (5 items used in a day), "Combo Master" (bonus challenges completed)
- **Inventory Management** — Add, remove, and track your fridge contents

## Testing

```bash
pytest tests/ -v
```

## Tech Stack

- Python · Pillow · httpx · Pydantic
- Simulated vision for zero-config dev
- Challenge engine generates creative daily tasks
- Streak + badge system for gamification