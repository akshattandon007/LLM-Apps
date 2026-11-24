"""Data models for StoryWeaver."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Choice:
    """A branching choice available to the reader at a story node."""

    text: str
    next_node_id: int


@dataclass
class StoryNode:
    """A single story chapter/scene with choices."""

    id: int
    narrative: str
    choices: list[Choice] = field(default_factory=list)


@dataclass
class StorySession:
    """Complete state of a reader's interactive fiction session."""

    title: str
    genre: str
    setting: str
    characters: str
    premise: str
    nodes: list[StoryNode] = field(default_factory=list)
    current_node_id: int = 0
    history: list[int] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add_node(self, node: StoryNode) -> None:
        """Append a story node and update timestamps."""
        self.nodes.append(node)
        self.current_node_id = node.id
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def get_current_node(self) -> Optional[StoryNode]:
        """Return the node the reader is currently at."""
        for node in self.nodes:
            if node.id == self.current_node_id:
                return node
        return None

    def make_choice(self, choice_index: int) -> Optional[Choice]:
        """Record the reader's choice and return the chosen option."""
        current = self.get_current_node()
        if not current or choice_index < 0 or choice_index >= len(current.choices):
            return None
        self.history.append(self.current_node_id)
        chosen = current.choices[choice_index]
        self.current_node_id = chosen.next_node_id
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return chosen

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> StorySession:
        nodes_data = data.pop("nodes", [])
        session = cls(**data)
        for nd in nodes_data:
            choices = [Choice(**c) for c in nd.pop("choices", [])]
            session.nodes.append(StoryNode(**nd, choices=choices))
        return session

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> StorySession:
        with open(path) as f:
            data = json.load(f)
        return cls.from_dict(data)
