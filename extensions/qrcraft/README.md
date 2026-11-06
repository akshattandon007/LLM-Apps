# 📷 QRCraft — QR Code Toolkit

**Generate QR codes from anything, decode QR codes from images.**

QRCraft is a two-way QR code toolkit for the terminal. Encode URLs, text, contacts, or anything else into QR codes as PNG images or ASCII art. Decode QR codes from image files (PNG, JPG, etc.) when `zbarimg` is available.

```
──── QR CODE ────
 ██████████████
 ██  ████  ██
 ██  ██████████
 ██████████████
```

---

## 🚀 Quick Start

```bash
# Install
pip install -r requirements.txt

# Generate a QR code from a URL
python -m qrcraft encode "https://github.com/akshattandon007/LLM-Apps" -o my-qr.png

# Generate as ASCII art (no image file)
python -m qrcraft encode "hello world" --ascii

# Pipe data in
echo "https://example.com" | python -m qrcraft encode -o from-pipe.png

# Decode a QR code from an image
python -m qrcraft decode qr.png

# JSON output for scripting
python -m qrcraft decode qr.png --json
```

---

## 📋 Usage

### `encode` / `e` — Generate QR codes

```bash
# Basic: save as PNG
qrcraft encode "https://github.com" -o gh.png

# ASCII art in terminal
qrcraft e "Hello World" --ascii

# Custom colours
qrcraft encode "link" -o link.png --fill "#FF0000" --back "#FFFFFF"

# Custom error correction (L, M, Q, H)
qrcraft encode "data" --error H -o high-redundancy.png

# Batch mode — generate multiple QR codes
qrcraft e "item1" --batch "item2" "item3" --output-dir ./codes
```

### `decode` / `d` — Read QR codes

```bash
# Decode from image
qrcraft decode screenshot.png

# Machine-readable JSON
qrcraft decode qr.png --json
# → [{"data": "https://github.com", "type": "QRCODE"}]

# From a screenshot of a WiFi QR code
qrcraft d wifiscan.jpg
```

---

## 🧪 Tests

```bash
cd extensions/qrcraft
python3 -m pytest tests/ -v
```

Tests cover: PNG encoding, ASCII mode, batch mode, custom colours, error correction levels, long URLs, decode failure handling, decode on blank images, CLI argument parsing, and edge cases (empty data, missing files).

---

## 🔧 Dependencies

| Package  | Purpose                  |
|----------|--------------------------|
| `qrcode` | QR code generation       |
| `Pillow` | Image I/O (encode PNG, decode load) |
| `requests` | Online decode API fallback |

For QR **decoding** with `zbarimg`, install zbar-tools:
```bash
sudo apt install zbar-tools   # Linux
brew install zbar             # macOS
```

Without zbarimg, decode falls back to a free online API (requires internet).

---

## 📁 Project Structure

```
extensions/qrcraft/
├── qrcraft/
│   ├── __init__.py      # Package metadata
│   ├── __main__.py      # `python -m qrcraft`
│   ├── cli.py           # CLI entry point (argparse)
│   ├── encode.py        # QR generation logic
│   └── decode.py        # QR decoding (zbarimg → pyzbar → API)
├── tests/
│   ├── __init__.py
│   └── test_qrcraft.py  # 18 tests, all passing
├── requirements.txt
├── pyproject.toml
├── README.md
├── Decisions.md
└── Flow.md
```

---

## 📄 License

MIT — part of the [LLM-Apps](https://github.com/akshattandon007/LLM-Apps) collection.