<![CDATA[<div align="center">

# 🐴 Professor Bray-niac

### AI-Powered Tutorial Builder Agent

*A Duolingo-inspired animated donkey teacher that explains programming concepts with real-world examples, code, jokes, and text-to-speech audio.*

**Powered by Claude Opus 4.6 · React · SVG Animation · Web Speech API**

![Version](https://img.shields.io/badge/version-1.0.0-green)
![License](https://img.shields.io/badge/license-MIT-blue)
![React](https://img.shields.io/badge/React-18.2-61dafb)
![Claude](https://img.shields.io/badge/Claude-Opus%204.6-orange)

</div>

---

## 🎬 What Does This Agent Do?

Professor Bray-niac is a **tutorial builder agent** that transforms any programming concept into an animated, narrated micro-lesson. You type a concept (e.g., *"What is a class in Python?"*), and the agent:

1. **Sends your concept** to Claude Opus 4.6 with a structured persona prompt
2. **Receives a JSON-structured tutorial** with 5-6 slides, each containing speech, whiteboard content, a joke, and an expression state
3. **Plays it back as an animated lesson** featuring a Duolingo-style donkey character who speaks aloud (TTS), writes on a whiteboard, and cracks terrible programming puns

The entire experience runs in the browser — no backend required beyond the Claude API.

---

## 🖼️ Visual Walkthrough

### Screen 1: Input Screen
```
┌──────────────────────────────────────────────┐
│         🎓 TUTORIAL BUILDER AGENT            │
│         Professor Bray-niac                  │
│                                              │
│          ┌──────────────────┐                │
│          │   🐴 ANIMATED    │                │
│          │   DONKEY WITH    │                │
│          │   FLOATING IDLE  │                │
│          │   ANIMATION      │                │
│          └──────────────────┘                │
│                                              │
│  ┌─────────────────────────────────────────┐ │
│  │ "HEE-HAW! Type any concept and I'll    │ │
│  │  teach it with examples and puns!" 🐴   │ │
│  └─────────────────────────────────────────┘ │
│                                              │
│  WHAT DO YOU WANT TO LEARN?        12/150    │
│  ┌─────────────────────────────────────────┐ │
│  │ What is a class in Python?              │ │
│  └─────────────────────────────────────────┘ │
│                                              │
│  🔊 Audio ON              🎬 Generate Tutorial│
│                                              │
│  Try these:                                  │
│  [Recursion] [Decorators] [APIs] [Dict]      │
└──────────────────────────────────────────────┘
```

**Features visible:**
- Animated donkey with idle breathing, blinking, and ear wiggle
- Word counter (max 150)
- Audio toggle (TTS on/off)
- Quick-pick example topic pills
- Green Duolingo-inspired colour scheme

---

### Screen 2: Loading State
```
┌──────────────────────────────────────────────┐
│                                              │
│          ┌──────────────────┐                │
│          │   🐴 DONKEY IN   │                │
│          │   THINKING POSE  │                │
│          │   (pupils up,    │                │
│          │   hoof on chin)  │                │
│          └──────────────────┘                │
│                                              │
│        🤔 Thinking of perfect puns...        │
│              ● ● ●                           │
│          (bouncing dots)                     │
│                                              │
└──────────────────────────────────────────────┘
```

**Features visible:**
- Donkey in `thinking` expression with animated mouth
- Rotating loading messages (6 variants)
- Bouncing dot loader

---

### Screen 3: Video Player (Tutorial Playback)
```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  ┌──────────────────┐  ┌───────────────────────────────┐ │
│  │ ╭─────────────╮  │  │ ┌─────────────────────────┐   │ │
│  │ │ Speech text  │  │  │ │  📘 Python Classes      │   │ │
│  │ │ from donkey  │  │  │ │                         │   │ │
│  │ ╰──────┬───────╯  │  │ │  Think of a class as a  │   │ │
│  │        │          │  │ │  COOKIE CUTTER:          │   │ │
│  │  ┌─────┴────┐     │  │ │                         │   │ │
│  │  │ 🐴 DONKEY │     │  │ │  class Dog:             │   │ │
│  │  │ SPEAKING  │     │  │ │    def __init__(self):   │   │ │
│  │  │ (mouth    │     │  │ │      self.name = name    │   │ │
│  │  │  moving)  │     │  │ │                    █     │   │ │
│  │  └──────────┘     │  │ │                         │   │ │
│  │  ╭────────────╮   │  │ └─────────────────────────┘   │ │
│  │  │ 🤣 Joke!   │   │  │   ┌─────────────────────┐    │ │
│  │  │ "Why do    │   │  │   │chalk pieces on tray  │    │ │
│  │  │  donkeys   │   │  │   └─────────────────────┘    │ │
│  │  │  love OOP?│   │  │                               │ │
│  │  ╰───────────╯   │  │     ● ● ●━━ ● ● ●            │ │
│  └──────────────────┘  └───────────────────────────────┘ │
│                                                          │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  3/6  ━━━━━━━━━━━━━━━░░░░░░░░░                      │ │
│  │           ⏮   ▶️   🔊   ✕                           │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                          │
│  Topic: What is a class in Python?                       │
└──────────────────────────────────────────────────────────┘
```

**Features visible:**
- **Left:** Donkey with active expression + speech bubble + joke bubble
- **Right:** Whiteboard with typewriter-animated text and cursor
- **Bottom:** Progress bar, slide counter, playback controls
- Slide navigation dots (clickable when paused)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      USER INPUT                         │
│              "What is a class in Python?"               │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                 CLAUDE OPUS 4.6 API                     │
│                                                         │
│  System Prompt: Professor Bray-niac persona             │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Forces structured JSON output:                    │  │
│  │ {                                                 │  │
│  │   title: "Python Classes",                        │  │
│  │   slides: [                                       │  │
│  │     {                                             │  │
│  │       speech: "What Bray-niac says aloud",        │  │
│  │       whiteboard: "Text/code on the board",       │  │
│  │       joke: "A donkey programming pun",           │  │
│  │       expression: "excited|thinking|joke|..."     │  │
│  │     }, ...                                        │  │
│  │   ]                                               │  │
│  │ }                                                 │  │
│  └───────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  PLAYBACK ENGINE                        │
│                                                         │
│  For each slide:                                        │
│                                                         │
│  ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌──────┐ │
│  │ Phase 1 │──▶│ Phase 2  │──▶│ Phase 3  │──▶│ Next │ │
│  │ SPEECH  │   │ TYPING   │   │  JOKE    │   │Slide │ │
│  │         │   │          │   │          │   │      │ │
│  │ TTS     │   │ Typewrite│   │ TTS      │   │      │ │
│  │ speaks  │   │ on board │   │ speaks   │   │      │ │
│  │ + mouth │   │ @ 30ms/  │   │ + mouth  │   │      │ │
│  │ animate │   │ char     │   │ animate  │   │      │ │
│  └─────────┘   └──────────┘   └──────────┘   └──────┘ │
└─────────────────────────────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
┌──────────────┐ ┌───────────┐ ┌──────────────┐
│   DONKEY     │ │WHITEBOARD │ │   TTS        │
│   SVG        │ │           │ │   AUDIO      │
│              │ │ Typewriter│ │              │
│ Spring       │ │ cursor    │ │ Speech-      │
│ physics on:  │ │ reveals   │ │ Synthesis    │
│ • Eyes       │ │ text line │ │ API with     │
│ • Eyebrows   │ │ by line   │ │ mouth shape  │
│ • Body       │ │           │ │ cycling      │
│ • Ears       │ │           │ │ (6 visemes)  │
│ • Blush      │ │           │ │              │
│              │ │           │ │              │
│ Auto-blink   │ │           │ │              │
│ Idle breathe │ │           │ │              │
│ 5 expression │ │           │ │              │
│ states       │ │           │ │              │
└──────────────┘ └───────────┘ └──────────────┘
```

---

## 🐴 The Donkey: Animation System

### Expressions

Professor Bray-niac has **5 expression states**, each with spring-animated transitions:

| Expression | Eye Scale | Brow | Body | Ears | Blush | When Used |
|---|---|---|---|---|---|---|
| `idle` | 1.0x | neutral | normal | relaxed | none | Default state |
| `excited` | 1.3x | raised | squished | perked up | pink | Key concepts, greetings |
| `thinking` | 0.9x | furrowed | tall | tilted | none | Analogies, chin-touch pose |
| `joke` | 1.15x | raised | bouncy | perked | light | Delivering punchlines |
| `celebrating` | 1.4x | high | bouncing | way up | full | Tutorial complete! |

### Idle Animation Loops
The donkey is **never static**. At all times:
- **Breathing:** Gentle body rise/fall at 2Hz
- **Head bob:** Subtle nod at 1.8Hz
- **Ear wiggle:** Independent ear movement at 2.5Hz
- **Tail sway:** Physics-driven wag
- **Auto-blink:** Random interval (2-6 seconds)
- **Pupil tracking:** Subtle eye movement following a sine path

### Lip Sync (Viseme System)
6 mouth shapes cycle during TTS speech at 110ms intervals:

| Shape | Name | Visual |
|---|---|---|
| 0 | Closed | Thin line |
| 1 | Slight open | Small oval |
| 2 | Open (ah) | Large oval + teeth |
| 3 | Wide (ee) | Horizontal stretch |
| 4 | Round (oh) | Vertical oval |
| 5 | Smile | Curved grin |

### Accessories
- 🎓 **Graduation cap** with physics-driven tassel swing
- 👓 **Round glasses** with lens shine highlights
- 🎀 **Red bow tie** with 3D shading

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** 18+ ([download](https://nodejs.org/))
- **npm** or **yarn**
- A **Claude API key** (for running locally — not needed when used as a Claude.ai artifact)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/akshattandon007/professor-brayniac-tutorial-agent.git
cd professor-brayniac-tutorial-agent

# 2. Install dependencies
npm install

# 3. Start the development server
npm run dev
```

The app will open at **http://localhost:3000**.

### Running as a Claude.ai Artifact

This project was designed as a Claude.ai artifact — the API calls are proxied through Claude's built-in API access. To use it:

1. Copy the contents of `src/` into a single `.jsx` artifact file
2. The prebuilt single-file version is available at `tutorial-builder-agent.jsx` in the outputs
3. No API key needed — Claude.ai handles authentication

### Running Locally with Your Own API Key

If you want to run it outside Claude.ai, you'll need to add your API key. Modify `src/config/prompt.js`:

```js
// Add your API key to the headers
const response = await fetch(API_URL, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-api-key': 'YOUR_ANTHROPIC_API_KEY',       // ← add this
    'anthropic-version': '2023-06-01',            // ← add this
  },
  body: JSON.stringify({ ... }),
});
```

> ⚠️ **Never commit API keys to version control.** Use environment variables:
> ```js
> 'x-api-key': import.meta.env.VITE_ANTHROPIC_API_KEY
> ```
> Then create a `.env.local` file:
> ```
> VITE_ANTHROPIC_API_KEY=sk-ant-...
> ```

### Build for Production

```bash
npm run build    # outputs to dist/
npm run preview  # preview the production build
```

---

## 📁 Project Structure

```
professor-brayniac-tutorial-agent/
│
├── index.html                  # HTML entry point
├── package.json                # Dependencies & scripts
├── vite.config.js              # Vite build config
├── LICENSE                     # MIT License
├── .gitignore
│
├── src/
│   ├── main.jsx                # React DOM entry
│   ├── index.css               # Global styles & animations
│   ├── App.jsx                 # Main orchestrator component
│   │
│   ├── components/
│   │   ├── DonkeyCharacter.jsx # Animated SVG donkey (280 lines)
│   │   ├── SpeechBubble.jsx    # Spring-animated speech bubbles
│   │   └── Whiteboard.jsx      # Typewriter whiteboard
│   │
│   ├── hooks/
│   │   ├── useSpring.js        # Spring physics animation hook
│   │   └── useTTS.js           # Text-to-Speech with mouth sync
│   │
│   └── config/
│       └── prompt.js           # Claude API config & system prompt
│
└── docs/
    └── screenshots/            # Documentation images
```

---

## 🔧 How It Works (Technical Deep Dive)

### 1. Concept Input → Claude API
When the user types a concept and clicks "Generate Tutorial", the app sends it to Claude Opus 4.6 with a system prompt that:
- Forces a specific JSON schema (no markdown, no backticks)
- Defines Professor Bray-niac's personality and teaching style
- Specifies exactly 5-6 slides with expression states
- Requires real-world analogies before code examples
- Mandates a joke on every slide

### 2. Structured Response
Claude returns structured JSON like:
```json
{
  "title": "Python Classes: Your Blueprint Factory!",
  "slides": [
    {
      "speech": "HEE-HAW! Welcome class! I'm Professor Bray-niac, and today we're going to learn about Python classes!",
      "whiteboard": "What is a Class?\n\nA class is a BLUEPRINT\nfor creating objects.\n\nLike a cookie cutter\nmakes cookies!",
      "joke": "Why did the donkey take a Python class? Because he wanted to be a little less ass-inine!",
      "expression": "excited"
    }
  ]
}
```

### 3. Playback Engine
The async playback engine processes each slide in 3 phases:
- **Phase 1 (Speech):** TTS reads the speech text while the donkey's mouth animates
- **Phase 2 (Typing):** Whiteboard text appears character-by-character at 30ms intervals
- **Phase 3 (Joke):** Joke bubble appears, TTS reads it, expression changes to `joke`

### 4. Animation System
- **Spring Physics** (`useSpring` hook): All expression transitions use physically-based spring dynamics with configurable stiffness and damping
- **Auto-Blink**: Random interval blink system (2-6s) with 150ms blink duration
- **Viseme Cycling**: 6 mouth shapes cycle at 110ms during TTS speech, creating a lip-sync illusion
- **Idle Loops**: Breathing, head bob, ear wiggle, and tail sway run continuously via `requestAnimationFrame`

---

## 🎯 Design Decisions

| Decision | Rationale |
|---|---|
| **SVG character** (not image/canvas) | Infinitely scalable, style-able, fast to render, no external assets |
| **Spring physics** (not CSS transitions) | Organic, bouncy feel matching Duolingo's animation philosophy |
| **Web Speech API** (not external TTS) | Zero-dependency, works offline, no API costs, runs in browser |
| **Single-file artifact** + **modular repo** | Works both as Claude.ai artifact AND standalone project |
| **JSON prompt schema** | Forces structured output; eliminates parsing ambiguity |
| **5-6 slides** | Sweet spot for ~90 second tutorials (under 2 min target) |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18 + Vite 5 |
| **Character** | Hand-crafted SVG with spring physics |
| **Audio** | Web Speech API (SpeechSynthesis) |
| **AI** | Claude Opus 4.6 (`claude-opus-4-6-20250619`) |
| **Styling** | CSS-in-JS (inline styles) + Google Fonts |
| **Fonts** | Nunito (UI), Caveat (whiteboard handwriting) |

---

## 📝 Customisation

### Change the character name
Edit `SYSTEM_PROMPT` in `src/config/prompt.js` — replace all "Professor Bray-niac" references.

### Adjust animation speed
- Speech rate: `useTTS.js` → `utterance.rate` (default: 0.92)
- Typing speed: `App.jsx` → typing interval (default: 30ms/char)
- Mouth cycle: `useTTS.js` → `MOUTH_CYCLE_MS` (default: 110ms)

### Add more expressions
1. Add a new entry to `EXPRESSIONS` in `DonkeyCharacter.jsx`
2. Add the expression name to the system prompt's valid values
3. Add expression-specific SVG elements (like the thinking chin-touch)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with 🐴 and terrible puns by [Akshat Tandon](https://github.com/akshattandon007)**

*Professor Bray-niac © HEE-HAW Industries*

</div>
]]>