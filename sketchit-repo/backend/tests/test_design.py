"""Tests for the design module — system prompt composition and theme library."""

from design import (
    DESIGN_PHILOSOPHY,
    DESIGN_PRINCIPLES,
    DESIGNER_SYSTEM_PROMPT,
    THEME_LIBRARY,
    build_system_prompt,
)


def test_system_prompt_is_nonempty():
    """The composed prompt should be substantive."""
    assert len(DESIGNER_SYSTEM_PROMPT) > 5000
    assert "SketchIt" in DESIGNER_SYSTEM_PROMPT


def test_system_prompt_contains_all_pieces():
    """All the major sections should be present in the final prompt."""
    prompt = DESIGNER_SYSTEM_PROMPT
    # From DESIGN_PHILOSOPHY
    assert "Intentionality over cleverness" in prompt
    # From DESIGN_PRINCIPLES
    assert "Hierarchy" in prompt
    assert "4.5:1" in prompt  # WCAG AA contrast
    # From OUTPUT_FORMAT_SPEC
    assert '"operations"' in prompt
    assert "inject_css" in prompt
    assert "load_font" in prompt
    # Theme library is present
    assert "Theme Library" in prompt


def test_system_prompt_includes_every_theme():
    """Every theme in the library should appear by name in the prompt."""
    for theme_name in THEME_LIBRARY:
        assert theme_name in DESIGNER_SYSTEM_PROMPT, f"Missing theme: {theme_name}"


def test_theme_library_has_expected_themes():
    """Spot-check that signature themes from the skills are present."""
    expected = {
        "anthropic",  # from brand-guidelines skill
        "ocean-depths",  # from theme-factory
        "modern-minimalist",  # from theme-factory
        "tech-innovation",  # from theme-factory
        "midnight-galaxy",  # from theme-factory
    }
    assert expected.issubset(THEME_LIBRARY.keys())


def test_every_theme_has_required_fields():
    """Each theme needs description, palette, fonts (with Google URL), and best_for."""
    for name, theme in THEME_LIBRARY.items():
        assert "description" in theme, f"{name} missing description"
        assert "palette" in theme, f"{name} missing palette"
        assert "fonts" in theme, f"{name} missing fonts"
        assert "best_for" in theme, f"{name} missing best_for"
        assert "display" in theme["fonts"], f"{name} fonts missing display"
        assert "body" in theme["fonts"], f"{name} fonts missing body"
        assert "google_url" in theme["fonts"], f"{name} fonts missing google_url"
        assert theme["fonts"]["google_url"].startswith("https://fonts.googleapis.com/"), (
            f"{name} google_url must be a Google Fonts URL"
        )


def test_every_theme_palette_uses_hex():
    """All palette colors must be hex strings."""
    for name, theme in THEME_LIBRARY.items():
        for color_name, value in theme["palette"].items():
            assert value.startswith("#"), f"{name}.{color_name} = {value!r} must be a hex color"
            # 4 (#RGB), 7 (#RRGGBB), or 9 (#RRGGBBAA) chars
            assert len(value) in (4, 7, 9), f"{name}.{color_name} = {value!r} has wrong hex length"


def test_build_system_prompt_is_deterministic():
    """Composing the prompt twice should produce identical output."""
    assert build_system_prompt() == build_system_prompt()


def test_philosophy_and_principles_are_separable():
    """The sub-pieces should be usable independently (for docs, other surfaces)."""
    assert DESIGN_PHILOSOPHY.strip()
    assert DESIGN_PRINCIPLES.strip()
    assert DESIGN_PHILOSOPHY != DESIGN_PRINCIPLES
