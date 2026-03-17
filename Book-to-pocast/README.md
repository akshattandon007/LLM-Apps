# 🎙️ PDF to Podcast

Turn any PDF into a spoken podcast episode — powered by Claude AI and Google Text-to-Speech.

Upload a research paper, report, or article and get back a ready-to-listen MP3 in minutes, narrated in a tone of your choice.

---

## ✨ What it does

1. **Reads** your PDF and extracts all text
2. **Summarises** the key ideas into a 400–600 word podcast monologue using Claude (Anthropic's AI)
3. **Speaks** the script aloud and saves it as an MP3 file

---

## 🎭 Speaker Tone Options

| Tone | Vibe |
|---|---|
| `casual` | Friendly, conversational — like a tech podcast host |
| `academic` | Measured, precise — like a university lecturer |
| `energetic` | High-energy, punchy — like a morning radio host |
| `storyteller` | Narrative, immersive — like an audiobook narrator |
| `news` | Crisp, authoritative — like a news anchor |

---

## 📁 Repository Structure

```
pdf-to-podcast/
├── pdf_to_podcast.py     # Main script
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

---

## 🚀 Getting Started

### Option A — Run in Google Colab (recommended, no local setup)

1. Open [Google Colab](https://colab.research.google.com) and create a new notebook
2. Upload your PDF using the 📁 Files sidebar
3. Run the following cells:

```python
# Cell 1 — Install dependencies
!pip install pypdf anthropic gtts
```

```python
# Cell 2 — Set your Anthropic API key (use Colab Secrets for safety)
from google.colab import userdata
import os
os.environ["ANTHROPIC_API_KEY"] = userdata.get("ANTHROPIC_API_KEY")
```

```python
# Cell 3 — Clone the repo and run
!git clone https://github.com/YOUR_USERNAME/pdf-to-podcast.git
%cd pdf-to-podcast

import sys
sys.argv = ["pdf_to_podcast.py", "/content/your_file.pdf", "--tone", "casual", "--save-script"]

exec(open("pdf_to_podcast.py").read())
main()
```

```python
# Cell 4 — Download the audio
from google.colab import files
files.download("podcast_output.mp3")
```

---

### Option B — Run Locally

**Prerequisites:** Python 3.8+

**1. Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/pdf-to-podcast.git
cd pdf-to-podcast
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Set your Anthropic API key**

Get your key from [console.anthropic.com](https://console.anthropic.com) → API Keys.

```bash
# Mac/Linux
export ANTHROPIC_API_KEY="sk-ant-..."

# Windows (Command Prompt)
set ANTHROPIC_API_KEY=sk-ant-...
```

**4. Run the script**
```bash
python pdf_to_podcast.py your_file.pdf --tone casual --output episode.mp3
```

---

## 📖 Full Usage

```
python pdf_to_podcast.py <pdf_path> [--tone TONE] [--output OUTPUT] [--save-script]

Arguments:
  pdf               Path to your input PDF file

Options:
  --tone            Speaker tone: casual | academic | energetic | storyteller | news
                    (default: casual)
  --output          Output MP3 filename (default: podcast_output.mp3)
  --save-script     Also save the generated script as a .txt file
```

**Examples:**
```bash
# Casual tone, default output name
python pdf_to_podcast.py report.pdf

# Energetic tone, custom output name
python pdf_to_podcast.py research_paper.pdf --tone energetic --output my_episode.mp3

# Storyteller tone, save the script too
python pdf_to_podcast.py annual_report.pdf --tone storyteller --save-script
```

---

## ⚙️ Requirements

- Python 3.8+
- Anthropic API key (get one at [console.anthropic.com](https://console.anthropic.com))
- Internet connection (for Claude API and Google TTS)

Dependencies (see `requirements.txt`):
```
pypdf
anthropic
gtts
```

---

## 📄 PDF Compatibility

| ✅ Works well | ❌ Avoid |
|---|---|
| Research papers | Scanned PDFs (image-only) |
| Reports & articles | Password-protected PDFs |
| Book chapters | Slide decks (too fragmented) |
| News articles saved as PDF | PDFs with mostly charts/diagrams |

---

## 💡 Tips

- **Best PDFs to try:** Papers from [arxiv.org](https://arxiv.org), company annual reports, or any article saved as PDF from your browser
- **Colab users:** Files upload to `/content/` — use that as your path
- **API costs:** Each run costs roughly $0.01–$0.05 depending on PDF length

---

## 🛠️ Built With

- [Anthropic Claude](https://anthropic.com) — AI summarisation & script generation
- [pypdf](https://github.com/py-pdf/pypdf) — PDF text extraction
- [gTTS](https://github.com/pndurette/gTTS) — Google Text-to-Speech

---

## 📜 License

MIT — feel free to use, modify, and share.
