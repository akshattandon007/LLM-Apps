# 🐴 Professor Bray-niac

### **AI-Powered Tutorial Builder Agent**

*A Duolingo-inspired animated donkey teacher that explains programming concepts with real-world examples, live code, dad jokes, and text-to-speech audio.*

[](https://www.google.com/search?q=https://github.com/akshattandon007/professor-brayniac-tutorial-agent)
[](https://opensource.org/licenses/MIT)
[](https://reactjs.org/)
[](https://www.anthropic.com/claude)

-----

## 🎬 Overview

Professor Bray-niac is a **tutorial builder agent** that transforms complex programming concepts into animated, narrated micro-lessons. Simply type a concept (e.g., *"What is a class in Python?"*), and the agent generates a multi-slide interactive experience in seconds.

### **The Workflow**

1.  **Input:** User provides a topic.
2.  **Intelligence:** Claude Opus 4.6 generates a structured JSON payload containing pedagogical content, puns, and character "moods."
3.  **Output:** An animated SVG donkey (Bray-niac) delivers the lesson via Text-to-Speech (TTS), writes on a digital whiteboard, and reacts emotionally to the content.

-----

## ✨ Key Features

  * **🎭 Dynamic Animation System:** Bray-niac features 5 expression states (`idle`, `excited`, `thinking`, `joke`, `celebrating`) powered by spring physics.
  * **🗣️ Lip-Sync TTS:** Uses the Web Speech API with a viseme system that cycles 6 mouth shapes for realistic narration.
  * **✍️ Animated Whiteboard:** Content is "written" in real-time with a typewriter effect and cursor tracking.
  * **🧠 Structured Learning:** Lessons follow a proven flow: Greeting ➔ Analogy ➔ Code Example ➔ Pun ➔ Wrap-up.
  * **🎨 Zero Assets:** The entire character is a hand-crafted SVG—no external PNGs or heavy video files required.

-----

## 🖼️ User Experience

### **1. Input Screen**

A clean, Duolingo-green interface where users can type topics or select from "quick-pick" pills like *Recursion* or *Decorators*.

### **2. Loading State**

Bray-niac enters a `thinking` pose (hoof on chin, eyes upward) while rotating through witty loading messages like *"Calculating donkey-power..."*

### **3. The Classroom**

The main player interface featuring:

  * **Left Pane:** Bray-niac with active speech and joke bubbles.
  * **Right Pane:** A whiteboard displaying handwritten-style notes and code.
  * **Controls:** Progress bars, play/pause, and slide navigation.

-----

## 🏗️ Technical Architecture

### **The Stack**

| Layer | Technology | Role |
| :--- | :--- | :--- |
| **Engine** | **React 18** | UI Orchestration & State |
| **AI** | **Claude Opus 4.6** | Content Generation (JSON Schema) |
| **Graphics** | **SVG + Spring Physics** | Resolution-independent animations |
| **Audio** | **Web Speech API** | Browser-native Text-to-Speech |

### **JSON Content Schema**

The agent expects a strict JSON format from the LLM to drive the UI:

```json
{
  "title": "Topic Name",
  "slides": [
    {
      "speech": "Narrator text...",
      "whiteboard": "Visual text/code...",
      "joke": "Donkey-themed pun",
      "expression": "excited"
    }
  ]
}
```

-----

## 🚀 Getting Started

### **Option A: Use as a Claude Artifact (Easiest)**

1.  Copy the code from `tutorial-builder-agent.jsx`.
2.  Paste it into a Claude.ai chat.
3.  Claude will render the full application immediately.

### **Option B: Local Development**

1.  **Clone & Install:**
    ```bash
    git clone https://github.com/akshattandon007/professor-brayniac-tutorial-agent.git
    cd professor-brayniac-tutorial-agent
    npm install
    ```
2.  **Environment Setup:**
    Create a `.env.local` file and add your Anthropic API Key:
    ```env
    VITE_ANTHROPIC_API_KEY=your_sk_key_here
    ```
3.  **Run:**
    ```bash
    npm run dev
    ```

-----

## 🔧 Customization

  * **Adjust Narration:** Modify `utterance.rate` in `useTTS.js` to speed up or slow down Bray-niac's voice.
  * **Change Persona:** Edit the `SYSTEM_PROMPT` in `src/config/prompt.js` to turn the donkey into a different animal or teacher style.
  * **Animation Physics:** Tweak stiffness and damping constants in the `useSpring` hook for more or less "bounce."

-----

## 🤝 Contributing

Puns and code improvements are welcome\!

1.  Fork the Project.
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the Branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

-----

\<div align="center"\>

Built with 🐴 and terrible puns by **[Akshat Tandon](https://github.com/akshattandon007)**

*Professor Bray-niac © HEE-HAW Industries*

\</div\>
