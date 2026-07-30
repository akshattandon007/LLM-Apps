import unittest

from livecommentary.providers import create_provider
from livecommentary.providers.simulated import SimulatedProvider


class TestSimulatedProvider(unittest.TestCase):
    def test_registry_creates_simulated(self):
        p = create_provider("simulated", speed=1000)
        self.assertIsInstance(p, SimulatedProvider)

    def test_unknown_provider_raises(self):
        with self.assertRaises(ValueError):
            create_provider("nope")

    def test_events_are_chronological_and_have_stable_ids(self):
        # speed=10000 -> the whole 95' match is "in the past" immediately
        p = SimulatedProvider(clock_minutes=999)
        events = p.get_events("sim-1")
        self.assertEqual(len(events), 15)
        minutes = [e.minute for e in events]
        self.assertEqual(minutes, sorted(minutes))
        ids = [e.id for e in events]
        self.assertEqual(len(ids), len(set(ids)))  # unique

    def test_final_state_score(self):
        p = SimulatedProvider(clock_minutes=999)
        st = p.get_state("sim-1")
        self.assertTrue(st.is_final)
        # Arsenal 2 (Jesus, Odegaard pen) vs Chelsea 1 (Palmer) in the script
        self.assertEqual((st.home_score, st.away_score), (2, 1))

    def test_discover(self):
        p = SimulatedProvider(clock_minutes=999)
        res = p.discover()
        self.assertEqual(len(res), 1)
        self.assertIn("Arsenal", res[0].description)


if __name__ == "__main__":
    unittest.main()
