"""MCP tool surface for the Figma Agent.

Tools are plain functions (easy to unit-test) that get registered on a FastMCP
server by `register()`. The Figma client is a module-level singleton that tests
can replace with a fake.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import figma_client, specs, tokens
from .models import DesignSpec, ExportResult, FigmaFile, FigmaNode, StyleToken

_client: Optional[figma_client.FigmaClient] = None


def get_client() -> figma_client.FigmaClient:
    """Lazily build (or reuse) the Figma client. Tests replace `tools._client`."""
    global _client
    if _client is None:
        _client = figma_client.FigmaClient()
    return _client


# ------------------------------------------------------------------ tools


def get_design_specs(
    file_key: str, node_id: Optional[str] = None
) -> Dict[str, Any]:
    """Extract structured design specs from a Figma file.

    When node_id is omitted, returns specs for every top-level canvas/frame.
    When node_id is provided, returns a single spec for that node.

    Returns dicts with widths, heights, fills (colors), strokes, corner
    radius, opacity, effects, layout constraints, typography, and children.
    """
    if node_id:
        data = get_client().get_file_nodes(file_key, node_id)
        nodes = data.get("nodes", {})
        node_data = nodes.get(node_id, {})
        doc = node_data.get("document", {})
        return specs.extract_specs(doc).model_dump()

    # Full file — walk top-level canvas frames
    data = get_client().get_file(file_key)
    doc = data.get("document", {})
    canvases = doc.get("children", [])
    results: List[Dict[str, Any]] = []
    for canvas in canvases:
        for child in canvas.get("children", []):
            results.append(specs.extract_specs(child).model_dump())
    return {"file_key": file_key, "frames": results}


def export_asset(
    file_key: str,
    node_id: str,
    format: str = "svg",
    scale: float = 1.0,
) -> Dict[str, Any]:
    """Get an export URL for a specific node in a Figma file.

    format: "svg" (default), "png", or "pdf"
    scale: export resolution multiplier (1.0, 2.0, 3.0, or 4.0)
    """
    result = get_client().get_images(
        file_key, [node_id], format=format, scale=scale
    )
    urls = result.get("images", {})
    return ExportResult(
        node_id=node_id,
        format=format,
        url=urls.get(node_id, ""),
        scale=scale,
        success=bool(urls.get(node_id)),
    ).model_dump()


def list_frames_and_layers(file_key: str) -> Dict[str, Any]:
    """List all top-level frames and their children in a Figma file.

    Returns a nested structure with id, name, type, and visibility for each
    frame and layer.
    """
    data = get_client().get_file(file_key)
    doc = data.get("document", {})
    canvases = doc.get("children", [])

    frames: List[Dict[str, Any]] = []
    for canvas in canvases:
        for child in canvas.get("children", []):
            frame = _summarize_node(child, depth=0)
            if frame:
                frames.append(frame)

    file_name = data.get("name", "")
    return {
        "file_key": file_key,
        "file_name": file_name,
        "frames": frames,
    }


def get_component_properties(component_id: str) -> Dict[str, Any]:
    """Get metadata and variant properties for a Figma component.

    Returns name, type, description, and variant properties.
    """
    data = get_client().get_component(component_id)
    component = data.get("component", data)
    return {
        "component_id": component_id,
        "name": component.get("name", ""),
        "description": component.get("description", ""),
        "type": component.get("type", ""),
        "containing_frame": component.get("containingFrame", {}),
        "remote": component.get("remote", False),
        "key": component.get("key", ""),
    }


def extract_style_tokens(file_key: str) -> Dict[str, Any]:
    """Extract style tokens (colors, typography, spacing) from a Figma file.

    Returns organized tokens plus CSS, Tailwind, and JSON serializations.
    """
    data = get_client().get_file(file_key)
    doc = data.get("document", {})

    all_tokens: List[StyleToken] = []

    def walk(node: Dict[str, Any]) -> None:
        all_tokens.extend(tokens.extract_color_tokens(node))
        all_tokens.extend(tokens.extract_typography_tokens(node))
        all_tokens.extend(tokens.extract_spacing_tokens(node))
        for child in node.get("children", []):
            walk(child)

    for canvas in doc.get("children", []):
        walk(canvas)

    return {
        "file_key": file_key,
        "token_count": len(all_tokens),
        "tokens": [t.model_dump() for t in all_tokens],
        "css": tokens.tokens_to_css(all_tokens),
        "tailwind_config": tokens.tokens_to_tailwind(all_tokens),
        "json": tokens.tokens_to_json(all_tokens),
    }


def get_design_diff(
    file_key: str, version_a: str, version_b: str
) -> Dict[str, Any]:
    """Compare two versions of a Figma file and report what changed.

    version_a and version_b are version IDs from the file's version history.
    Returns lists of added, removed, and changed frames/layers.
    """
    versions_data = get_client().get_file_versions(file_key)
    versions = versions_data.get("versions", [])

    # Find the two requested versions
    v_a: Optional[Dict[str, Any]] = None
    v_b: Optional[Dict[str, Any]] = None
    for v in versions:
        if v.get("id") == version_a or v.get("label", "") == version_a:
            v_a = v
        if v.get("id") == version_b or v.get("label", "") == version_b:
            v_b = v

    return {
        "file_key": file_key,
        "version_a": version_a,
        "version_b": version_b,
        "version_a_found": v_a is not None,
        "version_b_found": v_b is not None,
        "version_a_label": (v_a or {}).get("label", ""),
        "version_b_label": (v_b or {}).get("label", ""),
        "version_a_created": (v_a or {}).get("createdAt", ""),
        "version_b_created": (v_b or {}).get("createdAt", ""),
        "added": [],
        "removed": [],
        "changed": [],
        "note": (
            "Detailed node-level diff requires fetching both file versions "
            "and comparing their document trees. This is a placeholder "
            "showing version metadata."
        ),
    }


# ------------------------------------------------------------------ helpers


def _summarize_node(
    node: Dict[str, Any], depth: int = 0
) -> Optional[Dict[str, Any]]:
    """Recursively summarise a node for listing."""
    if not node:
        return None
    result: Dict[str, Any] = {
        "id": node.get("id", ""),
        "name": node.get("name", ""),
        "type": node.get("type", ""),
        "visible": node.get("visible", True),
        "depth": depth,
    }
    children = node.get("children", [])
    if children:
        result["children"] = [
            _summarize_node(c, depth=depth + 1) for c in children
        ]
        result["children_count"] = len(children)
    return result


# ------------------------------------------------------------------ wiring


def register(mcp) -> None:
    """Register every tool on a FastMCP server instance."""
    mcp.tool()(get_design_specs)
    mcp.tool()(export_asset)
    mcp.tool()(list_frames_and_layers)
    mcp.tool()(get_component_properties)
    mcp.tool()(extract_style_tokens)
    mcp.tool()(get_design_diff)