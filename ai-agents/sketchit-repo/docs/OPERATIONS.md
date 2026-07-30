# Operation Schema

Every response from the backend contains an `operations` array. Each operation is a JSON object with a `type` and type-specific fields. The content script executes them in order against the live DOM.

This document is the authoritative reference.

---

## Response shape

```json
{
  "explanation": "A 1–3 sentence design rationale",
  "operations": [
    { "type": "...", /* type-specific fields */ }
  ]
}
```

- `explanation` — Human-readable summary shown to the user
- `operations` — List of DOM-mutation instructions

---

## Operation types

### `inject_css`

Append a `<style>` tag to `<head>`. The primary way to restyle the page.

```json
{
  "type": "inject_css",
  "css": "body { background: #0B0D12; color: #F8FAFC; }"
}
```

**Guidance:** One large, well-scoped CSS block is usually preferable to many small ones. Use `!important` only when overriding strongly-specified host styles.

---

### `load_font`

Inject a `<link rel="stylesheet">` to `<head>` — typically for Google Fonts.

```json
{
  "type": "load_font",
  "href": "https://fonts.googleapis.com/css2?family=Fraunces:wght@400;600&display=swap"
}
```

**Guidance:** Emit `load_font` operations **before** any `inject_css` that references the font family. The agent is instructed to do this.

---

### `set_attribute`

Set an attribute on every element matching a selector.

```json
{
  "type": "set_attribute",
  "selector": "img.logo",
  "attribute": "alt",
  "value": "Company logo"
}
```

---

### `set_text`

Replace the text content of matched elements.

```json
{
  "type": "set_text",
  "selector": "h1.hero-title",
  "text": "Build beautiful products, faster."
}
```

Uses `textContent` (safe — no HTML parsing).

---

### `set_html`

Replace the inner HTML of matched elements.

```json
{
  "type": "set_html",
  "selector": "section.hero",
  "html": "<h1>New headline</h1><p>New subhead</p>"
}
```

⚠️ HTML is parsed and inserted — only use when semantic restructuring is needed.

---

### `add_class` / `remove_class`

Toggle a class on matched elements.

```json
{ "type": "add_class", "selector": "nav", "class": "scrolled" }
{ "type": "remove_class", "selector": ".legacy", "class": "legacy" }
```

---

### `replace_element`

Replace matched elements with a new element parsed from HTML. Used for semantic restructuring (swapping a `<div>` form for a proper `<form>` with labels, etc.).

```json
{
  "type": "replace_element",
  "selector": "#signup-form",
  "html": "<form id='signup-form' novalidate>...</form>"
}
```

Only the **first** element of the provided HTML is used as the replacement.

---

### `append_to`

Append HTML as the last child of matched elements. Used for adding new sections, nav bars, footers, etc.

```json
{
  "type": "append_to",
  "selector": "body",
  "html": "<footer class='site-footer'>© 2026</footer>"
}
```

---

### `remove_element`

Remove matched elements from the DOM.

```json
{ "type": "remove_element", "selector": ".ad-banner" }
```

---

## Selector rules

- Selectors are standard CSS selectors (`document.querySelectorAll` semantics)
- The widget's own DOM is auto-excluded — you can't accidentally target it
- Invalid selectors log a warning and no-op; they don't abort the batch

---

## Execution semantics

- Operations run **in order**
- Failure of one op does **not** abort the rest
- Each op returns `{ ok: boolean, note: string }` logged to the console
- All injected nodes (CSS, fonts, replacements) are tagged
  `data-sketchit-injected="<kind>"` so **Reset** can strip them cleanly

---

## Adding new operation types

1. Add the new type to the schema list in `DESIGNER_SYSTEM_PROMPT` inside `backend/server.py`
2. Implement a handler in `applyOperation()` in `extension/content.js`
3. Add an entry to this document
4. (Optional) write an example in the README

Keep operations:

- **Small** — one responsibility per type
- **Declarative** — describe the desired state, not an algorithm
- **Idempotent-ish** — re-running shouldn't duplicate side effects catastrophically
