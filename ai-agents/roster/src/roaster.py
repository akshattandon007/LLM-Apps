"""Roast generation engine — simulated and (optionally) live LLM modes."""

from __future__ import annotations

import os
import random
from typing import List, Optional

from dotenv import load_dotenv

from src.models import (
    Expression,
    GroupPhoto,
    Outfit,
    Person,
    Roast,
    RoastCard,
    RoastTarget,
    Tone,
    Vibe,
)
from src.tones import TONE_MAP

load_dotenv()


# ── Simulated roast templates per tone ──────────────────────────────────────

_SIMULATED_ROASTS: dict[str, dict[str, List[str]]] = {
    "siblings": {
        "expression": [
            "That smile screams 'I'm the favourite' and we both know that's a lie.",
            "You're trying to look mysterious but you just look mildly gassy.",
            "Your resting face is a court summons for good vibes.",
        ],
        "outfit": [
            "That outfit is a cry for help and nobody's answering.",
            "You dressed like you lost a bet with your own wardrobe.",
            "That shirt was a choice. A bad one, but a choice nonetheless.",
        ],
        "vibe": [
            "You have the energy of a group project member who didn't do the work.",
            "Your vibe is 'I'm the main character' but you're in the wrong show.",
            "You radiate 'I left the oven on' energy.",
        ],
        "body_language": [
            "Your arms are crossed like you're holding yourself together. Barely.",
            "That lean says 'too cool for this' but we all know you're just scared.",
            "You're standing like someone told you to 'act natural' and you panicked.",
        ],
        "arrangement": [
            "You pushed to the front for visibility and it's not helping your case.",
            "You're in the back like you're trying to escape the frame. We see you.",
            "You're positioned like the designated driver — physically there, spiritually gone.",
        ],
    },
    "coworkers": {
        "expression": [
            "That's your 'I'm listening' face and we can all tell you're not.",
            "You're smiling like you're in a hostage video.",
            "That expression says 'this could've been a Slack message'.",
        ],
        "outfit": [
            "You dressed for a day you planned to do nothing and succeeded.",
            "That blazer is doing a lot of heavy lifting and it's exhausted.",
            "Business casual means something different to everyone and you chose wrong.",
        ],
        "vibe": [
            "You have 'reply-all' energy and we're not here for it.",
            "You're giving 'meeting that should have been a memo' vibes.",
            "Your vibe is 'I'll circle back' and nobody wants you to.",
        ],
        "body_language": [
            "That posture says you're ready to zoom out of this conversation.",
            "You're folding your arms like you're about to drop a 'well, actually'.",
            "That stiff stance is HR-violation levels of discomfort.",
        ],
        "arrangement": [
            "You're front and center like this is your performance review.",
            "You squeezed into the middle like you're angling for a promotion. Noted.",
            "You're off to the side like a footnote nobody reads.",
        ],
    },
    "old_friends": {
        "expression": [
            "You're making the same expression as your senior photo. It didn't work then either.",
            "That grin is exactly as unhinged as it was in 2012. Love that for you.",
            "Your face says 'I've made peace with my decisions'. The rest of us haven't.",
        ],
        "outfit": [
            "You're wearing that shirt you got at a festival seven years ago and it shows.",
            "That fit is a museum piece — old, questionable, and we're afraid to touch it.",
            "You dressed like you raided your closet from the last decade. Because you did.",
        ],
        "vibe": [
            "You're giving the same energy as that one group chat argument from 2018.",
            "You haven't changed, and that's both comforting and concerning.",
            "You radiate 'I peaked in high school and I'm okay with that' energy.",
        ],
        "body_language": [
            "You're standing the exact same way you did in every group photo. Ever.",
            "That arm-around-the-shoulder move hasn't gotten smoother in ten years.",
            "You're leaning away like you're about to dodge the conversation.",
        ],
        "arrangement": [
            "You're in the middle because you're the glue. Or the chaos. Both, probably.",
            "You're in the back like you're already planning your exit. Classic you.",
            "You squeezed in at the last second, just like every plan we've ever made.",
        ],
    },
    "merciless": {
        "expression": [
            "Your smile looks like you're being held at gunpoint and honestly it's believable.",
            "That expression is what happens when a personality vacuum meets a camera.",
            "You look like a stock photo labelled 'regret'.",
        ],
        "outfit": [
            "That outfit is a crime against fashion and everyone here is an accessory.",
            "You dressed like the clearance rack threw up on you.",
            "Did you get dressed in the dark? In a hurry? In a blizzard? All three?",
        ],
        "vibe": [
            "Your vibe is 'I have a LinkedIn and I use it unironically'.",
            "You have the energy of a half-deflated balloon someone forgot to toss.",
            "You radiate 'I peak in group photos and it's still not working'.",
        ],
        "body_language": [
            "You're standing like you're trying to disappear and failing miserably.",
            "That pose says 'I was photoshopped in' and I believe it.",
            "Your body language is a cry for help in a language nobody speaks.",
        ],
        "arrangement": [
            "You're front and center like you're the main character. The reviews disagree.",
            "You're in the back like you know what you did. We all know what you did.",
            "You're off to the side like a typo in an otherwise fine sentence.",
        ],
    },
    "self_deprecating": {
        "expression": [
            "I'm doing my 'I belong here' face and fooling absolutely no one.",
            "My expression is 'please don't make this my profile picture' and it will be.",
            "I look like I'm calculating how long until I can leave. Answer: not soon enough.",
        ],
        "outfit": [
            "I dressed in the dark and it shows, but honestly this is my best effort.",
            "I wore this because it was on the floor. No further questions.",
            "My outfit says 'I have a style' and that style is 'I gave up'.",
        ],
        "vibe": [
            "I bring the energy of a WiFi signal with one bar.",
            "My vibe is 'I'm just here so I won't get fined'.",
            "I radiate the confidence of someone who googled 'how to pose' five minutes ago.",
        ],
        "body_language": [
            "I'm standing like I've never been in a photo before. Accurate.",
            "My posture is what happens when a chiropractor retires early.",
            "I'm leaning like I'm about to make a run for it. Don't blame me.",
        ],
        "arrangement": [
            "I'm in the middle to hide behind the people in front of me. Didn't work.",
            "I'm at the edge like I'm trying to make a clean getaway. Fair.",
            "I'm front and centre because nobody else wanted this spot. Called it.",
        ],
    },
}


def _pick_roasts(person: Person, tone: Tone) -> List[str]:
    """Generate 2-3 roast lines for a person in simulated mode."""
    tone_name = tone.name
    templates = _SIMULATED_ROASTS.get(tone_name, _SIMULATED_ROASTS["siblings"])

    lines = []
    targets_used = set()

    # Always target expression and vibe
    for key in ["expression", "vibe"]:
        pool = templates.get(key, [])
        if pool:
            lines.append(random.choice(pool))
            targets_used.add(key)

    # Pick one more from outfit, body_language, or arrangement
    extra = random.choice(["outfit", "body_language", "arrangement"])
    pool = templates.get(extra, [])
    if pool:
        lines.append(random.choice(pool))
        targets_used.add(key)

    # Add tone-specific closing verdict
    verdicts = {
        "siblings": "Love you, but the photo's not doing you favours.",
        "coworkers": "Let's circle back on this photo, shall we?",
        "old_friends": "Some things never change. Thank god.",
        "merciless": "You did this to yourself by being in the photo.",
        "self_deprecating": "I'm the reason this photo has a disclaimer.",
    }
    lines.append(verdicts.get(tone_name, "Next time, stand behind someone taller."))

    return lines


def _get_roast_targets() -> List[RoastTarget]:
    """Return a random subset of roast targets."""
    return list(RoastTarget)


class Roaster:
    """Roast generation engine.

    Simulated mode: uses preset templates keyed by tone + roast target.
    Live mode: would call an LLM API (not implemented in v1).
    """

    def __init__(self):
        self.api_key: Optional[str] = os.getenv("LLM_API_KEY")
        self.live: bool = bool(self.api_key)

    def set_client(self, api_key: str) -> None:
        """Inject a live API key (useful for testing or reconfiguration)."""
        self.api_key = api_key
        self.live = bool(api_key)

    def generate_roasts(
        self, group: GroupPhoto, tone: Tone, simulate: bool = True
    ) -> RoastCard:
        """Generate roasts for every person in the group photo.

        Args:
            group: The group photo with people to roast.
            tone: The roast tone to use.
            simulate: If True, use simulated templates. If False and a live API
                      key is configured, would call the LLM (not yet implemented).

        Returns:
            A fully populated RoastCard.
        """
        if not simulate and self.live:
            # Placeholder for live LLM integration
            return self._live_roast(group, tone)

        return self._simulated_roast(group, tone)

    def _simulated_roast(self, group: GroupPhoto, tone: Tone) -> RoastCard:
        """Generate roasts from preset templates."""
        roasts: List[Roast] = []

        for person in group.people:
            lines = _pick_roasts(person, tone)
            insult = lines[0] if lines else "No comment."
            final_verdict = lines[-1] if len(lines) > 1 else "That's all you get."

            roast = Roast(
                person=person,
                tone=tone.name,
                targets=list(RoastTarget),
                lines=lines,
                insult=insult,
                final_verdict=final_verdict,
            )
            roasts.append(roast)

        # Generate a group roast
        group_roast = self._group_roast(group, tone)

        # Footer
        footer = self._make_footer(tone)

        return RoastCard(
            title=f"Roster Roast: {group.title}",
            tone=tone,
            group=group,
            roasts=roasts,
            group_roast=group_roast,
            footer=footer,
        )

    def _live_roast(self, group: GroupPhoto, tone: Tone) -> RoastCard:
        """Placeholder for live LLM-powered roasting.

        Would call the LLM API with a prompt containing the group description
        and tone definition, then parse the structured roast response.
        """
        # For now, fall back to simulated with a note
        card = self._simulated_roast(group, tone)
        card.group_roast += "\n\n[Live LLM mode not yet implemented — used simulated roasts.]"
        return card

    @staticmethod
    def _group_roast(group: GroupPhoto, tone: Tone) -> str:
        """Generate a single-line roast for the group as a whole."""
        size = len(group.people)
        setting = group.setting or "this photo"

        group_roasts = {
            "siblings": [
                f"This family photo is a case study in shared genetics and questionable styling.",
                f"{size} people, one gene pool, and somehow it's still a grab bag.",
            ],
            "coworkers": [
                f"This team photo perfectly captures the energy of a meeting that ran 20 minutes over.",
                f"A group of {size} professionals who all agreed on one thing: get this over with.",
            ],
            "old_friends": [
                f"{size} friends who've seen each other at their worst. And this photo is proof.",
                f"This is the most chaotic {setting} since that trip none of you talk about.",
            ],
            "merciless": [
                f"A collection of {size} people who all thought they looked good today. The camera disagrees.",
                f"This photo is a visual apology to everyone who wasn't there.",
            ],
            "self_deprecating": [
                f"{size} people, zero coordination, maximum regret. My people.",
                f"This photo is a masterclass in what-not-to-do and we're all teaching it.",
            ],
        }

        pool = group_roasts.get(tone.name, group_roasts["siblings"])
        return random.choice(pool)

    @staticmethod
    def _make_footer(tone: Tone) -> str:
        footers = {
            "siblings": "— Roasted with love. You're still invited to Thanksgiving.",
            "coworkers": "— HR has been notified. This is fine.",
            "old_friends": "— We'll laugh about this later. We're laughing now, actually.",
            "merciless": "— No survivors. No regrets.",
            "self_deprecating": "— We roasted ourselves so you don't have to.",
        }
        return footers.get(tone.name, "— Roster: best served cold.")