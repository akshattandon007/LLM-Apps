"""Generate SketchIt extension icons (Notion-inspired).

A dark rounded-square with a pencil/sketch mark. Rendered with PIL at high
resolution then downsampled for crisp edges at small sizes.
"""
from PIL import Image, ImageDraw
import os

OUT = os.path.join(os.path.dirname(__file__), "icons")
os.makedirs(OUT, exist_ok=True)

SIZES = [16, 32, 48, 128]

# Supersample for clean anti-aliasing
SS = 8

def make_icon(size: int) -> Image.Image:
    s = size * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Background: near-black rounded square (Notion vibes)
    radius = int(s * 0.22)
    d.rounded_rectangle([0, 0, s, s], radius=radius, fill=(31, 33, 40, 255))

    # Pencil / sketch mark — same geometry as the widget SVG.
    # Scale to the icon canvas. Stroke width is a fraction of the size.
    stroke = max(2, int(s * 0.075))
    white = (255, 255, 255, 255)

    # The path (from the SVG) in a 24-unit system:
    #   M 4 20 L 4 16 L 16 4 L 20 8 L 8 20 Z
    #   M 14 6 L 18 10
    #   M 4 20 L 8 20
    unit = s / 24.0
    p = lambda x, y: (x * unit, y * unit)

    # Main pencil outline (closed)
    outline = [p(4, 20), p(4, 16), p(16, 4), p(20, 8), p(8, 20)]
    d.line(outline + [outline[0]], fill=white, width=stroke, joint="curve")

    # Ferrule crossline
    d.line([p(14, 6), p(18, 10)], fill=white, width=stroke)

    # Base line
    d.line([p(4, 20), p(8, 20)], fill=white, width=stroke)

    # Downsample
    return img.resize((size, size), Image.LANCZOS)


for sz in SIZES:
    icon = make_icon(sz)
    path = os.path.join(OUT, f"icon{sz}.png")
    icon.save(path, "PNG")
    print(f"Wrote {path}")

print("Done.")
