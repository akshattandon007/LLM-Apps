"""Figma REST API client.

Wrapper around the Figma API (v1) using the `requests` library.
Reads FIGMA_ACCESS_TOKEN from the environment.

https://www.figma.com/developers/api
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests

BASE_URL = "https://api.figma.com/v1"


class FigmaClient:
    """HTTP client for the Figma REST API v1."""

    def __init__(self, access_token: Optional[str] = None) -> None:
        self._access_token = access_token or os.environ.get(
            "FIGMA_ACCESS_TOKEN", ""
        )
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
            }
        )

    # ------------------------------------------------------------------ files

    def get_file(self, file_key: str) -> Dict[str, Any]:
        """Fetch the full document JSON for a Figma file.

        https://www.figma.com/developers/api#get-files-endpoint
        """
        resp = self._session.get(f"{BASE_URL}/files/{file_key}")
        resp.raise_for_status()
        return resp.json()

    def get_file_nodes(
        self, file_key: str, node_id: str
    ) -> Dict[str, Any]:
        """Fetch a specific node (and its children) from a file.

        https://www.figma.com/developers/api#get-file-nodes-endpoint
        """
        params = {"ids": node_id}
        resp = self._session.get(
            f"{BASE_URL}/files/{file_key}/nodes", params=params
        )
        resp.raise_for_status()
        return resp.json()

    # ---------------------------------------------------------------- images

    def get_images(
        self,
        file_key: str,
        node_ids: List[str],
        format: str = "svg",
        scale: float = 1.0,
    ) -> Dict[str, Any]:
        """Get export URLs for one or more nodes in a file.

        https://www.figma.com/developers/api#get-images-endpoint
        """
        params = {"ids": ",".join(node_ids), "format": format, "scale": scale}
        resp = self._session.get(
            f"{BASE_URL}/images/{file_key}", params=params
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------ components

    def get_component(self, component_id: str) -> Dict[str, Any]:
        """Fetch metadata about a component.

        https://www.figma.com/developers/api#get-component-endpoint
        """
        resp = self._session.get(
            f"{BASE_URL}/components/{component_id}"
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------- versions

    def get_file_versions(self, file_key: str) -> Dict[str, Any]:
        """Fetch the version history of a file.

        https://www.figma.com/developers/api#get-file-versions-endpoint
        """
        resp = self._session.get(
            f"{BASE_URL}/files/{file_key}/versions"
        )
        resp.raise_for_status()
        return resp.json()