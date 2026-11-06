"""QR code decoding — read QR codes from image files."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional


def decode(image_path: str, *, timeout: int = 15) -> list[dict]:
    """Read QR code(s) from *image_path*.

    Returns a list of decoded payloads::

        [{"data": "https://...", "type": "QRCODE"}, ...]

    An empty list means no QR code was found.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    results = []

    # Strategy 1: system zbarimg (fastest, most reliable)
    if _try_zbarimg(path, results):
        return results

    # Strategy 2: pyzbar if libzbar is loadable
    if _try_pyzbar(path, results):
        return results

    # Strategy 3: free online API (zxing.org)
    if _try_online_api(path, results, timeout=timeout):
        return results

    return results


def _try_zbarimg(path: Path, results: list) -> bool:
    """Attempt decode via zbarimg CLI (from zbar-tools package)."""
    try:
        r = subprocess.run(
            ["zbarimg", "--quiet", str(path)],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            for line in r.stdout.strip().splitlines():
                line = line.strip()
                if ":" in line:
                    _, data = line.split(":", 1)
                    results.append({"data": data.strip(), "type": "QRCODE"})
            return bool(results)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return False


def _try_pyzbar(path: Path, results: list) -> bool:
    """Attempt decode via pyzbar (Python ctypes binding)."""
    try:
        from pyzbar.pyzbar import scan
        # scan expects a PIL Image
        from PIL import Image
        img = Image.open(path)
        decoded = scan(img)
        if decoded:
            for item in decoded:
                data = item.data.decode("utf-8", errors="replace") if isinstance(item.data, bytes) else str(item.data)
                results.append({"data": data, "type": item.type if hasattr(item, "type") else "QRCODE"})
            return True
    except Exception:
        pass
    return False


def _try_online_api(path: Path, results: list, timeout: int = 15) -> bool:
    """Attempt decode via a free online QR decoding API.

    Uses zxing.org as the primary decoder (no auth key needed).
    """
    try:
        import requests
        # Try zxing.org decode API
        with open(path, "rb") as f:
            resp = requests.post(
                "https://zxing.org/w/decode",
                files={"f": f},
                timeout=timeout,
            )
        if resp.status_code == 200:
            # zxing returns JSON with the decoded text
            data = resp.json()
            if data.get("decoded"):
                for item in data["decoded"]:
                    results.append({"data": str(item), "type": "QRCODE"})
                return bool(results)
    except Exception:
        pass
    return False