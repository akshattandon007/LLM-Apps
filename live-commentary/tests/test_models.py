import unittest

from livecommentary.models import EventType, MatchEvent, MatchState, Team


class TestModels(unittest.TestCase):
    def test_scoreline_and_headline(self):
        s = MatchState(
            match_id="x", sport="soccer", league="EPL",
            home=Team("H", "Home", "HOM"), away=Team("A", "Away", "AWY"),
            home_score=2, away_score=1, status="in", clock="67'",
        )
        self.assertEqual(s.scoreline(), "HOM 2 - 1 AWY")
        self.assertIn("67'", s.headline())
        self.assertTrue(s.is_live)
        self.assertFalse(s.is_final)

    def test_event_scoring_flag(self):
        goal = MatchEvent(id="1", type=EventType.GOAL, text="goal!")
        foul = MatchEvent(id="2", type=EventType.FOUL, text="foul")
        self.assertTrue(goal.is_scoring())
        self.assertFalse(foul.is_scoring())

    def test_event_id_is_stable(self):
        e1 = MatchEvent(id="abc", type=EventType.SHOT, text="t")
        e2 = MatchEvent(id="abc", type=EventType.SHOT, text="t")
        self.assertEqual(e1.id, e2.id)


if __name__ == "__main__":
    unittest.main()
