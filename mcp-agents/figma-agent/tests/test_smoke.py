"""Smoke tests for the Figma MCP Agent.

Mocks the Figma API — no real credentials, no network.
Run with:  python tests/test_smoke.py   (also pytest-compatible)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import tools  # noqa: E402
from src.models import StyleToken  # noqa: E402

# ------------------------------------------------------------------ fake data

CANONICAL_FILE = {
    "name": "Landing Page v2",
    "lastModified": "2026-08-14T10:00:00Z",
    "thumbnailUrl": "https://figma.com/thumb.png",
    "version": "123456",
    "role": "viewer",
    "document": {
        "id": "0:0",
        "name": "Landing Page v2",
        "type": "DOCUMENT",
        "children": [
            {
                "id": "2:0",
                "name": "Page 1",
                "type": "CANVAS",
                "visible": True,
                "children": [
                    {
                        "id": "1:1",
                        "name": "Hero Section",
                        "type": "FRAME",
                        "visible": True,
                        "absoluteBoundingBox": {"width": 1440, "height": 600},
                        "fills": [
                            {
                                "type": "SOLID",
                                "visible": True,
                                "opacity": 1.0,
                                "color": {"r": 0.13, "g": 0.13, "b": 0.13},
                            }
                        ],
                        "strokes": [],
                        "effects": [],
                        "opacity": 1.0,
                        "constraints": {},
                        "children": [
                            {
                                "id": "1:2",
                                "name": "Headline",
                                "type": "TEXT",
                                "visible": True,
                                "absoluteBoundingBox": {"width": 600, "height": 48},
                                "fills": [
                                    {
                                        "type": "SOLID",
                                        "visible": True,
                                        "opacity": 1.0,
                                        "color": {"r": 1.0, "g": 1.0, "b": 1.0},
                                    }
                                ],
                                "strokes": [],
                                "effects": [],
                                "style": {
                                    "fontFamily": "Inter",
                                    "fontSize": 36,
                                    "fontWeight": 700,
                                    "lineHeightPx": 44,
                                    "letterSpacing": 0,
                                    "textAlign": "left",
                                },
                            }
                        ],
                    },
                    {
                        "id": "1:3",
                        "name": "Features Grid",
                        "type": "FRAME",
                        "visible": True,
                        "absoluteBoundingBox": {"width": 1440, "height": 400},
                        "fills": [
                            {
                                "type": "SOLID",
                                "visible": True,
                                "opacity": 1.0,
                                "color": {"r": 1.0, "g": 1.0, "b": 1.0},
                            }
                        ],
                        "strokes": [],
                        "effects": [],
                        "opacity": 1.0,
                        "constraints": {},
                        "children": [],
                    },
                ],
            },
        ],
    },
}

CANONICAL_NODES = {
    "nodes": {
        "1:1": {
            "document": {
                "id": "1:1",
                "name": "Hero Section",
                "type": "FRAME",
                "visible": True,
                "absoluteBoundingBox": {"width": 1440, "height": 600},
                "fills": [
                    {
                        "type": "SOLID",
                        "visible": True,
                        "opacity": 1.0,
                        "color": {"r": 0.13, "g": 0.13, "b": 0.13},
                    }
                ],
                "strokes": [],
                "effects": [],
                "opacity": 1.0,
                "constraints": {
                    "paddingLeft": 24,
                    "paddingRight": 24,
                    "paddingTop": 16,
                    "paddingBottom": 16,
                },
                "children": [],
            }
        }
    }
}

CANONICAL_IMAGES = {
    "err": None,
    "images": {
        "1:1": "https://figma.com/export/abc123/1:1.svg",
        "1:2": "https://figma.com/export/abc123/1:2.svg",
    },
}

CANONICAL_COMPONENT = {
    "component": {
        "key": "abc-def",
        "name": "Button/Primary",
        "description": "Primary call-to-action button",
        "type": "COMPONENT",
        "remote": False,
        "containingFrame": {"name": "Buttons", "pageId": "1:1"},
    }
}

CANONICAL_VERSIONS = {
    "versions": [
        {
            "id": "1234567890",
            "label": "v1",
            "description": "Initial design",
            "createdAt": "2026-08-01T09:00:00Z",
            "userName": "Alice",
        },
        {
            "id": "1234567891",
            "label": "v2",
            "description": "Updated hero section",
            "createdAt": "2026-08-14T10:00:00Z",
            "userName": "Bob",
        },
    ]
}


# ---------------------------------------------------------------- fake client


class FakeFigmaClient:
    """In-memory stand-in for src.figma_client.FigmaClient."""

    def __init__(self):
        self.files = {"abc123": CANONICAL_FILE}
        self.nodes = {"abc123": CANONICAL_NODES}
        self.images = {"abc123": CANONICAL_IMAGES}
        self.components = {"abc-def": CANONICAL_COMPONENT}
        self.versions = {"abc123": CANONICAL_VERSIONS}

    def get_file(self, file_key):
        return self.files[file_key]

    def get_file_nodes(self, file_key, node_id):
        return self.nodes[file_key]

    def get_images(self, file_key, node_ids, format="svg", scale=1.0):
        return self.images[file_key]

    def get_component(self, component_id):
        return self.components[component_id]

    def get_file_versions(self, file_key):
        return self.versions[file_key]


def setup():
    tools._client = FakeFigmaClient()


# ------------------------------------------------------------------ tests


def test_get_design_specs_full_file():
    result = tools.get_design_specs("abc123")
    assert result["file_key"] == "abc123"
    assert len(result["frames"]) == 2
    assert result["frames"][0]["node_name"] == "Hero Section"
    assert result["frames"][0]["width"] == 1440
    assert result["frames"][0]["height"] == 600


def test_get_design_specs_single_node():
    result = tools.get_design_specs("abc123", node_id="1:1")
    assert result["node_name"] == "Hero Section"
    assert result["node_id"] == "1:1"
    assert result["node_type"] == "FRAME"
    assert result["width"] == 1440
    assert result["height"] == 600


def test_export_asset_returns_url():
    result = tools.export_asset("abc123", "1:1", format="svg")
    assert result["node_id"] == "1:1"
    assert result["format"] == "svg"
    assert result["success"] is True
    assert "figma.com/export" in result["url"]


def test_export_asset_png_with_scale():
    result = tools.export_asset("abc123", "1:2", format="png", scale=2.0)
    assert result["format"] == "png"
    assert result["scale"] == 2.0
    assert result["success"] is True


def test_list_frames_and_layers():
    result = tools.list_frames_and_layers("abc123")
    assert result["file_key"] == "abc123"
    assert result["file_name"] == "Landing Page v2"
    assert len(result["frames"]) == 2
    # Hero Section has a child (Headline text)
    hero = result["frames"][0]
    assert hero["type"] == "FRAME"
    assert hero["name"] == "Hero Section"
    assert hero["children_count"] == 1
    assert hero["children"][0]["name"] == "Headline"


def test_get_component_properties():
    result = tools.get_component_properties("abc-def")
    assert result["component_id"] == "abc-def"
    assert result["name"] == "Button/Primary"
    assert result["description"] == "Primary call-to-action button"
    assert result["type"] == "COMPONENT"


def test_extract_style_tokens():
    result = tools.extract_style_tokens("abc123")
    assert result["file_key"] == "abc123"
    assert result["token_count"] > 0
    # Should have color tokens (dark fill, white fill)
    colors = [t for t in result["tokens"] if t["type"] == "color"]
    assert len(colors) >= 1
    # Should have typography tokens from the Headline text node
    typo = [t for t in result["tokens"] if t["type"] == "typography"]
    assert len(typo) >= 1
    # CSS output should be non-empty
    assert ":root {" in result["css"]
    assert "--figma-" in result["css"]


def test_get_design_diff():
    result = tools.get_design_diff("abc123", "v1", "v2")
    assert result["file_key"] == "abc123"
    assert result["version_a"] == "v1"
    assert result["version_b"] == "v2"
    assert result["version_a_found"] is True
    assert result["version_b_found"] is True
    assert result["version_a_label"] == "v1"
    assert result["version_b_label"] == "v2"


# ------------------------------------------------------------------ runner

TESTS = [
    test_get_design_specs_full_file,
    test_get_design_specs_single_node,
    test_export_asset_returns_url,
    test_export_asset_png_with_scale,
    test_list_frames_and_layers,
    test_get_component_properties,
    test_extract_style_tokens,
    test_get_design_diff,
]


def main() -> int:
    failed = 0
    for fn in TESTS:
        setup()
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL  {fn.__name__}: {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"ERROR {fn.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} smoke tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())