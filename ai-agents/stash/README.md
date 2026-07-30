# Stash

> Check what you've got. Make something beautiful.

Stash is a tiny web app for crafters who have supplies piling up and no idea what to make with them. Tick the boxes for what's already in your stash — yarn, fabric scraps, beads, clay, paint, you name it — hit **What can I make?** and get project ideas ranked by how much you already own.

No signup. No database. Just a JSON file of 31 hand-picked projects across 12 craft categories, and a Flask server that does the math.

---

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Open <http://localhost:5198> and start checking boxes.

---

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | Flask 3.x | Tiny, zero-config, perfect for a single-file API |
| Data | `projects.json` | No DB to run, no migrations, easy to edit by hand |
| Frontend | Vanilla HTML/CSS/JS in a Jinja template | No build step, no bundler, works everywhere |
| Styling | Custom CSS (warm, Etsy-inspired palette) | Feels like a craft shop, not a dashboard |

---

## Project Structure

```
stash/
├── app.py              # Flask server + /match endpoint
├── projects.json       # 31 seeded craft projects
├── requirements.txt    # flask>=3.0
├── templates/
│   └── index.html      # Single-page UI (Jinja template)
└── static/
    └── style.css       # Warm, responsive, crafty styles
```

---

## Architecture (Simple)

```
┌─────────────┐     POST /match     ┌─────────────┐
│   Browser   │ ─────────────────▶  │  Flask API  │
│  (checkboxes)│  { owned: [...] }   │  (app.py)   │
└─────────────┘ ◀─────────────────  └──────┬──────┘
        ▲                                   │
        │         JSON: ranked projects     │
        │    (match_pct, missing, owned)    │
        └───────────────────────────────────┘
```

**Matching logic** (in `app.py`, ~25 lines):

1. Load `projects.json` on every request — no cache, no DB, always fresh
2. Intersect `owned` supplies with each project's `supplies_needed`
3. Score = `owned_count / total_needed`
4. Sort by match % descending, then by total supplies needed (more complete kits rank higher)
5. Return top 8 matches

No database. No migrations. No background jobs. The JSON file *is* the database.

---

## Projects: What's Inside

31 projects across 12 craft categories:

| Category | Projects | Example |
|----------|----------|---------|
| crochet | 2 | Cozy Beanie, Granny Square Blanket |
| knitting | 1 | Infinity Scarf |
| sewing | 3 | Quilted Coasters, Fleece Pillow, Tote Bag |
| macrame | 2 | Plant Hanger, Keychain |
| jewelry | 3 | Beaded Bracelet, Polymer Clay Earrings, Wire-Wrapped Pendant |
| paper crafts | 3 | Greeting Cards, Paper Roses, Decoupage Tray |
| embroidery | 2 | Embroidered Patch, Hoop Wall Art |
| painting | 2 | Watercolour Galaxy, Painted Terracotta Pots |
| home decor | 4 | Tin Can Lanterns, Bead Garland, Pom-Pom Rug, Pressed Flower Frame |
| resin crafts | 1 | Resin Coasters |
| fabric dyeing | 1 | Tie-Dye T-Shirt |
| bath & body | 1 | Bath Bombs |

Each project has:
- `name` — project title
- `category` — one of the 12 above
- `supplies_needed` — array of supply strings (lowercase, singular/plural as needed)
- `difficulty` — `beginner`, `intermediate`, or `advanced`
- `time_estimate` — human-readable string like `"3-4 hours"` or `"45 minutes + 24h dry"`
- `tutorial_url` — link to a YouTube/tutorial (placeholder URLs in seed data)
- `description` — 1-2 sentence hook

---

## Adding New Projects

Open `projects.json` and append a new object to the array. Keep the schema consistent:

```json
{
  "name": "Your Project Name",
  "category": "crochet",              // use an existing category or add a new one
  "supplies_needed": [
    "yarn",
    "crochet hook",
    "stitch markers"
  ],
  "difficulty": "beginner",           // beginner | intermediate | advanced
  "time_estimate": "2-3 hours",
  "tutorial_url": "https://youtube.com/watch?v=real-tutorial-link",
  "description": "A one-sentence hook that makes someone want to start."
}
```

**Tips for good supply names:**
- Use lowercase
- Singular or plural is fine, but be consistent (`"scissors"` not `"scissor"`)
- Match the names used in the checklist (they're extracted from `projects.json` at startup)
- Keep it specific: `"worsted weight yarn"` beats `"yarn"` if the project needs it

After saving `projects.json`, just refresh the page — the checklist rebuilds automatically from the updated supply list.

---

## Running in Production (If You Want)

```bash
# With gunicorn (4 workers, port 8000)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

Put behind nginx/Caddy with TLS. No database to migrate, no migrations to run. Just deploy the folder.

---

## Why Stash Exists

Every crafter has a stash. Yarn bought for a sweater that never happened. Fabric for a quilt that's still a dream. Beads for "someday" earrings.

Stash doesn't make you feel guilty about it. It makes you *use* it.

Check a few boxes. Find a project you can start *tonight*. Make something.

---

## License

MIT — use it, fork you want.

---

*Built for crafters with stash guilt. No signup. Just make.*