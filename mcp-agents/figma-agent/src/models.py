"""Pydantic models for Figma MCP Agent request/response payloads."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FigmaFile(BaseModel):
    """Metadata about a Figma file."""
    file_key: str
    name: str = ""
    last_modified: str = ""
    thumbnail_url: str = ""
    version: str = ""
    role: str = ""


class FigmaNode(BaseModel):
    """A single Figma node (frame, layer, component, etc.)."""
    id: str
    name: str
    node_type: str = ""
    visible: bool = True
    bounding_box: Dict[str, float] = Field(default_factory=dict)
    absolute_bounding_box: Dict[str, float] = Field(default_factory=dict)
    fills: List[Dict[str, Any]] = Field(default_factory=list)
    strokes: List[Dict[str, Any]] = Field(default_factory=list)
    effects: List[Dict[str, Any]] = Field(default_factory=list)
    children: List[FigmaNode] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)


class DesignSpec(BaseModel):
    """Structured design specification for a frame or layer."""
    node_id: str
    node_name: str = ""
    node_type: str = ""
    width: Optional[float] = None
    height: Optional[float] = None
    fills: List[Dict[str, Any]] = Field(default_factory=list)
    strokes: List[Dict[str, Any]] = Field(default_factory=list)
    corner_radius: Optional[float] = None
    opacity: float = 1.0
    effects: List[Dict[str, Any]] = Field(default_factory=list)
    layout: Dict[str, Any] = Field(default_factory=dict)
    typography: List[Dict[str, Any]] = Field(default_factory=list)
    children: List[Dict[str, Any]] = Field(default_factory=list)


class StyleToken(BaseModel):
    """A single design token (color, typography, or spacing)."""
    type: str  # "color", "typography", "spacing"
    name: str = ""
    value: str = ""
    category: str = ""
    css_var: str = ""
    tailwind_class: str = ""
    figma_node_id: str = ""


class ExportResult(BaseModel):
    """Result of an export operation."""
    node_id: str
    format: str
    url: str = ""
    scale: float = 1.0
    success: bool = True


class DesignVersion(BaseModel):
    """A Figma file version entry."""
    id: str
    label: str = ""
    description: str = ""
    created_at: str = ""
    user_name: str = ""