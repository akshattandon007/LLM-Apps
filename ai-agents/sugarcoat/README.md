# 🍬 sugarcoat — AI Message Diplomat

**Say the hard thing, kindly.**

sugarcoat is a CLI tool that helps you rephrase difficult messages — breaking bad news, declining invitations, giving feedback, apologizing, or setting boundaries — in a tone that's **kind, clear, and effective**.

No more lying awake at 2 AM replaying that text you should have written differently.

## ✨ Features

- 🎭 **6 tone options** — gentle, empathetic, professional, assertive, warm, neutral
- 📝 **6 style options** — diplomatic, direct, apologetic, encouraging, concise, detailed
- 💡 **Explanations** — learn *why* the rephrased version works better
- 🔄 **Alternatives** — get 1-2 shorter phrasings for different situations
- 📋 **History-aware** — pass conversation context for smarter rephrasing
- 🎯 **No API key needed to start** — uses OpenRouter (free tier available)

## 🚀 Quick Start

```bash
# Install
pip install -r requirements.txt

# Rephrase a message
python3 sugarcoat.py "I can't come to your wedding" --style apologetic

# With context
python3 sugarcoat.py "Your presentation was confusing" \
  --tone empathetic \
  --style diplomatic \
  --context "A junior colleague who worked really hard on this"

# Interactive mode
python3 sugarcoat.py -i

# List available options
python3 sugarcoat.py --list-tones
python3 sugarcoat.py --list-styles
```

## 📋 Usage

```
usage: sugarcoat [-h] [-t {gentle,empathetic,professional,assertive,warm,neutral}]
                 [-s {diplomatic,direct,apologetic,encouraging,concise,detailed}]
                 [--context CONTEXT] [--api-key API_KEY] [--model MODEL]
                 [--list-tones] [--list-styles] [-i] [--history HISTORY]
                 [message]
```

### Examples

**Declining an invitation (apologetic):**
```bash
$ sugarcoat "I can't come" --style apologetic --context "Close friend's wedding"
```
> 💬 *"I'm so sorry, but I won't be able to make it to your wedding. I'm absolutely gutted to miss it — you know I wouldn't skip this for anything. I'll be thinking of you on the day and can't wait to celebrate with you after!"*

**Giving feedback (assertive + professional):**
```bash
$ sugarcoat "You're late again" --tone assertive --style professional --context "Team member, third time this month"
```
> 💬 *"I've noticed this is the third time this month you've arrived late to our morning standup. Going forward, I need you to be on time so we can start as a team. If something's preventing that, let's talk about it."*

**Setting a boundary (warm + direct):**
```bash
$ sugarcoat "Stop texting me at midnight" --tone warm --style direct
```
> 💬 *"I love hearing from you, but late-night messages wake me up. Could we save chats for daytime? I'll get back to you first thing!"*

## 🔧 Configuration

Set your OpenRouter API key (free at [openrouter.ai](https://openrouter.ai)):

```bash
export OPENROUTER_API_KEY="sk-or-..."
```

Or create a `.env` file:
```
OPENROUTER_API_KEY=sk-or-...
```

## 🧪 Tests

```bash
# Install test deps
pip install pytest httpx

# Run tests
pytest tests/ -v
```

## 🏗️ Architecture

```
sugarcoat/
├── sugarcoat.py          # CLI entry point — argument parsing, user interaction
├── sugarcoat_engine.py   # LLM interaction — prompt building, API calling, response parsing
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── Decisions.md          # Architecture decisions
├── Flow.md               # Execution flow diagram
└── tests/
    └── test_sugarcoat.py # Unit tests (mocked API)
```

## 📜 License

MIT — use it, share it, soften your messages with it.