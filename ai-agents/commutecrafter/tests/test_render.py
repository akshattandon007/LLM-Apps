"""Reason text and JSON shape."""

from __future__ import annotations

import json

from commutecrafter.llm import apply_template_reasons, template_reason
from commutecrafter.models import ContentItem, ScheduledItem
from commutecrafter.planner import build_plan
from commutecrafter.render import plan_json


def make_sched(seconds=300, fraction=1.0, words=1150):
    item = ContentItem(title="T", source="wikipedia", url="u", words=words, category="culture")
    return ScheduledItem(item=item, seconds=seconds, segment="core", fraction=fraction)


def test_template_reason_mentions_minutes_and_source():
    text = template_reason(make_sched())
    assert "5 min" in text
    assert "wikipedia" in text


def test_template_reason_flags_partial():
    text = template_reason(make_sched(fraction=0.5))
    assert "50%" in text


def test_apply_template_reasons_fills_every_item(corpus_items):
    plan = build_plan(corpus_items, 20)
    apply_template_reasons(plan)
    assert all(s.reason for s in plan.scheduled_items)


def test_plan_json_roundtrips(corpus_items):
    plan = build_plan(corpus_items, 20)
    text = plan_json(plan)
    payload = json.loads(text)
    assert payload["total_seconds"] == plan.total_seconds
    assert payload["fits"] is True
    assert isinstance(payload["segments"], list)


def test_plan_json_is_stable_ordering(corpus_items):
    plan = build_plan(corpus_items, 20)
    assert plan_json(plan) == plan_json(plan)
