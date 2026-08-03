# TextPersona 🎭

An AI-powered message rewriter. Type a normal message, pick a character persona (Yoda, Pirate, Shakespeare, Valley Girl, and more), and get an instant AI rewrite that preserves the original meaning while transforming the voice.

## Features

- **10 unique personas** — Yoda, Medieval Knight, Pirate, Valley Girl, Shakespeare, Southern Grandma, Drill Sergeant, Corporate Bot, Caveman, Therapist
- **Instant AI rewrites** via OpenRouter (OpenAI-compatible API)
- **Dark mode** with toggle, respecting system preference
- **History sidebar** — recent rewrites stored in localStorage
- **Copy & Share** buttons on every rewrite
- **Surprise Me** button for random persona selection
- **Mobile-first** responsive design
- Zero external dependencies beyond Next.js + React + Tailwind + daisyUI

## Tech Stack

- **Next.js 16** (pages router)
- **React 19**
- **TypeScript**
- **Tailwind CSS v4** + **daisyUI v5**
- **OpenRouter API** (OpenAI-compatible)

## Getting Started

### Prerequisites

- Node.js 20+
- An OpenRouter API key (get one at [openrouter.ai/keys](https://openrouter.ai/keys))

### Setup

```bash
# Clone and enter the project
cd text-persona

# Install dependencies
npm install

# Create environment file
echo "OPENROUTER_API_KEY=sk-or-v1-your-key-here" > .env

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and start rewriting!

### Production Build

```bash
npm run build
npm start
```

## Project Structure

```
src/
  pages/
    index.tsx          — Main page with all state management
    api/rewrite.ts     — API route calling OpenRouter
    _app.tsx           — App wrapper
    _document.tsx      — HTML document
  components/
    PersonaCard.tsx    — Individual persona selection card
    PersonaGrid.tsx    — Grid of persona cards + Surprise Me
    MessageInput.tsx   — Text input area
    RewriteOutput.tsx  — Rewritten output with copy/share
    HistorySidebar.tsx — Slide-out history panel
    DarkModeToggle.tsx — Light/dark toggle
  lib/
    personas.ts        — Persona definitions and prompts
    history.ts         — localStorage history helpers
  styles/
    globals.css        — Tailwind + daisyUI + animations
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | Yes | Your OpenRouter API key |

## License

MIT
