"""QR code generation — encode text / URLs into QR codes."""

import io
import sys
from typing import Optional

import qrcode
from qrcode.image.pil import PilImage
from qrcode.image.styledpil import StyledPilImage

# ── Public API ─────────────────────────────────────────────────────────────

def encode(
    data: str,
    output: Optional[str] = None,
    *,
    box_size: int = 10,
    border: int = 4,
    error_correction: str = "M",
    ascii: bool = False,
    fill_color: str = "#000000",
    back_color: str = "#FFFFFF",
) -> str:
    """Generate a QR code from *data*.

    Parameters
    ----------
    data : str
        Text or URL to encode.
    output : str or None
        File path to save the QR image.  ``None`` → print to stdout (ASCII
        when *ascii* is true, otherwise just report success).
        The file extension selects the format: ``.png``, ``.svg``, ``.jpg``.
    box_size : int
        Size of each QR module in pixels (default 10).
    border : int
        Width of the quiet-zone border in modules (default 4).
    error_correction : str
        ``"L"`` (≈7 %), ``"M"`` (≈15 %), ``"Q"`` (≈25 %), ``"H"`` (≈30 %).
    ascii : bool
        Print an ASCII-art representation to stdout instead of an image.
    fill_color, back_color : str
        QR foreground / background colours (hex or named).

    Returns
    -------
    str
        Path to the saved image, or ``"(stdout)"`` for ASCII mode.
    """
    ec_map = {"L": qrcode.constants.ERROR_CORRECT_L,
              "M": qrcode.constants.ERROR_CORRECT_M,
              "Q": qrcode.constants.ERROR_CORRECT_Q,
              "H": qrcode.constants.ERROR_CORRECT_H}
    ec = ec_map.get(error_correction.upper(), qrcode.constants.ERROR_CORRECT_M)

    qr = qrcode.QRCode(
        version=None,
        error_correction=ec,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # ── ASCII mode ─────────────────────────────────────────────────────
    if ascii:
        _print_ascii(qr)
        return "(stdout)"

    # ── Image mode ─────────────────────────────────────────────────────
    img = qr.make_image(
        image_factory=PilImage,
        fill_color=fill_color,
        back_color=back_color,
    )

    if output:
        img.save(output)
        return output

    # No output specified – print to stdout (base64 PNG in terminal)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    sys.stdout.buffer.write(buf.getvalue())
    return "(stdout)"


def encode_many(items: list[str], output_dir: str = ".", **kwargs) -> list[str]:
    """Generate one QR code per item in *items*.

    Saves each as ``qr-<N>.png`` in *output_dir*.
    Returns the list of created paths.
    """
    import os
    paths = []
    for i, item in enumerate(items):
        path = os.path.join(output_dir, f"qr-{i+1}.png")
        encode(item, output=path, **kwargs)
        paths.append(path)
    return paths


# ── Helpers ────────────────────────────────────────────────────────────────

def _print_ascii(qr) -> None:
    """Render the QR matrix as an ASCII block using Unicode upper-half blocks."""
    matrix = qr.get_matrix()
    sb = []
    for row in matrix:
        line = "".join("\u2588\u2588" if cell else "  " for cell in row)
        sb.append(line)
    sys.stdout.write("\n" + "\n".join(sb) + "\n")
    sys.stdout.flush()