"""Pydantic models for Parallel Lives."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class CharacterVoice(BaseModel):
    """Voice style notes for TTS rendering."""
    pitch: str = "neutral"
    speed: str = "normal"
    tone: str = "conversational"
    accent: Optional[str] = None


class Character(BaseModel):
    """A historical or fictional character you can call."""

    name: str
    emoji: str
    period: str
    personality: str
    greeting: str
    catchphrase: str
    voice: CharacterVoice = Field(default_factory=CharacterVoice)
    biography: str = ""
    knowledge_tags: List[str] = Field(default_factory=list)


class Message(BaseModel):
    """A single turn in a conversation."""

    role: str  # "user" or "character"
    content: str
    turn_number: int = 1


class ConversationState(BaseModel):
    """The full state of an active conversation."""

    character_name: str
    messages: List[Message] = Field(default_factory=list)
    turn_count: int = 0
    summary: str = ""
    key_facts: List[str] = Field(default_factory=list)

    def add_message(self, role: str, content: str) -> Message:
        """Add a message and advance the turn counter."""
        self.turn_count += 1
        msg = Message(role=role, content=content, turn_number=self.turn_count)
        self.messages.append(msg)
        return msg

    def context_window(self, max_turns: int = 6) -> str:
        """Return recent conversation as a formatted string."""
        recent = self.messages[-max_turns:]
        lines = []
        for m in recent:
            prefix = "You" if m.role == "user" else self.character_name
            lines.append(f"{prefix}: {m.content}")
        return "\n".join(lines)