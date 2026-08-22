# 🪞 Echo — Conversation Mindfulness Tool

> *What if every conversation left you a little wiser about yourself?*

**Echo** analyzes conversation transcripts and produces a playful "mirror report" — insights about who talked most, filler words, energy peaks, repeated phrases, and turn-taking patterns. Makes you a better conversationalist without being preachy.

## Usage

```bash
# Paste a transcript (format: "Speaker: text")
python main.py --transcript "Alice: That's a great point
Bob: Actually, I think we should consider..."

# Or let Echo analyze itself
echo "Alice: That's a great point. Bob: Actually, what if we try something different? Alice: I like that idea — it's exactly what we need!" | python main.py -

# Simulated demo
python main.py --simulate
```

## Features

| Feature | What it finds |
|---------|---------------|
| **Talk Ratio** | Who dominated? Percentages per speaker |
| **Filler Words** | "actually", "like", "you know", "um", "literally" |
| **Energy Peaks** | Excited moments by punctuation + enthusiasm markers |
| **Repeated Phrases** | 2-3 word phrases a speaker leans on |
| **Turn Analysis** | Interruptions, gaps, longest/shortest statements |
| **Mirror Report** | Playful, non-preachy takeaway in markdown |

## Quick Start

```bash
pip install -r requirements.txt
python main.py --simulate
```

## Testing

```bash
pytest tests/ -v
```

## Tech Stack

- Python · pydantic
- Full local analysis — no API keys needed
- 5 report modules: analyzer, patterns, reporter
- 15 smoke tests covering edge cases