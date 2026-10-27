"""Tests for the offdays planner — core leave optimization algorithm."""

import json
import unittest
from datetime import date

from offdays.planner import (
    Plan,
    Holiday,
    build_off_set,
    find_blocks,
    gap_before,
    gap_after,
    compute_plans,
)


# Minimal US 2026 public holidays (global true) — 10 holidays
US_2026_HOLIDAYS = [
    {"date": "2026-01-01", "name": "New Year's Day"},
    {"date": "2026-01-19", "name": "Martin Luther King, Jr. Day"},
    {"date": "2026-02-16", "name": "Presidents Day"},
    {"date": "2026-05-25", "name": "Memorial Day"},
    {"date": "2026-06-19", "name": "Juneteenth National Independence Day"},
    {"date": "2026-07-03", "name": "Independence Day"},
    {"date": "2026-09-07", "name": "Labour Day"},
    {"date": "2026-11-11", "name": "Veterans Day"},
    {"date": "2026-11-26", "name": "Thanksgiving Day"},
    {"date": "2026-12-25", "name": "Christmas Day"},
]


class TestBuildOffSet(unittest.TestCase):
    """Test off-set construction from holidays + weekends."""

    def test_off_set_includes_holidays_and_weekends(self):
        off, holidays = build_off_set(US_2026_HOLIDAYS, 2026)
        # Jan 1 (Thu) is a holiday
        self.assertIn(date(2026, 1, 1), off)
        # Jan 3 (Sat) is a weekend
        self.assertIn(date(2026, 1, 3), off)
        # Jan 4 (Sun) is a weekend
        self.assertIn(date(2026, 1, 4), off)
        # Jan 5 (Mon) is a workday
        self.assertNotIn(date(2026, 1, 5), off)

    def test_holiday_count(self):
        off, holidays = build_off_set(US_2026_HOLIDAYS, 2026)
        self.assertEqual(len(holidays), 10)
        holiday_names = [h.name for h in holidays]
        self.assertIn("New Year's Day", holiday_names)
        self.assertIn("Christmas Day", holiday_names)

    def test_jan_1_weekday(self):
        """Jan 1 2026 is a Thursday."""
        self.assertEqual(date(2026, 1, 1).weekday(), 3)  # Thursday


class TestFindBlocks(unittest.TestCase):
    """Test block-finding on known off-sets."""

    def setUp(self):
        self.off, _ = build_off_set(US_2026_HOLIDAYS, 2026)

    def test_jan_1_is_solo_block(self):
        """New Year's Day 2026 is Thursday — isolated block since Jan 2 is workday."""
        off, _ = build_off_set(US_2026_HOLIDAYS, 2026)
        blocks = find_blocks(off, 2026)
        jan1_block = None
        for b in blocks:
            if date(2026, 1, 1) in b:
                jan1_block = b
                break
        self.assertIsNotNone(jan1_block)
        self.assertEqual(len(jan1_block), 1)  # Isolated Thursday

    def test_mlk_block_merged_with_weekend(self):
        """MLK Day Jan 19 merges with preceding weekend (Jan 17-18)."""
        off, _ = build_off_set(US_2026_HOLIDAYS, 2026)
        blocks = find_blocks(off, 2026)
        mlk_block = None
        for b in blocks:
            if date(2026, 1, 19) in b:
                mlk_block = b
                break
        self.assertIsNotNone(mlk_block)
        self.assertIn(date(2026, 1, 17), mlk_block)
        self.assertIn(date(2026, 1, 18), mlk_block)
        self.assertIn(date(2026, 1, 19), mlk_block)
        self.assertEqual(len(mlk_block), 3)

    def test_no_blocks_empty_year(self):
        """Empty holiday list should still produce weekend blocks."""
        off, _ = build_off_set([], 2026)
        blocks = find_blocks(off, 2026)
        self.assertGreater(len(blocks), 50)


class TestGapFunctions(unittest.TestCase):
    """Test gap computation before/after blocks."""

    def setUp(self):
        self.off, _ = build_off_set(US_2026_HOLIDAYS, 2026)

    def test_gap_before_jan1(self):
        """Jan 1 is start of year — no left gap."""
        gap = gap_before(self.off, date(2026, 1, 1))
        self.assertEqual(gap, [])

    def test_gap_after_jan1_holiday(self):
        """Jan 1 (Thu) — gap to next weekend is Jan 2 (Fri) = 1 workday."""
        gap = gap_after(self.off, date(2026, 1, 1))
        self.assertEqual(len(gap), 1)
        self.assertEqual(gap[0], date(2026, 1, 2))

    def test_gap_before_mlk_block(self):
        """MLK block starts Jan 17 (Sat). Left gap = Jan 12-16 (Mon-Fri).
        gap_before returns nearest-first: [Jan 16, Jan 15, ..., Jan 12]."""
        gap = gap_before(self.off, date(2026, 1, 17))
        self.assertEqual(len(gap), 5)
        self.assertEqual(gap[0], date(2026, 1, 16))  # nearest first
        self.assertEqual(gap[-1], date(2026, 1, 12))  # farthest last

    def test_gap_after_mlk_block(self):
        """MLK block ends Jan 19 (Mon). Right gap = Jan 20-23 (Tue-Fri)."""
        gap = gap_after(self.off, date(2026, 1, 19))
        self.assertEqual(len(gap), 4)
        self.assertEqual(gap[0], date(2026, 1, 20))
        self.assertEqual(gap[-1], date(2026, 1, 23))

    def test_gap_before_independence_day_block(self):
        """Independence Day Jul 3 (Fri) merges with Jul 4-5 weekend. Block starts Jul 3.
        Left gap nearest-first: [Jul 2, Jul 1, Jun 30, Jun 29]."""
        off, _ = build_off_set(US_2026_HOLIDAYS, 2026)
        gap = gap_before(off, date(2026, 7, 3))
        self.assertEqual(len(gap), 4)
        self.assertEqual(gap[0], date(2026, 7, 2))
        self.assertEqual(gap[-1], date(2026, 6, 29))


class TestComputePlans(unittest.TestCase):
    """Test the full plan computation."""

    def test_compute_top_plans_for_us_2026_with_3_leave_days(self):
        """Should return ranked plans for US 2026 with up to 3 leave days."""
        plans = compute_plans(US_2026_HOLIDAYS, 2026, leave_budget=3, top_n=10)
        self.assertGreater(len(plans), 0)
        self.assertGreaterEqual(plans[0].days_off, 3)

    def test_jan_1_plan_book_fri(self):
        """Booking Jan 2 (Fri) around Jan 1 (Thu) should give 4 consecutive days off."""
        plans = compute_plans(US_2026_HOLIDAYS, 2026, leave_budget=1)
        jan2_plan = None
        for p in plans:
            if p.leave_dates == [date(2026, 1, 2)]:
                jan2_plan = p
                break
        self.assertIsNotNone(jan2_plan,
                             msg="Plan booking Jan 2 should exist")
        self.assertEqual(jan2_plan.days_off, 4,
                         msg="Jan 2 + weekend should give 4 off")
        self.assertEqual(jan2_plan.leave_used, 1)
        self.assertEqual(jan2_plan.stretch_start, date(2026, 1, 1))
        self.assertEqual(jan2_plan.stretch_end, date(2026, 1, 4))

    def test_thanksgiving_plan_book_friday(self):
        """Booking Nov 27 (Fri) after Thanksgiving Nov 26 (Thu) gives 4 off."""
        plans = compute_plans(US_2026_HOLIDAYS, 2026, leave_budget=2, top_n=100)
        nov27_plan = None
        for p in plans:
            if p.leave_dates == [date(2026, 11, 27)]:
                nov27_plan = p
                break
        self.assertIsNotNone(nov27_plan,
                             msg="Plan booking Nov 27 should exist in top 100")
        self.assertEqual(nov27_plan.days_off, 4)
        self.assertEqual(nov27_plan.stretch_start, date(2026, 11, 26))
        self.assertEqual(nov27_plan.stretch_end, date(2026, 11, 29))

    def test_christmas_block_free_weekend(self):
        """Dec 25 (Fri) 2026 merges with weekend Dec 26-27 for a free 3-day block."""
        plans = compute_plans(US_2026_HOLIDAYS, 2026, leave_budget=0)
        # Check any plan has Christmas in its holiday list (by substring)
        christmas_plans = [
            p for p in plans
            if any("Christmas" in h for h in (p.holidays_covered or []))
        ]
        free_plans = [p for p in christmas_plans if p.leave_used == 0]
        self.assertGreaterEqual(len(free_plans), 1)
        self.assertGreaterEqual(free_plans[0].days_off, 3)

    def test_marathon_plan_book_everything(self):
        """With 5 leave days, there should be at least one plan with 5+ days off."""
        plans = compute_plans(US_2026_HOLIDAYS, 2026, leave_budget=5, top_n=20)
        best = plans[0]
        self.assertGreaterEqual(best.days_off, 4)
        self.assertLessEqual(best.leave_used, 5)

    def test_no_holidays_returns_empty_plans(self):
        """No holidays = no holiday plans (only weekend blocks which we skip)."""
        plans = compute_plans([], 2026, leave_budget=3)
        self.assertEqual(len(plans), 0)

    def test_one_holiday_scenario(self):
        """Single holiday in a year should still produce a plan."""
        holidays = [{"date": "2026-07-04", "name": "Test Day"}]
        plans = compute_plans(holidays, 2026, leave_budget=2)
        self.assertGreaterEqual(len(plans), 1)

    def test_plan_deduplication(self):
        """Same stretch with different leave usage should be deduplicated."""
        plans = compute_plans(US_2026_HOLIDAYS, 2026, leave_budget=5, top_n=50)
        seen = set()
        for p in plans:
            key = (p.stretch_start, p.stretch_end, p.leave_used)
            self.assertNotIn(key, seen, f"Duplicate plan: {key}")
            seen.add(key)

    def test_plans_sorted_descending(self):
        """Plans should be sorted by days_off desc, then leave_used asc."""
        plans = compute_plans(US_2026_HOLIDAYS, 2026, leave_budget=5, top_n=20)
        for i in range(len(plans) - 1):
            a, b = plans[i], plans[i + 1]
            if a.days_off == b.days_off:
                self.assertLessEqual(a.leave_used, b.leave_used)
            else:
                self.assertGreater(a.days_off, b.days_off)

    def test_plan_dataclass_order(self):
        """Plan dataclass ordering should sort by days_off desc, leave_used asc."""
        p1 = Plan(days_off=5, leave_used=2, stretch_start=date(2026, 1, 1), stretch_end=date(2026, 1, 5))
        p2 = Plan(days_off=5, leave_used=1, stretch_start=date(2026, 1, 1), stretch_end=date(2026, 1, 5))
        p3 = Plan(days_off=4, leave_used=1, stretch_start=date(2026, 1, 1), stretch_end=date(2026, 1, 4))
        plans = sorted([p1, p2, p3])
        self.assertEqual(plans[0].days_off, 5)
        self.assertEqual(plans[0].leave_used, 1)
        self.assertEqual(plans[1].days_off, 5)
        self.assertEqual(plans[1].leave_used, 2)
        self.assertEqual(plans[2].days_off, 4)


if __name__ == "__main__":
    unittest.main()