# Myth

**Your friend, as a 19th-century inventor nobody's heard of.**

---

## What This Is

Myth is a zero-signup web app that generates full Wikipedia-style parody articles about your friends, cast into gloriously wrong historical eras. Pick a name, pick an era, optionally add a quirk ("believed cats were spies"), and get a complete fake biography — infobox with dubious dates, Early Life, Career, Controversies, Legacy, and a See Also section linking to articles like *The Great Steam-Powered Pigeon Incident of 1887*. 

It's *The Free Encyclopedia That Anyone Can Fabricate*. Screenshot it. Share it. Gaslight your group chat into believing Sarah Chen really did invent the pneumatic trouser press.

---

## How It Works

1. **Enter a name** — your friend, your enemy, your cat, the barista who spells "Mike" as "Myk"
2. **Pick an era** — eight flavours of historical absurdity (see below)
3. **Add a quirk** (optional) — "wrestled a bear for a sandwich," "communicated exclusively in limericks," whatever
4. **Click "Write Their History"** — wait ~800ms while the archives are summoned
5. **Copy, share, or screenshot** — the output is pure text in Wikipedia markup, ready to paste into a group chat or frame on your wall

---

## Available Eras

| Era | Vibe | Sample Occupation |
|-----|------|-------------------|
| **Victorian Inventor** | Gears, steam, questionable safety standards | Gentleman Scholar / Eccentric |
| **Renaissance Artist** | Medici drama, perfect hands, poisoned olives | Anatomy Enthusiast / Professional Rival |
| **1920s Bootlegger** | Milk trucks, speakeasies, parrots that won't testify | Jazz Patron / Entrepreneur |
| **Medieval Alchemist** | Sulphur, green-haired physicians, thimble-sized Philosopher's Stones | Court Advisor / Professional Mystery |
| **Cold War Spy** | Hollow chess pieces, redacted files, crossword puzzles that are definitely codes | Diplomat (allegedly) / Cipher Expert |
| **Ancient Philosopher** | Athens, annoying questions, movement is an illusion | Public Nuisance / Oracle Consultant |
| **Wild West Outlaw** | Decorative spoons, crooked pines, polite bandits | Folk Hero / Cattle Rustler (alleged) |
| **Jazz Age Musician** | 3 AM solos, piano fires, cutting contests that got literal | Bandleader / Improvisational Philosopher |

---

## Sample Output

> {{Infobox person
> | name         = Sir Malcolm Pembroke-Smythe
> | image        = Portrait_pending.jpg
> | caption      = Artist's impression (nobody could agree on the nose)
> | birth_date   = 1847
> | birth_place  = Probably
> | death_date   = 1912
> | death_place  = Mid-sentence
> | nationality  = British
> | occupation   = Eccentric
> | known_for    = That thing with the badger
> }}
>
> **Sir Malcolm Pembroke-Smythe** (1847 – 1912) was a British eccentric best known for their remarkable and somewhat baffling contributions to their field.[1]
>
> === Early Life ===
> Born to a family of modest means in rural England, Sir Malcolm Pembroke-Smythe showed an early fascination with mechanical contraptions, reportedly building a working steam-powered butter churn by age 12.[2]
>
> === Career ===
> In 1868, Sir Malcolm Pembroke-Smythe unveiled their most famous creation: the Automatic Teacup Reheater, a device that promised to revolutionise domestic engineering. The Royal Society was, by most accounts, deeply confused.[3]
>
> === Controversies ===
> In 1873, Sir Malcolm Pembroke-Smythe was accused of stealing credit from their assistant, a former chimney sweep named Bartholomew, who had actually done most of the inventing while Sir Malcolm Pembroke-Smythe was at the pub.[4]
>
> === Legacy ===
> While largely forgotten today, Sir Malcolm Pembroke-Smythe's work laid the groundwork for modern vibration science. A small plaque exists somewhere in Birmingham, though nobody has found it since 1987.
>
> === See Also ===
> * [[List of inventors who died trying to prove a point]]
> * [[The Great Steam-Powered Pigeon Incident of 1887]]
> * [[Eccentricity in Victorian England]]
> * [[Things that probably shouldn't have been electrified]]
>
> *This article is part of the **Myth Project**, a collection of biographies that are almost certainly not true but absolutely should be.*

---

## Tech Stack

- **Next.js 16** (App Router, React 19)
- **Tailwind CSS 4** + **DaisyUI 5** — retro terminal aesthetic, zero config pain
- **TypeScript** — because even fake history deserves type safety
- **OpenAI SDK** — present in deps but currently unused; the articles are generated client-side from hand-crafted template pools (see `src/app/page.tsx` — it's all there, no API key needed)
- **Zero backend** — fully static, deploys anywhere Next.js runs

---

## Getting Started

```bash
git clone https://github.com/your-org/myth.git
cd myth
npm install
npm run dev
```

Open http://localhost:3000. That's it. No `.env`, no database, no auth, no build step that takes longer than your coffee break.

---

## Share It

The output is pure text — copy it, screenshot it, paste it into Discord, print it on a birthday card, submit it to a peer-reviewed journal (we won't stop you). The Web Share API works on mobile; fallback copies to clipboard. 

**Pro tip:** Screenshot the rendered article in the Wikipedia-style card. The `Portrait_pending.jpg` caption reads *"Artist's impression (nobody could agree on the nose)."* Your friends *will* ask where you found it.

---

## Why I Built This

Wikipedia is *too factual*. It insists on "citations" and "verifiability" and "not inventing a steam-powered badger groomer." 

Your friends deserve better. They deserve a legacy where they dueled Lord Pemberton by talking about gears for four hours until he fell asleep. Where they vanished in 1912 under circumstances that invited much speculation — some say they achieved the Great Work and ascended; others note they had an unpaid tab at the local tavern. Where the See Also section links to *Things That Probably Shouldn't Have Been Electrified*.

Myth exists because the historical record is incomplete, and the gaps are where the fun lives.

---

## License

MIT — do whatever. Fork it, add eras, make your cousin a Byzantine eunuch, a Soviet cosmonaut who definitely saw something, a 14th-century plague doctor with a side hustle. The templates are in `src/app/page.tsx` — go wild.

---

*Built with the energy of Wikipedia editors having an off day.*