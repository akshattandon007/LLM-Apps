from datetime import date, timedelta
from models import MoveDetails, Playbook, TimelineEntry
from agents import utility_scheduler, address_changer, cost_estimator, timeline_architect


def _sample_details(**kwargs) -> MoveDetails:
    overrides = {
        "current_zip": "10001",
        "new_zip": "90210",
        "move_date": date(2025, 12, 15),
        "household_size": "2br",
        "is_renting": True,
    }
    overrides.update(kwargs)
    return MoveDetails(**overrides)


class TestUtilityScheduler:
    def test_basic_run(self):
        details = _sample_details()
        result = utility_scheduler.run(details)
        assert len(result.electric) > 0
        assert len(result.gas) > 0
        assert len(result.water) > 0
        assert len(result.internet) > 0
        assert len(result.notes) > 0

    def test_renting_note(self):
        result = utility_scheduler.run(_sample_details(is_renting=True))
        notes_text = " ".join(result.notes).lower()
        assert "renter" in notes_text or "lease" in notes_text

    def test_house_size_notes(self):
        result = utility_scheduler.run(_sample_details(household_size="studio"))
        notes = " ".join(result.notes)
        assert "deposit" in notes.lower()


class TestAddressChanger:
    def test_basic_run(self):
        details = _sample_details()
        result = address_changer.run(details)
        assert len(result.government) >= 4
        assert len(result.financial) >= 3
        assert len(result.subscriptions) >= 2

    def test_renting_extra(self):
        result = address_changer.run(_sample_details(is_renting=True))
        other_text = " ".join(result.other).lower()
        assert "deposit" in other_text

    def test_not_renting_no_deposit_note(self):
        result = address_changer.run(_sample_details(is_renting=False))
        other_text = " ".join(result.other).lower()
        assert "deposit" not in other_text


class TestCostEstimator:
    def test_basic_run(self):
        details = _sample_details()
        result = cost_estimator.run(details)
        assert result.truck_rental > 0
        assert result.total == 0  # total is computed via to_markdown, not pre-filled
        assert len(result.notes) >= 3

    def test_different_distances(self):
        local = _sample_details(current_zip="10001", new_zip="10002")
        far = _sample_details(current_zip="10001", new_zip="90210")
        local_cost = cost_estimator.run(local)
        far_cost = cost_estimator.run(far)
        # Cross-country should cost more than same-city
        assert far_cost.movers >= local_cost.movers

    def test_household_sizes(self):
        studio = cost_estimator.run(_sample_details(household_size="studio"))
        house = cost_estimator.run(_sample_details(household_size="house"))
        assert house.truck_rental >= studio.truck_rental
        assert house.movers >= studio.movers


class TestTimelineArchitect:
    def test_basic_run(self):
        details = _sample_details()
        result = timeline_architect.run(details)
        assert len(result) >= 6
        assert any("Move Day" in e.week for e in result)
        assert any("8 Weeks" in e.week for e in result)
        assert any("1 Week After" in e.week for e in result)

    def test_move_day_tasks(self):
        result = timeline_architect.run(_sample_details())
        move_day = [e for e in result if "Move Day" in e.week]
        assert len(move_day) == 1
        assert len(move_day[0].tasks) >= 5


class TestPlaybookMarkdown:
    def test_empty_playbook_renders(self):
        details = _sample_details()
        playbook = Playbook(move_details=details)
        md = playbook.to_markdown()
        assert "# 📦 MoveMate Relocation Playbook" in md
        assert str(details.move_date) in md

    def test_full_playbook(self):
        details = _sample_details()
        playbook = Playbook(move_details=details)
        playbook.utilities = utility_scheduler.run(details)
        playbook.address_changes = address_changer.run(details)
        playbook.costs = cost_estimator.run(details)
        playbook.neighborhood.nearby_amenities = ["Coffee Shop", "Grocery Store"]
        playbook.neighborhood.weather_summary = "Nice weather ahead."
        playbook.timeline = timeline_architect.run(details)

        md = playbook.to_markdown()
        assert "## ⚡ Utility Setup & Cancellation" in md
        assert "## 📬 Address Change Checklist" in md
        assert "## 💰 Cost Estimate" in md
        assert "## 🏘️ Neighborhood Snapshot" in md
        assert "## 📅 Moving Timeline" in md


class TestModels:
    def test_move_details_defaults(self):
        d = _sample_details(current_zip="12345")
        assert d.current_zip == "12345"
        assert d.current_address is None

    def test_timeline_entry(self):
        t = TimelineEntry(week="Test Week", tasks=["Task 1", "Task 2"], category="test")
        assert len(t.tasks) == 2
        assert t.category == "test"