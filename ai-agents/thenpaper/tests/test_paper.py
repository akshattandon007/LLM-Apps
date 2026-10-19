"""Tests for front-page assembly and rendering."""

from thenpaper import paper
from thenpaper.api import DayFacts, DayItem


def make_facts(**overrides) -> DayFacts:
    facts = DayFacts(
        month=10,
        day=19,
        events=[
            DayItem(year=1969, text="Apollo 11 splashdown celebration", kind="event"),
            DayItem(year=2020, text="A very modern thing happens to everyone", kind="event"),
            DayItem(year=1215, text="A charter is sealed by an angry king", kind="event"),
            DayItem(year=2001, text="Something with a long tail and a new beginning", kind="event"),
        ],
        births=[
            DayItem(year=1922, text="A Nobel laureate, born this day", kind="birth"),
            DayItem(year=1990, text="A future coder, born this day", kind="birth"),
            DayItem(year=1859, text="A Victorian inventor, born this day", kind="birth"),
        ],
        deaths=[DayItem(year=1945, text="A beloved dog passes peacefully", kind="death")],
        holidays=[DayItem(year=0, text="World Make-Believe Day\n(unofficial)", kind="holiday")],
        selected=[DayItem(year=2017, text="Oumuamua is discovered", kind="selected")],
        source="live",
    )
    facts.__dict__.update(overrides)
    return facts


def test_rank_events_recency_first():
    events = make_facts().events
    ranked = paper.rank_events(events, limit=10)
    assert ranked[0].year == 2020
    assert ranked[-1].year == 1215


def test_rank_events_focus_year():
    events = make_facts().events
    ranked = paper.rank_events(events, limit=10, focus_year=1969)
    assert ranked[0].year == 1969


def test_rank_births_modern_first():
    births = make_facts().births
    ranked = paper.rank_births(births, limit=3)
    assert ranked[0].year == 1990


def test_build_front_page_uses_selected_as_lead():
    page = paper.build_front_page(make_facts(), 10, 19)
    assert page.lead is not None
    assert page.lead.year == 2017
    assert "oumuamua" in page.lead.text.lower()


def test_build_front_page_uses_enhancement():
    class Enh:
        headline = "CUSTOM HEADLINE"
        dek = "Custom dek line."
        twin_intro = "Custom twins intro."

    page = paper.build_front_page(make_facts(), 10, 19, enhancement=Enh())
    assert page.headline == "CUSTOM HEADLINE"
    assert page.dek == "Custom dek line."
    assert page.twin_intro == "Custom twins intro."


def test_build_front_page_empty_facts():
    page = paper.build_front_page(DayFacts(month=1, day=1), 1, 1)
    assert page.lead is None
    assert page.headline  # fallback headline exists


def test_invalid_theme_falls_back_to_morning():
    page = paper.build_front_page(make_facts(), 10, 19, theme="loud")
    assert page.theme == "morning"
    assert page.edition == "Morning Edition"


def test_render_contains_key_sections():
    page = paper.build_front_page(make_facts(), 10, 19)
    text = paper.render(page)
    assert "THE" in text
    assert "THEN" in text
    assert "BORN THIS DAY" in text
    assert "IN MEMORIAM" in text
    assert "ON THE CALENDAR" in text
    assert "World Make-Believe Day" in text
    assert "simulated" in text or "live" in text


def test_render_focus_year_line():
    page = paper.build_front_page(make_facts(), 10, 19, focus_year=1969)
    assert "1969" in paper.render(page)


def test_lead_not_repeated_in_events():
    facts = make_facts()
    # selected[0] duplicates an events item exactly
    facts.selected = [DayItem(year=2020, text="A very modern thing happens to everyone", kind="selected")]
    page = paper.build_front_page(facts, 10, 19)
    assert page.lead is not None
    assert all((e.year, e.text) != (page.lead.year, page.lead.text) for e in page.events)


def test_wrap_handles_long_words():
    lines = paper._wrap("a" * 200, width=40)
    assert all(len(line) <= 40 for line in lines)
    assert lines  # non-empty