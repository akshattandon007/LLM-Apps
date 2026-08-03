# TextPersona 🎭

> **Your message, their voice.** Type something normal. Get it back as Yoda, a pirate, Shakespeare, a valley girl, or seven other gloriously distinct characters.

---

## What is this?

TextPersona is a tiny, playful web app that rewrites your text in character. You type a message, pick a persona, and an AI (via OpenRouter) transforms it — keeping your meaning but swapping the voice entirely.

Perfect for:
- Spicing up group chats
- Writing character dialogue for fun
- Seeing how "circle back on that synergy" sounds coming from a caveman
- Procrastinating productively

---

## Meet the Cast (10 Personas)

| Persona | Vibe | Sample Tagline |
|---------|------|----------------|
| 🧙 **Yoda** | Inverted syntax, cryptic wisdom | "Speak like the Jedi Master" |
| ⚔️ **Medieval Knight** | Thee/thou, chivalric flourish | "Hark, thy words shall be noble!" |
| 🏴‍☠️ **Pirate** | Arrr, matey, nautical slang | "Arrr, talk like a buccaneer!" |
| 💁‍♀️ **Valley Girl** | Like, totally, omg, gag me | "Like, totally transform your text!" |
| 🎭 **Shakespeare** | Iambic pentameter, dramatic flair | "Hark! Thy words become poetry!" |
| 👵 **Southern Grandma** | Bless your heart, honey, fixin' to | "Bless your heart, sugar!" |
| 🎖️ **Drill Sergeant** | ALL CAPS, MAGGOT, military bark | "DROP AND GIVE ME 20 WORDS!" |
| 🤖 **Corporate Bot** | Synergy, bandwidth, circle back | "Let's circle back on that synergy." |
| 🦴 **Caveman** | Primitive, grunts, third-person | "Me talk simple. You like." |
| 🧘 **Therapist** | Validating, reframing, warm | "And how does that make you feel?" |

**🎲 Surprise Me** — Feeling indecisive? Roll the dice for a random persona.

---

## Features

- **Instant AI rewrites** via OpenRouter (OpenAI-compatible API, GPT-4o-mini)
- **Dark/light mode** with system-preference detection and manual toggle
- **History sidebar** — your last 50 rewrites saved locally (localStorage, no server)
- **Copy & Share** buttons on every result (native Web Share API where supported)
- **Mobile-first responsive design** — works great on phone, tablet, desktop
- **Zero external runtime deps** — just Next.js, React, Tailwind v4, daisyUI v5
- **TypeScript strict mode** — catches bugs before you ship

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Framework | **Next.js 16** (Pages Router) |
| UI | **React 19**, **Tailwind CSS v4**, **daisyUI v5** |
| Language | **TypeScript** (strict) |
| AI Backend | **OpenRouter** (OpenAI-compatible) — model: `openai/gpt-4o-mini` |
| Storage | **localStorage** (client-side only) |
| Build | **Turbopack** (via `next dev`) |

---

## Quick Start

### Prerequisites

- **Node.js 20+**
- **OpenRouter API key** — get one free at [openrouter.ai/keys](https://openrouter.ai/keys)

### Local Development

```bash
# 1. Enter the project
cd /tmp/LLM-Apps/ai-agents/text-persona

# 2. Install dependencies
npm install

# 3. Add your OpenRouter key
echo "OPENROUTER_API_KEY=sk-or-your-key-here" > .env

# 4. Start the dev server (Turbopack enabled)
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and start rewriting!

### Production Build

```bash
npm run build   # Creates optimized production bundle
npm start       # Runs production server
```

---

## Project Structure

```
text-persona/
├── src/
│   ├── pages/
│   │   ├── index.tsx          # Main page — all client state lives here
│   │   ├── api/rewrite.ts     # POST /api/rewrite → calls OpenRouter
│   │   ├── _app.tsx           # App wrapper (imports global styles)
│   │   └── _document.tsx      # HTML document (auto-generated)
│   ├── components/
│   │   ├── MessageInput.tsx   # Textarea + char counter + clear
│   │   ├── PersonaGrid.tsx    # 5-col responsive grid + Surprise Me
│   │   ├── PersonaCard.tsx    # Clickable persona card (animated)
│   │   ├── RewriteOutput.tsx  # Result card: original → rewritten, copy/share
│   │   ├── HistorySidebar.tsx # Slide-out panel (mobile overlay + desktop drawer)
│   │   └── DarkModeToggle.tsx # ☀️/🌙 toggle with localStorage persistence
│   ├── lib/
│   │   ├── personas.ts        # 10 Persona definitions + system prompts
│   │   └── history.ts         # localStorage helpers (load/save/clear/id)
│   └── styles/
│       └── globals.css        # Tailwind v4 + daisyUI + custom animations
├── .env                       # Your OPENROUTER_API_KEY (gitignored)
├── package.json
├── tsconfig.json              # Strict TS, path aliases (@/* → src/*)
└── README.md                  # You are here
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | **Yes** | Your OpenRouter API key (format: `sk-or-...`) |

Create `.env` in the project root:
```
OPENROUTER_API_KEY=sk-or-your-actual-key
```

> ⚠️ **Never commit your `.env` file.** It's in `.gitignore` for a reason.

---

## How It Works (30-Second Version)

1. **You type** a message (max 500 chars)
2. **You click** a persona card (or 🎲 Surprise Me)
3. **Frontend POSTs** to `/api/rewrite` with `{ message, systemPrompt }`
4. **API route** calls OpenRouter with the persona's system prompt + your message
5. **OpenRouter** returns the rewritten text (GPT-4o-mini, temp 0.9, max 300 tokens)
6. **Frontend** displays original → rewritten, saves to history, enables copy/share

---

## Customizing Personas

Edit `src/lib/personas.ts`. Each persona needs:

```ts
{
  id: 'unique-id',           // URL-safe, used in history
  name: 'Display Name',      // Shown in UI
  emoji: '🎭',               // Single emoji (renders in cards)
  tagline: 'Short blurb',    // Subtitle in persona grid
  systemPrompt: '...'        // The actual LLM instruction
}
```

**Prompt design tips:**
- End with `Output ONLY the rewritten message, no preamble or quotes.`
- Be specific about vocabulary, syntax quirks, and tone
- Keep prompts under ~500 tokens for speed/cost

---

## License

MIT — do whatever you want, but if you add a **Gandalf** persona, PR it upstream. 🧙‍♂️

---

*Made with ☕ and a questionable number of persona prompts.*