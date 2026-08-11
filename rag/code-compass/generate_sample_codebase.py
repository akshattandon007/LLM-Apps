#!/usr/bin/env python3
"""Generate a sample codebase for smoke testing Code Compass.

Produces a small multi-module Python project in data/sample-project/.
"""

from __future__ import annotations

import os

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "data", "sample-project")


def _write(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content.lstrip("\n"))


def generate():
    print(f"Generating sample codebase in {SAMPLE_DIR}...")

    _write(
        os.path.join(SAMPLE_DIR, "main.py"),
        _MAIN_PY,
    )
    _write(
        os.path.join(SAMPLE_DIR, "todo_list.py"),
        _TODO_LIST_PY,
    )
    _write(
        os.path.join(SAMPLE_DIR, "storage.py"),
        _STORAGE_PY,
    )
    _write(
        os.path.join(SAMPLE_DIR, "validators.py"),
        _VALIDATORS_PY,
    )

    print(f"Done -- generated 4 files in {SAMPLE_DIR}")


_MAIN_PY = '''"""Todo app entry point."""

import sys
from todo_list import TodoList
from storage import FileStorage


def main():
    """Run the todo app CLI."""
    storage = FileStorage("todos.json")
    todo_list = TodoList(storage)

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "add":
            todo_list.add_item(" ".join(sys.argv[2:]))
        elif command == "list":
            items = todo_list.list_items()
            for item in items:
                print(f"[{"x" if item.completed else " "}] {item.title}")
        elif command == "complete":
            todo_list.complete_item(int(sys.argv[2]))
        else:
            print(f"Unknown command: {command}")
    else:
        todo_list.interactive_mode()


if __name__ == "__main__":
    main()
'''

_TODO_LIST_PY = '''"""Core todo list logic."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TodoItem:
    """A single todo item."""
    title: str
    completed: bool = False


class TodoList:
    """Manages a collection of todo items with persistence."""

    def __init__(self, storage):
        self.storage = storage
        self._items: list[TodoItem] = []
        self._load()

    def _load(self):
        data = self.storage.load()
        self._items = [TodoItem(**item) for item in data]

    def _save(self):
        self.storage.save([
            {"title": item.title, "completed": item.completed}
            for item in self._items
        ])

    def add_item(self, title: str) -> TodoItem:
        """Add a new todo item. Validates that title is non-empty."""
        if not title or not title.strip():
            raise ValueError("Title must not be empty")
        item = TodoItem(title=title.strip())
        self._items.append(item)
        self._save()
        return item

    def list_items(self) -> list[TodoItem]:
        """Return all items."""
        return list(self._items)

    def complete_item(self, index: int) -> TodoItem:
        """Mark an item as completed. Validates index bounds."""
        if index < 0 or index >= len(self._items):
            raise IndexError(f"Item index {index} out of range (0-{len(self._items) - 1})")
        self._items[index].completed = True
        self._save()
        return self._items[index]

    def remove_completed(self) -> int:
        """Remove all completed items. Returns count removed."""
        before = len(self._items)
        self._items = [item for item in self._items if not item.completed]
        self._save()
        return before - len(self._items)
'''

_STORAGE_PY = '''"""File-based storage backend."""

from __future__ import annotations

import json
import os


class FileStorage:
    """Handles JSON file persistence for todo items."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> list[dict]:
        """Load items from the JSON file. Returns empty list if missing."""
        if not os.path.exists(self.file_path):
            return []
        with open(self.file_path, "r") as f:
            return json.load(f)

    def save(self, items: list[dict]) -> None:
        """Save items to the JSON file."""
        with open(self.file_path, "w") as f:
            json.dump(items, f, indent=2)
'''

_VALIDATORS_PY = '''"""Input validation utilities."""

from __future__ import annotations

import re


def validate_email(email: str) -> bool:
    """Validate an email address format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_title(title: str) -> bool:
    """Validate a title is non-empty and not too long."""
    if not title or not title.strip():
        return False
    if len(title) > 200:
        return False
    return True
'''


if __name__ == "__main__":
    generate()
