# Design Principles

These are the principles baked into SketchIt's system prompt. They represent the bar the agent is held to — the minimum quality floor, not a ceiling.

Understanding these helps you:

- Predict what the agent will and won't do
- Write prompts that give it more creative runway
- Contribute improvements to the prompt

The agent's design intelligence is built in [`backend/design.py`](../backend/design.py), which composes four parts:

1. **Design philosophy** — the aesthetic worldview (intentionality, craftsmanship, point of view)
2. **Nine principles** — the enforceable quality floor (below)
3. **Theme library** — 11 curated palette + font pairings (see bottom of this doc)
4. **Output format spec** — the structural contract with the DOM executor

All four are derived from Claude's built-in design skills: `frontend-design`, `theme-factory`, `brand-guidelines`, and `canvas-design`.

---

## 1. Hierarchy

Every screen has **one** dominant element. Readers should know instantly what matters most.

Established via:

- **Size** — the hero headline is 5× the body text, not 1.5×
- **Weight** — 700 next to 400
- **Color** — a single accent against a neutral field
- **Space** — generous whitespace around the one thing that matters

Anti-pattern: six buttons, all the same size, all bright blue.

---

## 2. Contrast & legibility

Body text contrast ratio ≥ **4.5:1** (WCAG AA). Large text ≥ 3:1. No exceptions for aesthetic reasons.

The agent is told: if you have to choose between "looks cool" and "is readable," choose readable. A design nobody can read is a failed design.

---

## 3. Consistent spacing scale

All margins and padding come from a defined scale:

```
4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96
```

Why: arbitrary values (`margin: 17px`) make the page feel haphazard. A scale creates rhythm and visual coherence even when the reader can't articulate why.

The agent emits these as CSS custom properties:

```css
:root {
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 16px;
  --space-4: 24px;
  --space-5: 40px;
}
```

---

## 4. Typography pairing

**Avoid:** Arial, Times New Roman, `-apple-system` defaults, Inter (overused), Roboto (overused).

**Prefer:** Distinctive display + refined body pairings:

| Display | Body | Vibe |
|---|---|---|
| Fraunces | Inter | Editorial, warm |
| Playfair Display | Lora | Luxury, literary |
| Space Grotesk | IBM Plex Sans | Tech, clean |
| Recoleta | Source Sans | Friendly, approachable |
| Syne | DM Sans | Contemporary, bold |
| Cormorant | Jost | High-end, classical |

The agent loads these via Google Fonts before applying them. A distinctive pairing is one of the cheapest, biggest-impact changes you can make to an existing site.

---

## 5. Intentional color

A good palette has **three roles**:

- **Dominant (60%)** — the brand or mood color
- **Neutral base (30%)** — background, surfaces, subtle text
- **Accent (10%)** — for CTAs, highlights, focus states

Avoid: the rainbow. Avoid: the default AI purple-gradient-on-white. Avoid: seven competing primary colors.

When the user requests a color scheme, the agent:

1. Picks one dominant from that family
2. Chooses a neutral base that harmonizes
3. Picks a single sharp accent

---

## 6. Whitespace is a feature

Tight layouts feel cheap. Crowded forms feel anxious. Breathing room is the single most consistent signal of a premium-feeling interface.

Rule of thumb: if the agent's design feels cramped, it should roughly double all margins and paddings and see what happens.

---

## 7. Micro-interactions

Every interactive element should have:

- **Hover state** — subtle color or background shift
- **Focus state** — visible ring for keyboard users (accessibility!)
- **Transition** — 150–250 ms ease, no faster, no slower
- **Active state** — slight translate or scale on click

```css
button {
  transition: background 180ms ease, transform 180ms ease;
}
button:hover { background: var(--color-primary-dark); }
button:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.1);
}
button:active { transform: translateY(1px); }
```

---

## 8. Mobile-considerate

Even when the user doesn't mention mobile:

- Tap targets ≥ **44×44 px**
- Font sizes ≥ 16 px for body (prevents iOS auto-zoom)
- Flexible layouts (`flex-wrap`, `min-width: 0`, etc.)
- No fixed widths that blow out on narrow screens

---

## 9. Not generic

The single most important rule. The agent is explicitly told: **commit to an aesthetic point of view.**

If the prompt is vague, pick a direction — editorial, brutalist, Swiss, retro-futurist, soft-pastel, industrial — and execute it with conviction. A clear aesthetic the user doesn't love is better than a timid average nobody remembers.

What this rules out:

- Generic SaaS purple gradients on white
- Default Material Design without customization
- The "AI aesthetic" of Inter + rounded corners + lavender
- Beige-on-beige minimalism with no personality

---

## How to prompt for great results

Knowing the principles, these prompts produce the best outcomes:

✅ *"Editorial magazine layout, serif headlines, generous margins, warm palette"*
✅ *"Brutalist — stark black-and-white, mono font, hard edges, zero gradients"*
✅ *"Soft pastel, rounded everything, Recoleta for headlines, tactile buttons"*

Less effective:

❌ *"Make it better"* (no direction — the agent picks one for you, which may not match your taste)
❌ *"Use 47 colors"* (violates the intentional-color principle; the agent will push back)
❌ *"Delete all whitespace"* (violates a core principle; you'll get resistance)

The agent isn't an anything-goes renderer — it's a designer. Treat it like one.

---

## The Theme Library

The agent has 11 vetted themes it can reference by name. Each has a defined palette, display/body font pairing, and a "best for" guideline. Invoking a theme by name in your prompt gives the agent a strong starting point, but it can also blend or adapt them.

| Theme | Vibe | Best for |
|---|---|---|
| **Anthropic** | Warm, literary, restrained (ivory + orange) | Publications, thoughtful SaaS, writing tools |
| **Ocean Depths** | Professional maritime (navy + teal) | Financial services, consulting |
| **Sunset Boulevard** | Warm, vibrant (coral + amber) | Hospitality, food, creative agencies |
| **Forest Canopy** | Earth tones (deep green + sage) | Wellness, sustainability, outdoor brands |
| **Modern Minimalist** | Editorial grayscale | Portfolios, design tools, premium SaaS |
| **Golden Hour** | Nostalgic autumnal (ochre + sienna) | Editorial magazines, luxury brands |
| **Arctic Frost** | Cool and crisp (ice blues) | Fintech, analytics, cloud infrastructure |
| **Desert Rose** | Dusty pinks + terracotta | Wellness, beauty, boutique commerce |
| **Tech Innovation** | Electric blue on near-black | AI/ML products, developer tools |
| **Botanical Garden** | Leaf greens + petal pinks | Organic food, weddings, hospitality |
| **Midnight Galaxy** | Deep indigo + violet | Music, gaming, entertainment |

Use them by naming them (*"make this Arctic Frost"*), by describing the feel (*"tech startup vibe"* → Tech Innovation), or by referencing the page's purpose (the agent will match to the closest "best for" guideline).

Full theme definitions — hex codes, font pairings, Google Fonts URLs — live in [`backend/design.py`](../backend/design.py).
