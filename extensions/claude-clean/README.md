# Claude Clean

A Chrome extension that rewrites Claude-generated text by varying vocabulary and restructuring sentences to change its statistical properties.

> **Claim:** This transformation changes the statistical properties of the text, but cannot guarantee that Claude's watermark detection will no longer identify it.
>
> This extension does **not** claim to "remove watermark" or "delete hidden characters." Claude's watermark is statistical — not a simple hidden character.

## Features

- **Paste & Clean** — Paste any Claude-generated text, click Clean, get a rewritten version
- **Before/After Comparison** — See original and cleaned text side-by-side
- **Local Processing** — All text transformation happens in your browser. Nothing is uploaded.
- **Right-Click Integration** — On claude.ai, right-click any selected text → "Clean with Claude Claude Clean"
- **Content Script** — A "Clean with Claude Clean" button appears on Claude output blocks
- **Dark Mode** — Toggle light/dark theme
- **Word & Character Counts** — See stats for both original and cleaned text

## Transformation Pipeline

1. Sentence segmentation
2. Vocabulary variation (synonym replacement)
3. Sentence restructuring (clause reordering)
4. Semantic consistency check (preserves numbers, names, URLs)

## Privacy

- All text processing is done **locally in your browser**
- No data is ever uploaded to any server
- Pasted content is never stored by default
- No analytics, no telemetry, no tracking

## Installation

### From GitHub Releases

1. Download the latest `.zip` from the [Releases](https://github.com/akshattandon007/Claude-Clean/releases) page
2. Extract the zip to a folder
3. Open Chrome → Extensions (`chrome://extensions`)
4. Enable **Developer mode** (toggle top-right)
5. Click **Load unpacked** and select the extracted folder

### Build from Source

```bash
# Clone the repo
git clone https://github.com/akshattandon007/Claude-Clean.git
cd Claude-Clean

# Install dependencies
npm install

# Build
npm run build

# The dist/ folder is the unpacked extension
# Load it via Chrome Extensions → Developer mode → Load unpacked
```

## Usage

1. Click the Claude Clean icon in your toolbar
2. Paste Claude-generated text into the text area
3. Click **Clean Claude Text**
4. Review the changes in the Before/After panel
5. Click **Copy Clean Text** to copy the result

Or on claude.ai:
1. Select any Claude-generated text
2. Right-click → **Clean with Claude Clean**
3. Open the extension — the text is auto-loaded

## Development

```bash
npm run dev     # Start Vite dev server with HMR
npm run build   # Build for production
npm run preview # Preview the build
```

## License

MIT