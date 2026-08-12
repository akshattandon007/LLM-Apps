# 🎤 VoiceVault — Your Loved One's Voice, Forever

> *"What was your first car?" · "How did you meet grandma?" · "What's your earliest memory of me?"*  
> **Ask anything. They answer in their voice.**

---

## 💛 What is this?

VoiceVault is an **interactive audio keepsake** — a way to keep someone's voice alive.

You record 30–60 second voice samples from a loved one (a grandparent, a parent, a partner). Then you type questions about their life, and VoiceVault answers in **their voice**, drawn from the stories they told you.

Not text. Not an AI impersonation. **Their voice.** Saying the things they'd say.

---

## 🪄 How it works

It's three steps:

### 1️⃣ Record 🎙️
Capture 3–5 short stories (30–60 seconds each) from someone you love. Give each one a short caption so VoiceVault knows what it's about — *"First time they rode a motorcycle"*, *"How they proposed"*, *"The family dog they had as a kid"*.

### 2️⃣ Ask ❓
Type any question about their life:
- *"What was your first job?"*
- *"What was I like as a baby?"*
- *"What's one thing you've never told anyone?"*

### 3️⃣ Listen 🎧
VoiceVault finds the story that best matches your question, generates a warm spoken response, and delivers it in **their cloned voice**. It's them. Talking to you. Right now.

---

## ✨ Features

| Feature | What it does |
|---|---|
| 🎙️ **Voice Recording** | Record straight from your browser via Web Audio API |
| ❓ **Intelligent Q&A** | Type any life question; VoiceVault picks the right story and crafts a spoken answer |
| 👤 **Voice Profiles** | Keep multiple people — each with their own recordings, voice clone, and story library |
| 🗂️ **Story Library** | Browse every recording you've captured, replay anytime |
| 📤 **Share** | Point someone at your VoiceVault page and let them ask their own questions |

---

## 🛠️ Setup

```bash
# 1. Clone and install
cd ai-agents/voice-vault
npm install

# 2. Set up your environment
cp .env.example .env.local
```

### Required keys

| Variable | Where to get it |
|---|---|
| `ELEVENLABS_API_KEY` | [elevenlabs.io](https://elevenlabs.io) — for voice cloning + TTS |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) — for story matching |

Then:

```bash
# 3. Run!
npm run dev
```

Open **[http://localhost:3000](http://localhost:3000)** and start recording.

---

## 🧰 Tech stack

| Layer | What |
|---|---|
| 🖥️ **Framework** | Next.js 16 (Pages Router) + TypeScript |
| 🎨 **UI** | Tailwind CSS v4 + DaisyUI 5 (warm custom themes) |
| 🗣️ **Voice** | ElevenLabs API — instant voice cloning + text-to-speech |
| 🧠 **LLM** | Anthropic / Claude — story matching + response generation |
| 💾 **Storage** | localStorage (all data stays on your device — v1 constraint) |

---

## ⚠️ v1 caveats

- **localStorage cap** — audio is stored as base64 data URLs (~5MB limit). Keep recordings short (30–60s). If you record too much, the oldest stories get dropped.
- **Same-device only** — your data lives in your browser. Clear localStorage or switch machines and you start over.
- **Paid ElevenLabs plan required** for instant voice cloning. If cloning fails, the app falls back to a premade voice (Rachel) so Q&A still works.
- **Caption-based matching** — v1 matches questions against your captions, not the audio content. Write good captions, get better answers.
- **No transcription** — the app doesn't transcribe recordings. Your captions are the story index.

---

## 📁 Project structure

```
ai-agents/voice-vault/
├── package.json
├── tsconfig.json
├── next.config.js
├── postcss.config.mjs
├── .env.example
├── .gitignore
├── src/
│   ├── styles/
│   │   └── globals.css
│   ├── pages/
│   │   ├── index.tsx
│   │   ├── record.tsx
│   │   ├── profile/[id].tsx
│   │   └── api/
│   │       ├── voice.ts
│   │       └── ask.ts
│   ├── components/
│   │   ├── VoiceRecorder.tsx
│   │   ├── AudioPlayer.tsx
│   │   ├── StoryCard.tsx
│   │   ├── ProfileCard.tsx
│   │   └── Layout.tsx
│   └── lib/
│       ├── store.ts
│       └── api.ts
```

---

*Built to keep voices alive. Record someone you love today.* 💛