# Troubleshooting

Common issues and how to fix them. If you hit something not covered here, please open an issue.

---

## Installation & setup

### "ANTHROPIC_API_KEY not set"

The backend needs your Anthropic API key. Three ways to provide it:

1. **`.env` file** (easiest) — `cp .env.example .env` and fill in the value
2. **Environment variable** — `export ANTHROPIC_API_KEY="sk-ant-..."`
3. **Inline** — `ANTHROPIC_API_KEY=sk-ant-... python server.py`

Verify by hitting `http://127.0.0.1:5174/health` — `api_key_configured` should be `true`.

### "Address already in use" on port 5174

Something else is already using the port. Either:

- Kill the other process: `lsof -ti:5174 | xargs kill` (macOS/Linux)
- Or change SketchIt's port: set `SKETCHIT_PORT=5175`, then update:
  - `extension/manifest.json` → `host_permissions`
  - `extension/content.js` → `BACKEND_URL`
  - `extension/popup.js` → fetch URL

### "No module named 'flask'" / "No module named 'anthropic'"

You skipped the `pip install -r requirements.txt` step, or you're running Python from outside the virtualenv.

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Extension installation

### Widget doesn't appear on any page

1. Check `chrome://extensions` — is SketchIt listed and **enabled**?
2. Reload the page (Ctrl+R / Cmd+R) after installing the extension
3. Open DevTools console on the page — look for `[SketchIt]` logs or errors
4. Check the widget isn't hidden off-screen: search the DOM for `#sketchit-root`

### Widget doesn't appear on `chrome://`, `edge://`, or Chrome Web Store pages

**Expected.** Chrome blocks content scripts on browser-internal pages for security. Try any normal website.

### Widget appears but clicking does nothing

- Is the backend running? Run `curl http://127.0.0.1:5174/health`
- Open the page's DevTools console — you'll see the error message when you submit
- Check the network tab for failed POSTs to `/chat`

---

## Runtime errors

### "Backend not reachable"

The extension couldn't connect to the local server. Verify:

```bash
curl http://127.0.0.1:5174/health
# Expected: {"status":"ok",...}
```

If that fails, the Python server isn't running or isn't bound correctly. Check the server terminal for errors.

### "Model did not return valid JSON"

Occasional model hiccup. The server catches most of these by stripping code fences and retrying with brace-matching. If you still see it:

- Check the `raw` field in the error response
- Try rephrasing your prompt to be more specific
- Restart the server (sometimes the conversation state confuses the model)

### "Applied 0 / N operation(s)"

The model produced operations but none matched anything on the page. Causes:

- Selectors reference elements that don't exist (e.g. the model guessed `.login-form` but the site uses `#loginForm`)
- The host page is rendered by JavaScript after page load — try waiting a few seconds, then prompting
- The page HTML sent to the backend was truncated (see *Long pages* below)

### Changes flicker and disappear

A few sites aggressively rehydrate their DOM (React apps with constant re-renders, frameworks that diff against a virtual DOM). SketchIt's injected styles persist because they live in `<head>`, but replaced elements will be overwritten by the framework. There's no clean fix for this short of injecting CSS only.

Workaround: write CSS-only prompts like *"Just change the visual styling, don't restructure the HTML"* for these sites.

---

## Content Security Policy (CSP) issues

Some sites (banks, corporate webapps) ship a strict CSP that blocks:

- Inline `<style>` tags
- External stylesheets from `fonts.googleapis.com`
- `<link>` tags added at runtime

You'll see errors in the console like:

> Refused to apply inline style because it violates the following Content Security Policy directive…

There's no universal fix — it's working as intended from the site's perspective. Most public websites (marketing, news, ecommerce, personal sites, SaaS landing pages) don't have CSPs this strict. SketchIt works fine on them.

---

## Performance

### Slow responses

Typical request: 3–10 seconds depending on page size and operation complexity. If you're seeing 30+ seconds:

- Very large pages hit the 60k-char truncation and may take longer — try the page in an incognito window without ad blockers to rule out bloat
- Rate-limited API keys will queue — check the Anthropic console
- First request of a session is slower due to cold caches

### Long pages get truncated

The backend caps page HTML at 60k chars to stay within the model's context window. Pages over that get truncated with a `<!-- ...truncated... -->` marker.

Workarounds:

- Focus prompts on specific sections: *"Restyle just the header"*
- Raise the cap if you have a larger context budget — edit `MAX_HTML` in `server.py`

---

## Saving modified pages

### Saved HTML file looks broken when opened

The saved file has the **post-modification DOM** serialized, but it links to the original site's external resources (images, scripts, third-party CSS). If you open it offline or from another origin, CORS or missing resources may cause visual breakage.

Workarounds:

- Open the saved file over HTTP (`python -m http.server` in the folder)
- Use a tool like [SingleFile](https://github.com/gildas-lormeau/SingleFile) to inline assets before saving

### Save button does nothing

Check the console — content scripts can't download files if the user hasn't interacted with the page recently in some browsers. Click somewhere on the page, then try again.

---

## Still stuck?

- Search [existing issues](https://github.com/YOUR_USERNAME/sketchit/issues)
- Open a new issue with:
  - SketchIt version
  - Chrome (or browser) version
  - The URL where the problem happened (if possible)
  - Full console output from the page and from the server terminal
  - The exact prompt you used
