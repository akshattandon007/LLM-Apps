import unittest

from livecommentary.engine import TemplateEngine
from livecommentary.providers.simulated import SimulatedProvider
from livecommentary.runner import Runner, CommentaryLine


class CollectingRunner:
    """Helper to capture emitted lines."""

    def __init__(self):
        self.lines = []

    def __call__(self, line: CommentaryLine):
        self.lines.append(line)


class TestRunner(unittest.TestCase):
    def setUp(self):
        self.provider = SimulatedProvider(clock_minutes=999)  # whole match in the past
        self.engine = TemplateEngine(language="English")

    def test_dedup_across_ticks(self):
        sink = CollectingRunner()
        runner = Runner(provider=self.provider, engine=self.engine, emit=sink)
        first = runner.tick("sim-1")
        second = runner.tick("sim-1")  # same events; should all be deduped
        self.assertEqual(len(first), 15)
        self.assertEqual(len(second), 0)
        self.assertEqual(len(sink.lines), 15)

    def test_goal_commentary_includes_score(self):
        sink = CollectingRunner()
        runner = Runner(provider=self.provider, engine=self.engine, emit=sink)
        runner.tick("sim-1")
        goal_lines = [l.text for l in sink.lines if l.text.startswith("GOAL!")]
        self.assertTrue(goal_lines)
        self.assertTrue(any("ARS" in t or "CHE" in t for t in goal_lines))

    def test_spanish_engine(self):
        sink = CollectingRunner()
        runner = Runner(provider=self.provider,
                        engine=TemplateEngine(language="Spanish"), emit=sink)
        runner.tick("sim-1")
        self.assertTrue(any(l.text.startswith("¡GOOOL!") for l in sink.lines))

    def test_run_until_final(self):
        sink = CollectingRunner()
        runner = Runner(provider=self.provider, engine=self.engine, emit=sink)
        runner.run("sim-1", max_ticks=5)
        self.assertEqual(len(sink.lines), 15)  # all events, no dupes


if __name__ == "__main__":
    unittest.main()
