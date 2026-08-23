# 📸 Photo Time Machine — See Yourself Through the Decades

> *Upload a selfie, see yourself across every era — from the 1950s to the 2050s.*

**Photo Time Machine** takes your photo and transforms it through 6 historical/future eras: 1950s greaser, 1970s disco, 1990s grunge, 2000s Y2K, 2025 present, and 2050s cyberpunk. Each era gets period-accurate styling descriptions, visual filters, and a playful caption. Perfect for social media shares and group chat fun.

## Eras

| Decade | Style | Vibe |
|--------|-------|------|
| 🎸 1950s | Poodle skirts, greaser, black & white | *Rock around the clock* |
| 🕺 1970s | Disco, bell-bottoms, afros, sepia | *Stayin' Alive* |
| 🎸 1990s | Grunge, frosted tips, scrunchies | *Smells Like Teen Spirit* |
| 📱 2000s | Low-rise, frosted, digital flash | *Bye Bye Bye* |
| 👤 2025 | Natural, current | *As you are today* |
| 🤖 2050s | Cyberpunk, neon, holographic | *Beyond 2025* |

## Usage

```bash
# Simulated demo (no photo needed)
python main.py --simulate

# With a real photo
python main.py --upload my_selfie.jpg

# Generate all eras at once
python main.py --upload photo.jpg --all
```

## Quick Start

```bash
pip install -r requirements.txt
python main.py --simulate
```

## Features

- **6 Eras** — 1950s → 2050s with distinct styles
- **Playful Captions** — Era-appropriate taglines for each decade
- **Gallery View** — See all eras side-by-side
- **Visual Filters** — Black & white, sepia, cool-blue, digital flash, natural, neon
- **Simulated Mode** — Works without image gen APIs

## Testing

```bash
pytest tests/ -v
```