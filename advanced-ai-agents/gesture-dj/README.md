# Gesture DJ 🎧

> **Your room is the DJ booth. The music adapts to the vibe — automatically.**

---

## The Anti-Playlist

You know the drill. Someone puts on a playlist. Three songs in, the energy dies. Someone else grabs the aux cord. Arguments ensue. The vibe is dead.

**Gesture DJ kills the aux cord.**

Point a webcam at your room. The agent watches. It *listens* with its eyes — headcount, movement, gestures, energy — and the music bends to match. No queues. No voting. No "wait, who put this on?" Just a room that sounds like the room feels.

---

## What It Actually Does

| Mode | Trigger | What Plays |
|------|---------|------------|
| 🎓 **Study** | 1–2 people, low movement, focused poses | Lo-fi, ambient electronic, minimal beats |
| 🧘 **Chill** | 2–4 people, relaxed, conversation posture | Downtempo, ambient house, slow grooves |
| 🕺 **Party** | 4+ people, high movement, arms up, dancing | High-BPM house, techno, disco, edits |
| 💪 **Workout** | Repetitive motion, high tempo movement | Driving bass, 120–140 BPM, no breakdowns |
| 🌙 **Late Night** | Low light, 1–2 people, slow sway | Deep house, melodic tech, after-hours energy |

**Gesture controls** — because nobody wants to unlock a phone mid-dance:
- ✋ **Palm up** → Volume up
- ✊ **Fist** → Pause/Play
- 👉 **Point right** → Next track
- 👈 **Point left** → Previous track
- 🤘 **Rock on** → Boost energy (party mode injection)
- 🤟 **Love** → Save current track to favorites

---

## How It Works (The Loop)

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│   WEBCAM    │ ──▶ │  VISION      │ ──▶ │  MOOD ENGINE    │ ──▶ │  MUSIC       │
│   FEED      │     │  PIPELINE    │     │  (classification│     │  ADAPTER     │
│             │     │  (MediaPipe, │     │   + confidence) │     │  (Spotify    │
│   30 FPS    │     │   YOLO,      │     │                  │     │   Web API)   │
└─────────────┘     │   custom)    │     └─────────────────┘     └──────────────┘
                    └──────────────┘              ▲                    │
                           │                      │                    ▼
                    ┌──────┴──────┐               │            ┌──────────────┐
                    │  GESTURE    │               └─────────── │  STATE SYNC  │
                    │  DETECTOR   │                            │  (history,   │
                    │  (Hands,    │                            │   prefs,     │
                    │   Pose)     │                            │   learning)  │
                    └─────────────┘                            └──────────────┘
```

**The agent doesn't just classify — it decides.** It maintains a running belief about "what the room wants right now," weighs confidence, smooths transitions (no jarring cuts), and learns your crew's taste over time. It's a control loop, not a classifier.

---

## Why an AI Agent? (Not a Chatbot)

This isn't "ask an LLM what to play." That's slow, disconnected, and wrong for real-time.

**Gesture DJ is an agent because:**
- **Multi-modal vision** — It fuses pose, hands, face, and object detection into a single scene understanding. Not separate models stitched together.
- **Real-time state** — It holds a rolling belief state: `current_mood`, `confidence`, `energy_trajectory`, `gesture_queue`. Updates at 30 FPS.
- **Tool integration** — It *acts*: calls Spotify Web API, manages playback devices, crossfades, queues, saves favorites. Tools are first-class.
- **Autonomy with guardrails** — It runs the room. You override with gestures. That's the contract.
- **Memory** — Session history → preference learning → better cold starts. "Last time these 3 people were here, they wanted disco by 11pm."

---

## Tech Stack

| Layer | Tech |
|-------|------|
| **Vision** | MediaPipe (Hands, Pose, Face), YOLOv8 (headcount/activity), OpenCV |
| **Agent Core** | TypeScript, Node.js, event-driven architecture |
| **Music** | Spotify Web API (Playback SDK + Web API), crossfade engine |
| **State** | Redis (hot state), SQLite (session history, preferences) |
| **Real-time** | WebSocket server → React frontend (optional dashboard) |
| **Deploy** | Docker, runs on any machine with a webcam + Node 20+ |

---

## Getting Started

```bash
# 1. Clone
git clone https://github.com/your-org/gesture-dj.git
cd gesture-dj

# 2. Install
npm install

# 3. Configure
cp .env.example .env
# Add your SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI

# 4. Run
npm run dev
```

**Requirements:**
- Node.js 20+
- A webcam (built-in or USB)
- Spotify Premium (for playback control)
- Linux/macOS/Windows (tested on all three)

**First run:** Authorize Spotify in the browser window that opens. Point camera at room. Dance.

---

## The Vibe Menu (Detected Moods → What Plays)

| Mood | BPM Range | Genres | Example Artists |
|------|-----------|--------|-----------------|
| **Deep Focus** | 60–85 | Lo-fi, ambient, modern classical | Nujabes, Tycho, Hiroshi Yoshimura |
| **Coffee Shop** | 85–105 | Indie electronic, chillhop | Bonobo, Rujoke, Tomggg |
| **Golden Hour** | 100–115 | Melodic house, balearic | DJ Koze, Palms Trax, Tornado Wallace |
| **Warmup** | 115–125 | Disco edits, funky house | Dâm-Funk, Greg Wilson, Honey Dijon |
| **Peak Time** | 125–135 | Tech house, driving techno | Peggy Gou, Charlotte de Witte, Nina Kraviz |
| **Afterhours** | 110–125 | Deep, hypnotic, minimal | Ricardo Villalobos, Zip, Janeret |
| **Sunrise** | 90–110 | Ambient techno, dub | Basic Channel, DeepChord, Echospace |

*The agent blends between these. No hard cuts. The room breathes.*

---

## Why I Built This

**I was tired of aux cord tyranny.**

Every party: someone's phone dies. Someone's playlist has 3 good songs and 40 skips. The "DJ" gets defensive when the room clears. The vibe dies because *music is reactive, not predictive*.

**I wanted music that reads the room better than I can.**

Not "smart shuffle." Not "algorithm knows you." **The room knows.** The bodies in it. The energy between them. The gestures people make when they *feel* a track — hands up, lean in, nod, smile.

So I built an agent that watches. Learns. Adapts. Gets out of the way.

**Your room is the DJ booth.** This just gave it a brain.

---

## Roadmap (Things That Would Be Cool)

- [ ] **Multi-room sync** — basement + living room = one coherent arc
- [ ] **Guest gestures** — "save this track" without app install (QR → web gesture)
- [ ] **Vibe profiles** — "Friday night crew" vs "Sunday morning cleanup" presets
- [ ] **Local LLM fallback** — run mood classification fully offline (privacy mode)
- [ ] **Lighting integration** — DMX/Philips Hue sync to mood transitions
- [ ] **Setlist export** — "What did we listen to last night?" → Spotify playlist

---

## License

MIT. Use it, fork it, run it at your wedding, your hackathon, your 3am coding session.

---

## Shoutouts

- MediaPipe team — making vision accessible
- Spotify — for the API (please don't rate-limit me into oblivion)
- The open-source DJ tooling community — you know who you are
- My roommates — for enduring 47 versions of "wait, let me adjust the confidence threshold"

---

**Made with ☕, 🎧, and too many late-night test sessions.**

*Star the repo if your room sounds better now. Open an issue if it doesn't. PRs welcome — especially ones that add new moods.*