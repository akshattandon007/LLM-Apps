"""Optional text-to-speech.

Speaking is strictly optional — the system prints commentary regardless. Two
backends are tried in order:

* ``gTTS`` (Google Translate TTS): excellent multilingual coverage, needs
  internet, writes/plays an mp3.
* ``pyttsx3``: fully offline, uses the OS voices (language coverage depends on
  what your OS has installed).

If neither is available, :class:`NullSpeaker` is used and nothing is spoken.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from typing import Optional

# Map a few human language names to gTTS/ISO codes.
_LANG_CODES = {
    "english": "en",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "italian": "it",
    "portuguese": "pt",
    "japanese": "ja",
    "korean": "ko",
    "arabic": "ar",
    "hindi": "hi",
    "mandarin": "zh-CN",
    "chinese": "zh-CN",
    "russian": "ru",
}


def lang_code(language: str) -> str:
    return _LANG_CODES.get(language.strip().lower(), "en")


class Speaker:
    def say(self, text: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def close(self) -> None:
        pass


class NullSpeaker(Speaker):
    """Does nothing — used when TTS is disabled or unavailable."""

    def say(self, text: str) -> None:
        return


class GttsSpeaker(Speaker):
    def __init__(self, language: str):
        from gtts import gTTS  # noqa: F401  (import check)

        self.language = lang_code(language)
        self._player = _find_player()

    def say(self, text: str) -> None:
        from gtts import gTTS

        if not text.strip():
            return
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fh:
            path = fh.name
        gTTS(text=text, lang=self.language).save(path)
        if self._player:
            subprocess.run(
                self._player + [path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )


class Pyttsx3Speaker(Speaker):
    def __init__(self, language: str):
        import pyttsx3

        self.engine = pyttsx3.init()

    def say(self, text: str) -> None:
        if not text.strip():
            return
        self.engine.say(text)
        self.engine.runAndWait()


def _find_player():
    for cmd in (["mpg123", "-q"], ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"],
                ["afplay"], ["cvlc", "--play-and-exit", "--intf", "dummy"]):
        if shutil.which(cmd[0]):
            return cmd
    return None


def make_speaker(enabled: bool, language: str = "English") -> Speaker:
    """Best-effort speaker factory. Never raises — falls back to silence."""
    if not enabled:
        return NullSpeaker()
    try:
        return GttsSpeaker(language)
    except Exception:
        pass
    try:
        return Pyttsx3Speaker(language)
    except Exception:
        pass
    return NullSpeaker()
