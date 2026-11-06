# Flow

## Execution Trace

```
CLI (argv)
  │
  ├─ qrcraft encode "https://..." -o qr.png
  │    └─ cli.main()
  │         └─ cli._handle_encode(args)
  │              └─ encode.encode(data, output, ...)
  │                   ├─ qrcode.QRCode()           ← create QR matrix
  │                   ├─ qr.add_data(data)         ← feed input data
  │                   ├─ qr.make(fit=True)         ← auto-select version
  │                   ├─ qr.make_image(...)        ← Pillow image from matrix
  │                   └─ img.save(output)          ← write to file or stdout
  │
  ├─ qrcraft encode "hello" --ascii
  │    └─ cli.main()
  │         └─ cli._handle_encode(args)
  │              └─ encode.encode(data, ascii=True)
  │                   ├─ qrcode.QRCode() + add_data + make
  │                   └─ encode._print_ascii(qr)
  │                        └─ qr.get_matrix()      ← boolean matrix
  │                        └─ print("██" if cell else "  ") for each row
  │
  ├─ qrcraft decode qr.png
  │    └─ cli.main()
  │         └─ cli._handle_decode(args)
  │              └─ decode.decode(image_path)
  │                   ├─ _try_zbarimg()            ❶ fastest
  │                   │    └─ subprocess.run(["zbarimg", path])
  │                   ├─ _try_pyzbar()             ❷ ctypes binding
  │                   │    └─ pyzbar.pyzbar.scan(PIL.Image)
  │                   └─ _try_online_api()         ❸ network fallback
  │                        └─ requests.post("https://zxing.org/w/decode", files={"f": ...})
  │
  └─ echo "url" | qrcraft encode -o pipe.png
       └─ same as encode path, but data read from sys.stdin
```

## Module Dependency Graph

```
qrcraft/cli.py
  ├── qrcraft/encode.py
  │    └── qrcode          (PyPI)
  │    └── PIL             (Pillow, PyPI)
  │
  ├── qrcraft/decode.py
  │    ├── subprocess      (stdlib)      → zbarimg CLI
  │    ├── pyzbar.pyzbar   (PyPI)        → libzbar ctypes
  │    ├── PIL             (Pillow, PyPI) → image loading
  │    └── requests        (PyPI)        → online API fallback
  │
  └── qrcraft/__init__.py
```

## Data Flow

```
User Input ("https://example.com")
        │
        ▼
  ┌─────────────┐
  │ cli._handle_encode │
  │  parse CLI args    │
  └──────┬─────────────┘
         │ data, output, ascii, box_size, border, error_correction, colors
         ▼
  ┌──────────────┐
  │ encode.encode │
  │               │
  │  1. Create QRCode(data)         │
  │  2. qr.make(fit=True)           │  ← auto-version
  │  3. If ascii: _print_ascii()    │
  │     Else: make_image() → save() │
  └──────┬──────────────────────────┘
         │ PNG/SVG file OR stdout
         ▼
    Output: qr.png / terminal art
```

```
Image File (qr.png)
        │
        ▼
  ┌──────────────┐
  │ cli._handle_decode │
  │  parse CLI args    │
  └──────┬──────────────┘
         │ image_path, json, timeout
         ▼
  ┌────────────────────────┐
  │  decode.decode()       │
  │                        │
  │  Strategy pipeline:    │
  │   ❶ zbarimg (subproc) │  ← fastest, needs zbar-tools
  │   ❷ pyzbar (ctypes)   │  ← needs libzbar shared lib
  │   ❸ zxing.org (HTTP)  │  ← needs internet
  │                        │
  │  Returns list[dict]    │
  └──────┬─────────────────┘
         │ [{"data": "...", "type": "QRCODE"}, ...]
         ▼
    Output: "https://example.com"  OR  {"data": "...", ...}
```

## Key Functions

| Function | File | Called By | Purpose |
|---|---|---|---|
| `main(argv)` | `cli.py` | entry point | Parse CLI args, route to encode/decode handlers |
| `_handle_encode(args)` | `cli.py` | `main` | Extract encode params, call `encode.encode()` or `encode_many()` |
| `_handle_decode(args)` | `cli.py` | `main` | Extract decode params, call `decode.decode()`, format output |
| `encode(data, output, ...)` | `encode.py` | `_handle_encode` | Generate QR matrix, render as image or ASCII |
| `encode_many(items, ...)` | `encode.py` | `_handle_encode` | Batch encode → multiple files |
| `_print_ascii(qr)` | `encode.py` | `encode` | Render QR matrix to terminal using Unicode blocks |
| `decode(image_path, ...)` | `decode.py` | `_handle_decode` | Try 3 strategies to decode a QR image |
| `_try_zbarimg(path, results)` | `decode.py` | `decode` | Call zbarimg CLI, parse output |
| `_try_pyzbar(path, results)` | `decode.py` | `decode` | Use pyzbar ctypes binding with PIL image |
| `_try_online_api(path, results)` | `decode.py` | `decode` | POST image to zxing.org decode API |
| `build_parser()` | `cli.py` | import | Build argparse parser with encode/decode subcommands |