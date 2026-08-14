"""Style token extraction from Figma node data.

Parse Figma's paint/fill data into CSS color values, font data into Tailwind
classes, and spacing into rem values.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .models import StyleToken

# ------------------------------------------------------------------- colors


def _rgba_to_css(r: float, g: float, b: float, a: float) -> str:
    """Convert RGBA floats (0-1 range) to a CSS color string."""
    r_int = round(r * 255)
    g_int = round(g * 255)
    b_int = round(b * 255)
    if a < 1.0:
        return f"rgba({r_int}, {g_int}, {b_int}, {a})"
    return f"rgb({r_int}, {g_int}, {b_int})"


def _parse_fill_paint(fill: Dict[str, Any]) -> Optional[str]:
    """Extract a CSS color string from a Figma fill paint object."""
    paint_type = fill.get("type", "")
    if paint_type == "SOLID":
        color = fill.get("color", {})
        opacity = fill.get("opacity", 1.0)
        return _rgba_to_css(
            color.get("r", 0),
            color.get("g", 0),
            color.get("b", 0),
            opacity,
        )
    # Gradient / image / video fills are not reduced to a single color here
    return None


def extract_color_tokens(node: Dict[str, Any]) -> List[StyleToken]:
    """Extract color tokens from a Figma node's fills and strokes."""
    tokens: List[StyleToken] = []
    node_name = node.get("name", "")

    for fill in node.get("fills", []):
        css_color = _parse_fill_paint(fill)
        if css_color is None:
            continue
        visible = fill.get("visible", True)
        if not visible:
            continue
        tokens.append(
            StyleToken(
                type="color",
                name=f"{node_name}/fill",
                value=css_color,
                category="fill",
                css_var=f"--figma-{_slugify(node_name)}-fill",
                tailwind_class=_color_to_tailwind(css_color),
                figma_node_id=node.get("id", ""),
            )
        )

    for stroke in node.get("strokes", []):
        css_color = _parse_fill_paint(stroke)
        if css_color is None:
            continue
        tokens.append(
            StyleToken(
                type="color",
                name=f"{node_name}/stroke",
                value=css_color,
                category="stroke",
                css_var=f"--figma-{_slugify(node_name)}-stroke",
                tailwind_class=_color_to_tailwind(css_color),
                figma_node_id=node.get("id", ""),
            )
        )

    return tokens


# --------------------------------------------------------------- typography


def _extract_font_info(
    style: Dict[str, Any],
) -> Dict[str, str]:
    """Pull CSS-printable font info from a Figma type style dict."""
    info: Dict[str, str] = {}
    font_family = style.get("fontFamily", "")
    font_postscript = style.get("fontPostScriptName", "")
    info["font_family"] = font_family or font_postscript or "sans-serif"
    info["font_size"] = f"{style.get('fontSize', 16)}px"
    info["font_weight"] = str(style.get("fontWeight", 400))
    info["line_height"] = (
        f"{style.get('lineHeightPx', 1.2 * style.get('fontSize', 16))}px"
    )
    info["letter_spacing"] = f"{style.get('letterSpacing', 0)}px"
    info["text_align"] = style.get("textAlign", "left")
    return info


def _font_to_tailwind(
    font_family: str, font_size: float, font_weight: int
) -> str:
    """Map Figma font data to the closest Tailwind utility class."""
    # font-size mapping (approximate)
    size_map: Dict[float, str] = {
        10: "text-xs",
        12: "text-xs",
        14: "text-sm",
        16: "text-base",
        18: "text-lg",
        20: "text-xl",
        24: "text-2xl",
        30: "text-3xl",
        36: "text-4xl",
        48: "text-5xl",
        60: "text-6xl",
        72: "text-7xl",
        96: "text-8xl",
    }
    size_class = "text-base"
    for px in sorted(size_map.keys(), reverse=True):
        if font_size >= px:
            size_class = size_map[px]
            break

    # font-weight mapping
    weight_map = {
        100: "font-thin",
        200: "font-extralight",
        300: "font-light",
        400: "font-normal",
        500: "font-medium",
        600: "font-semibold",
        700: "font-bold",
        800: "font-extrabold",
        900: "font-black",
    }
    weight_class = weight_map.get(font_weight, "font-normal")

    return f"{size_class} {weight_class}"


def extract_typography_tokens(node: Dict[str, Any]) -> List[StyleToken]:
    """Extract typography tokens from a Figma node's style data."""
    tokens: List[StyleToken] = []
    node_name = node.get("name", "")
    style = node.get("style", {})
    if not style:
        return tokens

    font_info = _extract_font_info(style)
    font_family = font_info.get("font_family", "sans-serif")
    font_size = float(style.get("fontSize", 16))
    font_weight = int(style.get("fontWeight", 400))
    slug = _slugify(node_name)

    tokens.append(
        StyleToken(
            type="typography",
            name=f"{node_name}/font-family",
            value=font_family,
            category="font-family",
            css_var=f"--figma-{slug}-font-family",
            tailwind_class=_family_to_tailwind(font_family),
            figma_node_id=node.get("id", ""),
        )
    )
    tokens.append(
        StyleToken(
            type="typography",
            name=f"{node_name}/font-size",
            value=font_info["font_size"],
            category="font-size",
            css_var=f"--figma-{slug}-font-size",
            tailwind_class=_font_to_tailwind(font_family, font_size, font_weight),
            figma_node_id=node.get("id", ""),
        )
    )
    tokens.append(
        StyleToken(
            type="typography",
            name=f"{node_name}/line-height",
            value=font_info["line_height"],
            category="line-height",
            css_var=f"--figma-{slug}-line-height",
            tailwind_class="",
            figma_node_id=node.get("id", ""),
        )
    )
    tokens.append(
        StyleToken(
            type="typography",
            name=f"{node_name}/letter-spacing",
            value=font_info["letter_spacing"],
            category="letter-spacing",
            css_var=f"--figma-{slug}-letter-spacing",
            tailwind_class=_tracking_to_tailwind(
                float(style.get("letterSpacing", 0))
            ),
            figma_node_id=node.get("id", ""),
        )
    )

    return tokens


def _family_to_tailwind(family: str) -> str:
    """Map a font family to a Tailwind font-family utility."""
    low = family.lower()
    if "inter" in low or "sans" in low:
        return "font-sans"
    if "serif" in low:
        return "font-serif"
    if "mono" in low or "code" in low:
        return "font-mono"
    return "font-sans"


def _tracking_to_tailwind(spacing: float) -> str:
    """Map letter-spacing px to Tailwind tracking class."""
    if spacing >= 0.1:
        return "tracking-wide"
    elif spacing <= -0.1:
        return "tracking-tight"
    return "tracking-normal"


# ---------------------------------------------------------------- spacing


def _px_to_rem(px: float) -> str:
    """Convert px to rem (assuming 16px base)."""
    rem = px / 16.0
    return f"{rem:.4f}rem"


def _spacing_to_tailwind(px: float) -> str:
    """Map px spacing to the closest Tailwind spacing class."""
    # Approximate Tailwind spacing scale (in px at 1rem=16px)
    scale: Dict[int, str] = {
        0: "p-0",
        1: "p-px",
        4: "p-1",
        8: "p-2",
        12: "p-3",
        16: "p-4",
        20: "p-5",
        24: "p-6",
        32: "p-8",
        40: "p-10",
        48: "p-12",
        64: "p-16",
        80: "p-20",
        96: "p-24",
    }
    closest = "p-4"
    for px_val in sorted(scale.keys(), reverse=True):
        if px >= px_val:
            closest = scale[px_val]
            break
    return closest


def extract_spacing_tokens(node: Dict[str, Any]) -> List[StyleToken]:
    """Extract spacing tokens from a Figma node's layout constraints."""
    tokens: List[StyleToken] = []
    node_name = node.get("name", "")
    slug = _slugify(node_name)
    ab = node.get("absoluteBoundingBox", {})

    # Extract padding-like values from constraints
    constraints = node.get("constraints", {})
    for key in ("paddingLeft", "paddingRight", "paddingTop", "paddingBottom"):
        val = constraints.get(key)
        if val is not None:
            tokens.append(
                StyleToken(
                    type="spacing",
                    name=f"{node_name}/{key}",
                    value=_px_to_rem(float(val)),
                    category=key,
                    css_var=f"--figma-{slug}-{key}",
                    tailwind_class=_spacing_to_tailwind(float(val)),
                    figma_node_id=node.get("id", ""),
                )
            )

    # Also add width/height as spacing tokens for reference
    for dim in ("width", "height"):
        val = ab.get(dim)
        if val is not None:
            tokens.append(
                StyleToken(
                    type="spacing",
                    name=f"{node_name}/{dim}",
                    value=_px_to_rem(float(val)),
                    category=dim,
                    css_var=f"--figma-{slug}-{dim}",
                    tailwind_class=_spacing_to_tailwind(float(val)),
                    figma_node_id=node.get("id", ""),
                )
            )

    return tokens


# ----------------------------------------------------------- format helpers


def tokens_to_css(tokens: List[StyleToken]) -> str:
    """Format tokens as CSS custom properties."""
    lines: List[str] = [":root {"]
    for t in tokens:
        if t.css_var:
            lines.append(f"  {t.css_var}: {t.value};")
    lines.append("}")
    return "\n".join(lines)


def tokens_to_tailwind(tokens: List[StyleToken]) -> str:
    """Format tokens as a JSON mapping for Tailwind config extension."""
    import json

    tailwind_config: Dict[str, Any] = {
        "colors": {},
        "fontFamily": {},
        "fontSize": {},
        "spacing": {},
    }
    for t in tokens:
        if t.type == "color" and t.category == "fill":
            safe = _safe_tailwind_key(t.name)
            tailwind_config["colors"][safe] = t.value
        elif t.type == "typography" and t.category == "font-family":
            safe = _safe_tailwind_key(t.name)
            tailwind_config["fontFamily"][safe] = t.value
        elif t.type == "typography" and t.category == "font-size":
            safe = _safe_tailwind_key(t.name)
            tailwind_config["fontSize"][safe] = t.value
        elif t.type == "spacing":
            safe = _safe_tailwind_key(t.name)
            tailwind_config["spacing"][safe] = t.value
    return json.dumps(tailwind_config, indent=2)


def tokens_to_json(tokens: List[StyleToken]) -> str:
    """Format tokens as a generic JSON array."""
    import json

    return json.dumps(
        [t.model_dump() for t in tokens], indent=2
    )


# --------------------------------------------------------------- utilities


def _slugify(name: str) -> str:
    """Turn a Figma node name into a CSS-safe slug."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def _safe_tailwind_key(name: str) -> str:
    """Turn a token name into a Tailwind-safe key."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def _color_to_tailwind(css_color: str) -> str:
    """Map a CSS color to the closest Tailwind color name (best effort)."""
    # Parse RGB from the CSS string
    match = re.match(
        r"rgba?\((\d+),\s*(\d+),\s*(\d+)", css_color
    )
    if not match:
        return ""

    r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))

    # Very rough hue buckets — provides a starting point
    if r > 240 and g > 240 and b > 240:
        return "text-white"
    if r < 20 and g < 20 and b < 20:
        return "text-black"
    if r > 200 and g < 100 and b < 100:
        return "text-red-500"
    if r > 200 and g > 150 and b < 100:
        return "text-orange-500"
    if r > 220 and g > 220 and b < 120:
        return "text-yellow-500"
    if r < 100 and g > 180 and b < 100:
        return "text-green-500"
    if r < 100 and g < 100 and b > 200:
        return "text-blue-500"
    if r < 100 and g > 150 and b > 200:
        return "text-cyan-500"
    if r > 150 and g < 100 and b > 200:
        return "text-purple-500"
    if r > 200 and g < 100 and b > 150:
        return "text-pink-500"
    if r > 150 and g > 100 and b < 80:
        return "text-amber-500"
    if r < 80 and g > 100 and b > 150:
        return "text-teal-500"
    return ""