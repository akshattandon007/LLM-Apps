"""live-commentary: pluggable, multilingual live sports commentary.

Public surface:
    from livecommentary import Runner, create_provider
    from livecommentary.engine import ClaudeEngine, TemplateEngine
"""

from .models import (
    EventType,
    MatchEvent,
    MatchState,
    MatchSummary,
    Team,
)
from .providers import create_provider
from .runner import Runner, CommentaryLine

__version__ = "1.0.0"

__all__ = [
    "EventType",
    "MatchEvent",
    "MatchState",
    "MatchSummary",
    "Team",
    "create_provider",
    "Runner",
    "CommentaryLine",
    "__version__",
]
