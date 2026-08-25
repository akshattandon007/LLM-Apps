"""Smoke tests for Parallel Lives."""

from __future__ import annotations

import pytest

from src.characters import get_character, list_characters
from src.conversation import Conversation
from src.models import Character, Message
from src.responder import generate_response, set_client, _simulate_response


# ---------------------------------------------------------------------------
# Character data tests
# ---------------------------------------------------------------------------

class TestCharacters:
    """All 6 characters are defined, accessible, and well-formed."""

    def test_all_characters_accessible(self):
        """Every key in the roster is retrievable by get_character()."""
        roster = list_characters()
        assert len(roster) >= 5, "Need at least 5 characters"
        for key, char in roster:
            fetched = get_character(key)
            assert fetched is not None, f"get_character('{key}') returned None"
            assert fetched.name == char.name

    def test_each_character_has_required_fields(self):
        """Every character has name, emoji, period, personality, greeting, catchphrase."""
        for key, char in list_characters():
            assert char.name, f"{key} missing name"
            assert char.emoji, f"{key} missing emoji"
            assert char.period, f"{key} missing period"
            assert char.personality, f"{key} missing personality"
            assert char.greeting, f"{key} missing greeting"
            assert char.catchphrase, f"{key} missing catchphrase"
            assert isinstance(char.emoji, str)

    def test_get_character_case_insensitive(self):
        """get_character works regardless of casing."""
        assert get_character("Einstein") is not None
        assert get_character("EINSTEIN") is not None
        assert get_character("einstein") is not None
        assert get_character("CLEOPATRA") is not None

    def test_get_character_unknown(self):
        """Unknown names return None."""
        assert get_character("zzz_nobody") is None
        assert get_character("") is None

    def test_socrates_included(self):
        """Socrates is in the roster."""
        soc = get_character("socrates")
        assert soc is not None
        assert "Socrates" in soc.name


class TestConversation:
    """Conversation flow works end-to-end."""

    def test_start_returns_greeting(self, mock_einstein, conversation):
        """start() returns a Message with the character's greeting."""
        msg = conversation.start()
        assert isinstance(msg, Message)
        assert msg.role == "character"
        assert mock_einstein.greeting in msg.content

    def test_add_user_and_character_turns(self, conversation):
        """Recording turns increments the message list."""
        conversation.start()
        user_msg = conversation.add_user_turn("Hello, can you hear me?")
        assert user_msg.role == "user"
        assert user_msg.turn_number == 2

        char_msg = conversation.add_character_turn("Loud and clear.")
        assert char_msg.role == "character"
        assert char_msg.turn_number == 3
        assert len(conversation.state.messages) == 3

    def test_context_window(self, conversation):
        """context_window returns last N turns formatted."""
        conversation.start()
        conversation.add_user_turn("How does gravity work?")
        conversation.add_character_turn("It's not a force — it's a curvature.")

        ctx = conversation.state.context_window(max_turns=4)
        assert "gravity" in ctx
        assert "curvature" in ctx
        assert "Albert Einstein" in ctx or ctx.count("You:") > 0

    def test_key_facts_persist(self, conversation):
        """Accepted key facts are stored and deduplicated."""
        conversation.add_key_fact("Einstein knows this caller as Alice.")
        conversation.add_key_fact("Einstein knows this caller as Alice.")
        assert len(conversation.state.key_facts) == 1

    def test_system_prompt_includes_character(self, conversation, mock_einstein):
        """build_system_prompt contains character identity and rules."""
        conversation.start()
        prompt = conversation.build_system_prompt()
        assert mock_einstein.name in prompt
        assert mock_einstein.catchphrase in prompt
        assert "RULES" in prompt
        assert "CONVERSATION SO FAR" in prompt


class TestResponder:
    """Response generation works in simulate mode (no LLM needed)."""

    def test_simulate_returns_text(self, conversation, mock_einstein):
        """_simulate_response returns non-empty string."""
        conversation.start()
        conversation.add_user_turn("What is time?")
        response = _simulate_response(conversation)
        assert isinstance(response, str)
        assert len(response) > 10

    def test_simulate_includes_character_voice(self, conversation):
        """Simulated responses feel in-character."""
        conversation.start()
        conversation.add_user_turn("Tell me about yourself.")
        response = _simulate_response(conversation)
        # Einstein templates use asterisks for actions
        assert "*" in response

    def test_generate_response_simulate_default(self, conversation):
        """generate_response works with simulate=True and no API key."""
        conversation.start()
        conversation.add_user_turn("Hello!")
        response = generate_response(conversation, simulate=True)
        assert isinstance(response, str)
        assert len(response) > 0

    def test_generate_response_live_mode_with_mock_client(
        self, conversation, mock_httpx_client
    ):
        """generate_response works with simulate=False and a mock client."""
        conversation.start()
        conversation.add_user_turn("Greetings from the future!")
        response = generate_response(conversation, simulate=False, api_key="sk-test")
        assert isinstance(response, str)
        assert len(response) > 0
        assert mock_httpx_client.post.called, "httpx client should have been called"

    def test_generate_response_fallback_on_api_error(
        self, conversation
    ):
        """On API error, returns a fallback string with catchphrase."""
        conversation.start()
        conversation.add_user_turn("Hello?")
        # No mock client injected → real client exists but has no base URL → exception
        # We don't set env vars, so it fails and returns fallback
        set_client(None)  # reset so it creates a real client
        response = generate_response(conversation, simulate=False, api_key="sk-broken")
        assert isinstance(response, str)
        assert conversation.character.catchphrase in response


class TestCLI:
    """CLI integration checks (no subprocess)."""

    def test_list_characters_returns_all(self):
        """list_characters returns all defined characters."""
        roster = list_characters()
        names = [c.name for _, c in roster]
        assert "Albert Einstein" in names
        assert "Sherlock Holmes" in names
        assert "Ada Lovelace" in names
        assert "Joan of Arc" in names
        assert "Cleopatra VII" in names
        assert "Socrates" in names


class TestModels:
    """Pydantic models validate correctly."""

    def test_character_model(self, mock_einstein):
        assert mock_einstein.name == "Albert Einstein"
        assert mock_einstein.model_dump()["name"] == "Albert Einstein"

    def test_message_model(self):
        msg = Message(role="user", content="Hello", turn_number=1)
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_conversation_state_add_message(self):
        from src.models import ConversationState
        state = ConversationState(character_name="Test")
        msg = state.add_message("character", "Welcome")
        assert state.turn_count == 1
        assert msg.turn_number == 1
        assert len(state.messages) == 1

    def test_voice_defaults(self):
        from src.models import CharacterVoice
        v = CharacterVoice()
        assert v.pitch == "neutral"
        assert v.speed == "normal"