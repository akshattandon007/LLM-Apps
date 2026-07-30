# SketchIt Extension

A Chrome extension (Manifest V3) that injects a floating chat widget on every page and applies design operations returned by the SketchIt backend.

## Load the extension

1. Open `chrome://extensions` in Chrome (or any Chromium browser)
2. Enable **Developer mode** (top-right)
3. Click **Load unpacked**
4. Select this `extension/` folder
5. The SketchIt pencil icon appears in your toolbar

## Files

| File | Purpose |
|---|---|
| `manifest.json` | Manifest V3 config — permissions, content scripts, icons |
| `background.js` | Service worker. Listens for toolbar icon clicks and messages the content script |
| `content.js` | The main file. Injects the floating widget, captures page HTML, POSTs to the backend, executes returned DOM operations, handles save / reset / close |
| `widget.css` | Scoped widget styles. High specificity + `!important` so host pages can't break the UI |
| `popup.html` / `popup.js` | Small status popup shown when clicking the toolbar icon — pings the backend and shows whether it's up |
| `icons/icon{16,32,48,128}.png` | Icon at all required sizes |
| `generate_icons.py` | Script to regenerate icons from the SVG mark (requires Pillow) |

## How it works

1. `content.js` loads on every page (`run_at: document_idle`) and appends the widget DOM to `<html>`.
2. When the user submits a prompt:
   - The page HTML is serialized (widget excluded via `data-sketchit` attribute)
   - POST to `http://127.0.0.1:5174/chat`
   - Response is a list of **operations** — `inject_css`, `replace_element`, `load_font`, etc.
3. Each operation is executed against the live DOM. All injected nodes get a `data-sketchit-injected` attribute so they can be removed on reset.
4. **Save** serializes the current DOM (minus the widget) and triggers an HTML download via a blob URL.

## Permissions

| Permission | Why |
|---|---|
| `activeTab` | Read/modify the current tab's DOM |
| `scripting` | Background service worker messaging |
| `storage` | Reserved for future preferences |
| `downloads` | Save modified HTML files |
| `host_permissions: http://127.0.0.1:5174/*` | Talk to the local backend |
| `content_scripts: <all_urls>` | Widget appears on every page |

**The extension makes no network calls other than to your local backend.**

## Regenerating icons

If you tweak the logo SVG, regenerate all sizes:

```bash
cd extension
pip install Pillow
python generate_icons.py
```

## Development tips

- Click the 🔄 reload button on the extension card at `chrome://extensions` after every change to `content.js` / `widget.css`
- For `manifest.json` changes, you sometimes need to remove + re-add the extension
- Open the DevTools console on the host page to see SketchIt logs (prefixed `[SketchIt]`)
- Open the service-worker console via `chrome://extensions → SketchIt → service worker` to see background logs

## Packaging

To create a distributable `.zip`:

```bash
cd extension
zip -r ../sketchit-extension-v1.0.0.zip . -x "generate_icons.py" "*.DS_Store"
```

To publish to the Chrome Web Store, you'll need an icon at 128 px and screenshots. See [Chrome Web Store docs](https://developer.chrome.com/docs/webstore/publish).
