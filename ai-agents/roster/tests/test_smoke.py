"""Smoke tests for Roster — all pass with mock data."""

from __future__ import annotations

from src.models import GroupPhoto, RoastCard, Roast, Tone
from src.tones import TONE_MAP, list_tones
from src.roaster import Roaster
from src.card import format_card


class TestTones:
    """Tone definitions are well-formed."""

    def test_builtin_tones_have_minimum_count(self):
        tones = list_tones()
        assert len(tones) >= 4, f"Expected at least 4 tones, got {len(tones)}"

    def test_each_tone_has_all_fields(self):
        for tone in list_tones():
            assert tone.name, f"Tone missing name: {tone}"
            assert tone.description, f"Tone {tone.name} missing description"
            assert tone.vibe, f"Tone {tone.name} missing vibe"
            assert 1 <= tone.intensity <= 10, f"Tone {tone.name} intensity out of range"

    def test_tone_map_has_all_tones(self):
        for tone in list_tones():
            assert tone.name in TONE_MAP, f"Tone {tone.name} not in TONE_MAP"
            assert TONE_MAP[tone.name] is tone, f"TONE_MAP mismatch for {tone.name}"


class TestRoaster:
    """Roast engine produces well-formed output."""

    def setup_method(self):
        self.roaster = Roaster()
        self.tone = TONE_MAP["siblings"]

    def test_generate_roasts_returns_card(self, family_group):
        card = self.roaster.generate_roasts(family_group, self.tone, simulate=True)
        assert isinstance(card, RoastCard)
        assert card.title == "Roster Roast: The Family Portrait"

    def test_each_person_gets_a_roast(self, family_group):
        card = self.roaster.generate_roasts(family_group, self.tone, simulate=True)
        assert len(card.roasts) == len(family_group.people)
        for roast in card.roasts:
            assert len(roast.lines) >= 2

    def test_roast_has_insult_and_verdict(self, family_group):
        card = self.roaster.generate_roasts(family_group, self.tone, simulate=True)
        for roast in card.roasts:
            assert roast.insult
            assert roast.final_verdict

    def test_group_roast_is_present(self, family_group):
        card = self.roaster.generate_roasts(family_group, self.tone, simulate=True)
        assert card.group_roast

    def test_all_tones_produce_output(self, coworkers_group, all_tones):
        for tone in all_tones:
            card = self.roaster.generate_roasts(coworkers_group, tone, simulate=True)
            assert isinstance(card, RoastCard)
            assert card.tone.name == tone.name

    def test_set_client_toggles_live_flag(self):
        r = Roaster()
        assert not r.live
        r.set_client("sk-fake-key-12345")
        assert r.live
        assert r.api_key == "sk-fake-key-12345"
        r.set_client("")
        assert not r.live


class TestCard:
    """Card formatting produces valid output."""

    def setup_method(self):
        self.roaster = Roaster()
        self.tone = TONE_MAP["merciless"]

    def test_format_card_returns_string(self, coworkers_group):
        card = self.roaster.generate_roasts(coworkers_group, self.tone, simulate=True)
        output = format_card(card)
        assert isinstance(output, str)
        assert len(output) > 100

    def test_format_card_includes_group_name(self, coworkers_group):
        card = self.roaster.generate_roasts(coworkers_group, self.tone, simulate=True)
        output = format_card(card)
        assert "Q3 Team Photo" in output

    def test_format_card_includes_roast_lines(self, coworkers_group):
        card = self.roaster.generate_roasts(coworkers_group, self.tone, simulate=True)
        output = format_card(card)
        assert "💀" in output
        assert "🎯" in output

    def test_format_card_writes_to_file(self, coworkers_group, tmp_path):
        card = self.roaster.generate_roasts(coworkers_group, self.tone, simulate=True)
        fpath = tmp_path / "roast.txt"
        output = format_card(card, filepath=str(fpath))
        assert fpath.exists()
        content = fpath.read_text()
        assert len(content) > 100
        assert output == content


class TestGroups:
    """Example groups are well-formed."""

    def test_family_group_has_people(self, family_group):
        assert len(family_group.people) == 3
        for p in family_group.people:
            assert p.name
            assert p.description

    def test_coworkers_group_has_people(self, coworkers_group):
        assert len(coworkers_group.people) == 3
        for p in coworkers_group.people:
            assert p.name
            assert p.vibe


class TestIntegration:
    """End-to-end: roaster + card produce coherent output."""

    def setup_method(self):
        self.roaster = Roaster()

    def test_full_pipeline_with_siblings_tone(self, family_group):
        tone = TONE_MAP["siblings"]
        card = self.roaster.generate_roasts(family_group, tone, simulate=True)
        output = format_card(card)
        # Siblings tone should have affectionate phrases
        assert "love" in output.lower() or "family" in output.lower()
        assert card.tone.name == "siblings"

    def test_full_pipeline_with_merciless_tone(self, coworkers_group):
        tone = TONE_MAP["merciless"]
        card = self.roaster.generate_roasts(coworkers_group, tone, simulate=True)
        output = format_card(card)
        # Merciless tone should not have 'love' tropes
        assert "no survivors" in output.lower() or "zero survivors" in output.lower()
        assert card.footer

    def test_empty_group_returns_empty_card(self):
        group = GroupPhoto(title="Empty", people=[], setting="Nowhere")
        tone = TONE_MAP["siblings"]
        card = self.roaster.generate_roasts(group, tone, simulate=True)
        assert len(card.roasts) == 0
        output = format_card(card)
        assert output