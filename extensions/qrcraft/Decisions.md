# Decisions

## 1. CLI-first, not web app

**Chosen:** CLI tool with `argparse`, `python -m` and entry-point scripts.  
**Rejected:** Flask/FastAPI web app, GUI, browser extension.  
**Why:** Extensions category is for standalone utilities. A web server would be overkill for a tool that generates a QR code from a text input. CLI composes naturally with pipes, scripts, and automation (e.g. `echo "url" | qrcraft encode -o qr.png`).

## 2. Python, not Rust/Go/Node.js

**Chosen:** Python 3.10+.  
**Rejected:** Rust (performance), Go (executable size), Node.js (npm dep chain).  
**Why:** Python has the best QR code ecosystem (`qrcode`, `Pillow`, `pyzbar`), is pre-installed on the target system, and the tool is I/O-bound, not CPU-bound. A QR generation takes ~50ms — rewriting in a compiled language would add build complexity for zero perceptible benefit.

## 3. `qrcode[pil]` over pure-libqrencode bindings

**Chosen:** `qrcode` Python package (with Pillow image factory).  
**Rejected:** `qbl` (C lib bindings), `segno` (pure Python but less ecosystem), system `qrencode` CLI via subprocess.  
**Why:** `qrcode` is the most popular Python QR library (PyPI: 50M+/month), supports SVG/PNG/ASCII out of the box, has configurable error correction, and works offline. Calling `qrencode` via subprocess would add a system dependency and complicate cross-platform support.

## 4. ASCII rendering via Unicode blocks, not half-block characters

**Chosen:** Full-block Unicode characters (`█` with `▄` for half-rows).  
**Rejected:** "██" per module (double-width), braille patterns, HTML rendering.  
**Why:** Using two spaces for empty and `██` for filled gives the best terminal readability across all fonts and terminal emulators. Braille patterns are too dense for most terminals. HTML rendering requires a browser — defeats the CLI purpose.

## 5. Three-strategy decode pipeline (fail open)

**Chosen:** Try `zbarimg` → `pyzbar` → online API in sequence.  
**Rejected:** Single-decoder hard dependency.  
**Why:** QR decoding requires a C library (`libzbar`) which isn't guaranteed on every system. The pipeline starts with the fastest option (zbarimg CLI), falls through to pyzbar if libzbar is loadable as a shared library, and finally attempts an online decode API (zxing.org) as a network fallback. If all three fail, returns an empty list — the tool always works for generation, and decode degrades gracefully.

## 6. PNG as default image format, not SVG

**Chosen:** PNG (via Pillow, default).  
**Rejected:** SVG (vector, tiny file size).  
**Why:** PNG displays everywhere (terminals, messengers, browsers, document editors). SVG requires a viewer that renders SVG. The file size difference is negligible for a single QR code (~2 KB PNG vs ~1 KB SVG). PNG also works with Pillow's native save path.

## 7. Error correction default M (15%), not L (7%) or H (30%)

**Chosen:** Default error correction = M (~15% data recovery).  
**Rejected:** L (7%, more data capacity), H (30%, max redundancy).  
**Why:** M is the QR standard's recommended default — good balance between data density and damage tolerance. H is useful for QR codes on physical objects (stickers, products) but adds ~30% more modules for the same data. Users who need higher redundancy can pass `--error H`.

## 8. No contact/vCard/geolocation encoders built-in

**Chosen:** Accept arbitrary text input; let users format their own vCards/MECARD.  
**Rejected:** Structured encoders for vCard, WiFi credentials, geo locations.  
**Why:** These add complexity (field validation, format negotiation) and are better handled by piping formatted text into qrcraft. A user who wants a WiFi QR code can pipe `WIFI:S:MyNetwork;T:WPA;P:pass;;` into the tool. The UNIX philosophy applies: do one thing well.

## 9. Tests: pytest with tempfile fixtures, not mocking

**Chosen:** Real file I/O with `tempfile` + `pytest`.  
**Rejected:** Mocking `qrcode.make_image` and `PIL.Image.save`.  
**Why:** QR code generation is deterministic and fast (~50ms per code). Using real files catches encoding/save issues that mocking would miss. The one mock-like test (stdout capture) exists only because stdout is the implicit "no output path" default.

## 10. `encode` and `decode` as subcommands, not separate scripts

**Chosen:** Single `qrcraft` command with `encode`/`decode` subcommands.  
**Rejected:** Two separate scripts (`qr-encode`, `qr-decode`).  
**Why:** A unified CLI is easier to discover, tab-complete, and document. Subcommands keep the mental model clean: `qrcraft encode ...` / `qrcraft decode ...`. Aliases (`e`, `d`) shorten common invocations.

## 11. No dependency on `opencv-python` for QR decoding

**Chosen:** Skip OpenCV despite its built-in QR decoder.  
**Rejected:** Using `cv2.QRCodeDetector` for decode.  
**Why:** OpenCV adds ~40 MB to the install and pulls in NumPy transitively. For a CLI utility, that's disproportionate — especially since `zbarimg` does the job in 200 KB. Users who need offline decode can install `zbar-tools`.

## 12. Setup: `pyproject.toml` (PEP 621), not `setup.py`

**Chosen:** Modern PEP 621 `pyproject.toml` with `[project.scripts]`.  
**Rejected:** Legacy `setup.py`, `setup.cfg`.  
**Why:** PEP 621 is the modern Python packaging standard. `pyproject.toml` requires less boilerplate, supports declarative metadata, and works with both `pip install -e .` and build tools like `build`.

## 13. Batch mode as `--batch` flag, not separate subcommand

**Chosen:** `qrcraft encode "item1" --batch "item2" "item3"`.  
**Rejected:** Separate `qrcraft batch` subcommand.  
**Why:** Batch encoding is a variant of encode, not a different operation. Using `--batch` keeps parameter inheritance (same `--error`, `--box-size` for all items) and avoids code duplication.

## 14. Output file extension determines format

**Chosen:** If output path ends in `.svg`, generate SVG; `.jpg`/`.jpeg` → JPEG; `.png` → PNG.  
**Rejected:** Explicit `--format` flag.  
**Why:** Convention-over-configuration. The file extension is the standard way to express format intent. An explicit flag would only add confusion when the extension and flag disagree. `qrcode`'s image factory already routes to `save()` which respects the extension.