"""Conversation flow management for Parallel Lives."""

from __future__ import annotations

from typing import List, Optional

from src.models import Character, ConversationState, Message


class Conversation:
    """Manages a single conversation with a character.

    Holds state (message history, key facts) and provides helpers
    for context building and memory extraction.
    """

    def __init__(self, character: Character) -> None:
        self.character = character
        self.state = ConversationState(character_name=character.name)

    def start(self) -> Message:
        """Return the character's greeting as the first message."""
        return self.state.add_message("character", self.character.greeting)

    def add_user_turn(self, text: str) -> Message:
        """Record the user's message."""
        return self.state.add_message("user", text)

    def add_character_turn(self, text: str) -> Message:
        """Record the character's response."""
        return self.state.add_message("character", text)

    def build_system_prompt(self) -> str:
        """Build the system prompt for the LLM based on character and memory."""
        char = self.character

        parts = [
            f"You are {char.name} ({char.period}).",
            f"Personality: {char.personality}",
            f"Biography: {char.biography}",
            f"Your catchphrase is: \"{char.catchphrase}\"",
            "",
            "RULES:",
            "- Respond ENTIRELY in-character. Never break character.",
            f"- Use period-accurate knowledge ({', '.join(char.knowledge_tags)}).",
            "- Keep responses 1-3 paragraphs. Conversational, not essay-length.",
            "- Refer to the user directly as 'you' in a natural way.",
            "- Occasionally use your catchphrase when it fits naturally.",
            "- Include character-appropriate actions in *asterisks*.",
            "",
            "CONVERSATION SO FAR:",
            self.state.context_window(max_turns=8),
        ]

        if self.state.key_facts:
            parts.append("")
            parts.append("KEY FACTS YOU REMEMBER ABOUT THIS PERSON:")
            for fact in self.state.key_facts:
                parts.append(f"- {fact}")

        return "\n".join(parts)

    def extract_memory(self, response: str) -> List[str]:
        """Pull key personal details from a response for memory tracking."""
        # Simple heuristic: extract named entities or facts
        # In v2 this would use NER; for v1 we track user-provided facts
        # by asking the LLM, but this is handled in responder.
        return []

    def add_key_fact(self, fact: str) -> None:
        """Manually add a fact the character should remember."""
        if fact not in self.state.key_facts:
            self.state.key_facts.append(fact)

    @property
    def active(self) -> bool:
        """True when a conversation has at least the greeting."""
        return len(self.state.messages) > 0