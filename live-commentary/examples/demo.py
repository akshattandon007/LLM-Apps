"""Programmatic example: drive the commentary engine yourself.

Run with:  python examples/demo.py

This uses the offline simulated match and the offline template engine, so it
needs no keys and no network. Swap in ESPNProvider + ClaudeEngine for the real
thing (see the README).
"""

from livecommentary.engine import TemplateEngine
from livecommentary.providers.simulated import SimulatedProvider
from livecommentary.runner import Runner


def main() -> None:
    provider = SimulatedProvider(speed=8.0)        # ~12s for the whole match
    engine = TemplateEngine(language="English", style="play-by-play")

    def on_state(state):
        print(f"\n--- {state.headline()} ---")

    runner = Runner(provider=provider, engine=engine)
    runner.run("sim-1", on_state=on_state)


if __name__ == "__main__":
    main()
