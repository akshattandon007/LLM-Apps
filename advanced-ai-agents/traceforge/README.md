# TraceForge

A self-improving agent loop where good runs become reusable skills.

## What it does

TraceForge captures full execution traces from AI agent runs (prompts, tool calls, outputs, failures), lets you review and curate them, then uses an LLM-as-judge to extract reusable skills from successful traces. Over time, the agent gets observably better.

## Features

- **Dashboard** — list of all trace runs with status badges, timestamps, and agent metadata
- **Run Creator** — type a task, hit Run, and watch the agent process it via OpenRouter
- **Trace Viewer** — collapsible timeline showing every step: prompt, tool calls, outputs, reasoning, errors
- **Curation Mode** — mark traces as Good or Bad; good traces feed the skill forge
- **Skill Forge** — LLM-as-judge analyzes curated traces and extracts versioned skills with tool chains, decision logic, and safety verifiers
- **Skills Library** — grid of all extracted skills with full spec view

## Tech Stack

- Next.js 16 (Pages Router)
- TypeScript
- Tailwind CSS v4 + daisyUI
- OpenRouter API (OpenAI-compatible)
- localStorage for persistence

## Getting Started

```bash
# Install dependencies
npm install

# Set your OpenRouter API key
export OPENROUTER_API_KEY=sk-or-v1-...

# Run the dev server
npm run dev

# Build for production
npm run build
npm start
```

Open http://localhost:3000 in your browser.

## How it works

1. **Run a task** — type a task for the agent, which calls OpenRouter with function calling support
2. **Review the trace** — see every step the agent took in a collapsible timeline
3. **Curate** — mark traces as Good or Bad
4. **Analyze** — the LLM judge extracts reusable patterns from good traces
5. **Build skills** — extracted skills appear in the library with versioned specs

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | Your OpenRouter API key |

## Project Structure

```
src/
├── pages/
│   ├── index.tsx          # Main page
│   ├── _app.tsx           # App wrapper
│   └── api/
│       ├── agent.ts       # Agent execution endpoint
│       └── analyze.ts     # Skill extraction endpoint
├── components/
│   ├── Layout.tsx         # Header + dark mode toggle
│   ├── Dashboard.tsx      # Trace list
│   ├── RunCreator.tsx     # Task input + run
│   ├── TraceViewer.tsx    # Timeline viewer
│   └── SkillsLibrary.tsx  # Skill cards grid
├── lib/
│   └── storage.ts         # localStorage helpers
└── types.ts               # TypeScript types
```