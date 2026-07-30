# Grandma's Voice

# 👵🎙️✨ Bedtime Stories in Their Voice

> **"I made a story with Grandma's voice."**  
> *Forward this to someone who'd love to hear their voice tonight.*

---

## The Heart of It

Bedtime used to be simple. A lap. A book. A voice that knew every pause, every silly voice for every character, every *exactly right* pause before "the end."

Then life happened. Distance. Time zones. Bedtimes that don't align. A grandma in Florida, a grandpa in Manila, an auntie in London — and a child in pajamas asking, *"Can Grandma read to me tonight?"*

**Grandma's Voice bridges that distance.**

Record a 30-second voice sample. Pick a story genre. Get a 4-chapter illustrated bedtime story narrated in *their* voice — complete with emoji illustrations for each chapter, personalized with your child's name, ready to read aloud or share in the family group chat.

> The first time my daughter heard her grandmother's voice come out of my phone reading a story *about her*, she didn't just listen. She leaned into the phone like she was leaning into Grandma's shoulder. That's the moment this app exists for.

---

## ✨ What It Is

**Grandma's Voice** is a tiny web app that turns a 30-second voice recording into a personalized, illustrated 4-chapter bedtime story — narrated in the voice of someone your child loves.

**Who it's for:**
- 👵 Grandparents who live far away
- 👨‍👩‍👧 Parents traveling for work
- ✈️ Military families across time zones
- 🏥 Families navigating illness or separation
- 💔 Anyone who's ever missed bedtime

**What it makes:** A story card for each of 4 chapters — title, emoji illustration, the story text in quotation marks (as if spoken), and a gentle footer: *"— read in Grandma's voice 🎙️"*

---

## 🌈 Story Genres

| Genre | Vibe | Best For |
|-------|------|----------|
| 🏴‍☠️ **Adventure** | Pirate ships, hidden maps, daring escapes | Brave bedtime explorers |
| 🧚 **Fairytale** | Magic forests, talking animals, happy endings | Dreamers who believe in wonder |
| 🚀 **Space** | Rockets, friendly aliens, distant planets | Kids who stare at the moon |
| 🌊 **Ocean** | Mermaids, submarines, underwater kingdoms | Little mermaids & captains |
| 🤪 **Silly** | Giggly monsters, backwards days, noodle storms | The gigglers & wigglers |
| 🛌 **Cozy** | Warm blankets, sleepy bears, gentle lullabies | Wind-down nights, tired eyes |

Each genre has 4 hand-crafted chapters with custom emoji illustrations — like `🗺️✨🏚️` for a mysterious attic map, or `🐉🫧💜` for a lavender-bubble-breathing dragon.

---

## 🪄 How It Works (3 Steps)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   1. RECORD     │     │   2. CHOOSE     │     │   3. READ       │
│                 │     │                 │     │                 │
│  🎙️ 30 seconds  │ ──▶ │  📚 Pick genre  │ ──▶ │  📖 4 chapters  │
│  "Grandma"      │     │  Adventure,     │     │  🖼️ Illustrated │
│  "Abuela"       │     │  Cozy, Space... │     │  📋 Copy/Share  │
│  "Papa"         │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

1. **Record** — Enter the storyteller's name (Grandma, Abuelo, Auntie Mei, Papa...) and your child's name. Record ~30 seconds of them talking — reading a text, telling a memory, just saying "I love you."
2. **Choose** — Pick from 6 story genres. Each has a distinct vibe and hand-crafted 4-chapter arc.
3. **Read** — Get a beautiful story card for each chapter. Copy the full story. Share it in the family chat. Read it aloud tonight.

---

## 💝 Features for Families

- **🎙️ Voice-first** — The story *feels* like them because it's *in their voice*
- **👶 Personalized** — Child's name woven into every chapter
- **🖼️ Illustrated** — Each chapter has a unique emoji illustration (works everywhere, no images to load)
- **📋 Copy & Share** — One tap copies the full story to clipboard for the family group chat
- **🔄 Infinite stories** — Pick another genre, generate again, build a library
- **🏠 Works offline** — Once loaded, runs entirely in the browser (mock stories for now; voice clone API-ready)
- **💾 No accounts, no tracking** — Just open and make a memory

---

## 🛠️ Tech Stack

| Layer | Tech |
|-------|------|
| **Framework** | Next.js 16 (App Router) |
| **UI** | React 19 + Tailwind CSS 4 + DaisyUI 5 |
| **Language** | TypeScript 5 |
| **Styling** | Warm amber/rose gradients, card-based story layout, DaisyUI components |
| **State** | React hooks (no external state lib needed) |
| **Voice** | Browser MediaRecorder API (ready for ElevenLabs / PlayHT / OpenAI TTS integration) |
| **Deploy** | `npm run build && npm run start` — works on Vercel, Netlify, any Node host |

> **Architecture note:** The current build uses lovingly hand-crafted mock stories per genre. The voice recording is captured via `MediaRecorder` and the architecture is ready for a real voice-cloning TTS integration (ElevenLabs, PlayHT, OpenAI TTS, or local models like Coqui/XTTS). Swap the `handleGenerateStory` function to call your TTS API of choice.

---

## 🚀 Getting Started

```bash
# Clone and enter
cd grandmas-voice

# Install dependencies
npm install

# Start dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) — record a voice, pick a story, make a memory.

**Build for production:**
```bash
npm run build && npm run start
```

---

## 🛠️ Project Structure

```
grandmas-voice/
├── src/
│   ├── pages/
│   │   └── index.tsx       # The entire app — single-page flow
│   └── styles/
│       └── globals.css     # Tailwind + warm custom gradients
├── package.json
├── tsconfig.json
└── README.md               # ← you are here
```

---

## 💭 Why I Built This

I built this because I know what it's like to put a child to bed while the person they most want to hear is three time zones away.

My mom lives in another country. My daughter asks for her *every night*. FaceTime helps, but it's not a story. It's not a ritual. It's not something she can hold onto at 2 AM when she wakes up missing Nani.

So I built the smallest thing weekend I built this. Not a startup. Not a platform. A **tool for one bedtime** — that turned out to work for a lot of bedtimes.

**Stories bridge distance.**  
**Voices carry love.**  
**This app just makes it easy.**

If this makes one bedtime easier for your family, it was worth every minute.

---

## 💌 Share It

> **Forward this to someone who'd love to hear their person's voice tonight.**

```
Grandma's Voice — Bedtime stories in their voice
👵🎙️✨ grandmas-voice.vercel.app (or your deploy URL)
```

Send it to:
- Your sister who travels for work
- Your parents who miss the grandkids
- Your friend whose partner is deployed
- The family group chat with the note: *"Made this for [kid's name]. Try it tonight?"*

---

## 📄 License

MIT — Use it, fork it, build on it, share it.  
If you add real voice cloning, consider the ethics: **only clone voices with explicit, enthusiastic consent.** This app records locally and doesn't send audio anywhere unless *you* wire it up.

---

## 🙏 Acknowledgments

- **DaisyUI** — beautiful, accessible components that just work
- **Tailwind CSS** — for the warm gradients that feel like bedtime
- **Next.js team** — for making React feel like magic
- **Every grandparent who's read "Goodnight Moon" 400 times** — you're the real MVPs

---

<div align="center">

**Made with 💛 for bedtime everywhere**

*If this made your night, ⭐ the repo and share it with a family who needs it.*

</div>