"""Design spec extraction from Figma node data.

Pull dimensions, colors, fonts, spacing, and effects from Figma's document JSON.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import DesignSpec


def extract_specs(node: Dict[str, Any]) -> DesignSpec:
    """Extract a structured design spec from a single Figma node.

    Walks fills, strokes, effects, style (typography), and layout constraints.
    """
    bounding = node.get("absoluteBoundingBox", {})
    layout = {
        "constraints": node.get("constraints", {}),
        "layoutMode": node.get("layoutMode", ""),
        "itemSpacing": node.get("itemSpacing", 0),
        "paddingLeft": node.get("paddingLeft", 0),
        "paddingRight": node.get("paddingRight", 0),
        "paddingTop": node.get("paddingTop", 0),
        "paddingBottom": node.get("paddingBottom", 0),
        "counterAxisSizingMode": node.get("counterAxisSizingMode", ""),
        "primaryAxisSizingMode": node.get("primaryAxisSizingMode", ""),
    }

    typography = _extract_typography(node.get("style", {}))

    children = [
        {
            "id": c.get("id", ""),
            "name": c.get("name", ""),
            "type": c.get("type", ""),
            "visible": c.get("visible", True),
        }
        for c in node.get("children", [])
    ]

    return DesignSpec(
        node_id=node.get("id", ""),
        node_name=node.get("name", ""),
        node_type=node.get("type", ""),
        width=bounding.get("width"),
        height=bounding.get("height"),
        fills=_summarize_fills(node.get("fills", [])),
        strokes=_summarize_strokes(node.get("strokes", [])),
        corner_radius=_get_corner_radius(node),
        opacity=node.get("opacity", 1.0),
        effects=_summarize_effects(node.get("effects", [])),
        layout=layout,
        typography=typography,
        children=children,
    )


def extract_component_specs(
    component: Dict[str, Any],
) -> List[DesignSpec]:
    """Extract specs for a component and all of its variant children.

    Returns one spec per variant (or just the component itself if it has no
    variant properties).
    """
    specs: List[DesignSpec] = []

    # The component node itself
    component_node = component.get("node", component)
    specs.append(extract_specs(component_node))

    # Extract specs for variant children
    for child in component_node.get("children", []):
        if child.get("type") in ("COMPONENT_SET", "COMPONENT"):
            specs.append(extract_specs(child))

    return specs


def spec_to_markdown(spec: DesignSpec) -> str:
    """Render a DesignSpec as readable Markdown."""
    lines: List[str] = []
    lines.append(f"## {spec.node_name}")
    lines.append(f"- **Node ID:** `{spec.node_id}`")
    lines.append(f"- **Type:** {spec.node_type}")

    if spec.width is not None and spec.height is not None:
        lines.append(
            f"- **Dimensions:** {spec.width:.0f} × {spec.height:.0f} px"
        )
    if spec.opacity < 1.0:
        lines.append(f"- **Opacity:** {spec.opacity * 100:.0f}%")

    # Fills
    if spec.fills:
        lines.append("")
        lines.append("### Fills")
        for fill in spec.fills:
            color_str = _fill_color_str(fill)
            lines.append(f"- {fill.get('type', 'unknown')} {color_str}")

    # Strokes
    if spec.strokes:
        lines.append("")
        lines.append("### Strokes")
        for stroke in spec.strokes:
            color_str = _fill_color_str(stroke)
            weight = stroke.get("weight", {})
            px = weight.get("thickness", "?")
            lines.append(
                f"- {stroke.get('type', 'unknown')} {color_str}, "
                f"weight: {px}px"
            )

    # Corner radius
    if spec.corner_radius is not None and spec.corner_radius > 0:
        lines.append("")
        lines.append(f"- **Corner radius:** {spec.corner_radius:.0f}px")

    # Effects
    if spec.effects:
        lines.append("")
        lines.append("### Effects")
        for ef in spec.effects:
            lines.append(
                f"- {ef.get('type', 'unknown')}: "
                f"offset ({ef.get('offset', {}).get('x', 0)}, "
                f"{ef.get('offset', {}).get('y', 0)}), "
                f"radius {ef.get('radius', 0)}, "
                f"{_fill_color_str(ef)}"
            )

    # Typography
    if spec.typography:
        lines.append("")
        lines.append("### Typography")
        for t in spec.typography:
            for k, v in t.items():
                lines.append(f"- **{k}:** {v}")

    # Children
    if spec.children:
        lines.append("")
        lines.append(f"### Children ({len(spec.children)})")
        for c in spec.children:
            vis = "visible" if c.get("visible", True) else "hidden"
            lines.append(f"- `{c['id']}` {c['name']} ({c['type']}, {vis})")

    lines.append("")
    return "\n".join(lines)


# ----------------------------------------------------------------- internal


def _summarize_fills(fills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract visible fill info for the spec summary."""
    result = []
    for f in fills:
        if not f.get("visible", True):
            continue
        result.append(
            {
                "type": f.get("type", ""),
                "opacity": f.get("opacity", 1.0),
                "color": f.get("color", {}),
            }
        )
    return result


def _summarize_strokes(
    strokes: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Extract visible stroke info for the spec summary."""
    result = []
    for s in strokes:
        if not s.get("visible", True):
            continue
        result.append(
            {
                "type": s.get("type", ""),
                "opacity": s.get("opacity", 1.0),
                "color": s.get("color", {}),
                "weight": s.get("weight", {}),
            }
        )
    return result


def _fill_color_str(fill: Dict[str, Any]) -> str:
    """Return a readable color string from a fill/effect dict."""
    color = fill.get("color", {})
    if color:
        r = round(color.get("r", 0) * 255)
        g = round(color.get("g", 0) * 255)
        b = round(color.get("b", 0) * 255)
        a = fill.get("opacity", 1.0)
        if a < 1.0:
            return f"rgba({r}, {g}, {b}, {a})"
        return f"rgb({r}, {g}, {b})"
    return ""


def _summarize_effects(
    effects: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Extract effect info for the spec summary."""
    result = []
    for ef in effects:
        if not ef.get("visible", True):
            continue
        result.append(
            {
                "type": ef.get("type", ""),
                "offset": ef.get("offset", {}),
                "radius": ef.get("radius", 0),
                "spread": ef.get("spread", 0),
                "color": ef.get("color", {}),
                "opacity": ef.get("opacity", 1.0),
            }
        )
    return result


def _get_corner_radius(node: Dict[str, Any]) -> Optional[float]:
    """Extract corner radius from a node, handling mixed radii."""
    cr = node.get("cornerRadius")
    if cr is not None and isinstance(cr, (int, float)):
        return float(cr)
    # Individual corner radii
    for key in (
        "topLeftRadius",
        "topRightRadius",
        "bottomLeftRadius",
        "bottomRightRadius",
    ):
        val = node.get(key)
        if val is not None and val > 0:
            return float(val)
    return None


def _extract_typography(
    style: Dict[str, Any],
) -> List[Dict[str, str]]:
    """Extract typography properties from a node's style dict."""
    if not style:
        return []
    return [
        {
            "font_family": style.get("fontFamily", ""),
            "font_size": f"{style.get('fontSize', '?')}px",
            "font_weight": str(style.get("fontWeight", "?")),
            "line_height": f"{style.get('lineHeightPx', '?')}px",
            "letter_spacing": f"{style.get('letterSpacing', 0)}px",
            "text_align": style.get("textAlign", "left"),
        }
    ]