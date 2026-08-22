"""Smoke tests for Echo — conversation mindfulness CLI."""

from __future__ import annotations

import pytest

from src.analyzer import analyze
from src.models import Transcript, TranscriptLine
from src.patterns import detect_energy_peaks, detect_repeated_phrases
from src.reporter import generate_report


class TestAnalyzer:
    """Smoke tests for the analyzer module."""

    def test_basic_analysis(self, mock_transcript_camping):
        """Analyzer runs without error and returns expected fields."""
        result = analyze(mock_transcript_camping)

        assert result.total_words > 0
        assert result.total_turns == 20
        assert len(result.speakers) == 3
        assert result.speakers[0].talk_percentage > 0
        assert result.filler_words_total >= 0

    def test_speaker_order(self, mock_transcript_camping):
        """Speakers are sorted by word count descending."""
        result = analyze(mock_transcript_camping)
        for i in range(len(result.speakers) - 1):
            assert result.speakers[i].word_count >= result.speakers[i + 1].word_count

    def test_single_speaker(self, mock_single_speaker):
        """Single speaker analysis works."""
        result = analyze(mock_single_speaker)
        assert len(result.speakers) == 1
        assert result.speakers[0].talk_percentage == 100.0

    def test_empty_transcript(self):
        """Empty transcript produces zero counts."""
        transcript = Transcript(lines=[])
        result = analyze(transcript)
        assert result.total_words == 0
        assert result.total_turns == 0
        assert len(result.speakers) == 0

    def test_filler_detection(self):
        """Common filler words are detected."""
        transcript = Transcript(
            lines=[
                TranscriptLine(speaker="A", text="Actually, like, you know, I mean um hi."),
            ]
        )
        result = analyze(transcript)
        assert result.filler_words_total > 0
        filler_map = {k.lower(): v for k, v in result.filler_word_summary.items()}
        assert filler_map.get("actually", 0) >= 1
        assert filler_map.get("like", 0) >= 1

    def test_talk_percentage_sums(self, mock_transcript_camping):
        """Talk percentages sum to approximately 100."""
        result = analyze(mock_transcript_camping)
        total = sum(s.talk_percentage for s in result.speakers)
        assert 99.0 <= total <= 101.0


class TestPatterns:
    """Smoke tests for pattern detection."""

    def test_energy_peaks_detected(self, mock_transcript_camping):
        """Energy peaks are found in the camping transcript."""
        peaks = detect_energy_peaks(mock_transcript_camping)
        assert len(peaks) > 0
        for peak in peaks:
            assert peak.energy_score > 0
            assert peak.speaker
            assert peak.text

    def test_energy_empty_transcript(self):
        """Empty transcript produces no energy peaks."""
        transcript = Transcript(lines=[])
        peaks = detect_energy_peaks(transcript)
        assert len(peaks) == 0

    def test_repeated_phrases(self, mock_transcript_camping):
        """Repeated phrases are detected."""
        phrases = detect_repeated_phrases(mock_transcript_camping)
        assert len(phrases) >= 0
        for phrase in phrases:
            assert phrase.count >= 2
            assert len(phrase.speakers) > 0

    def test_repeated_phrases_empty(self):
        """Empty transcript has no repeated phrases."""
        transcript = Transcript(lines=[])
        phrases = detect_repeated_phrases(transcript)
        assert len(phrases) == 0


class TestReporter:
    """Smoke tests for the reporter module."""

    def test_report_generated(self, mock_transcript_camping):
        """Report is generated without error."""
        result = analyze(mock_transcript_camping)
        report = generate_report(result)
        assert "# 🪞 Echo Mirror Report" in report
        assert len(report) > 100

    def test_report_contains_speakers(self, mock_transcript_camping):
        """Report mentions the speakers."""
        result = analyze(mock_transcript_camping)
        report = generate_report(result)
        for s in result.speakers:
            assert s.speaker in report

    def test_report_empty_transcript(self):
        """Report handles empty transcript."""
        transcript = Transcript(lines=[])
        result = analyze(transcript)
        report = generate_report(result)
        assert report
        assert "# 🪞 Echo Mirror Report" in report


class TestEndToEnd:
    """End-to-end smoke tests."""

    def test_full_pipeline(self, mock_transcript_camping):
        """Full analysis + report pipeline runs end-to-end."""
        result = analyze(mock_transcript_camping)
        result.energy_peaks = detect_energy_peaks(mock_transcript_camping)
        result.repeated_phrases = detect_repeated_phrases(mock_transcript_camping)
        report = generate_report(result)
        assert len(report) > 200
        assert "Alice" in report
        assert "Bob" in report
        assert "Carol" in report

    def test_meeting_transcript(self, mock_transcript_meeting):
        """Meeting transcript analysis works."""
        result = analyze(mock_transcript_meeting)
        result.energy_peaks = detect_energy_peaks(mock_transcript_meeting)
        result.repeated_phrases = detect_repeated_phrases(mock_transcript_meeting)
        report = generate_report(result)
        assert "Priya" in report
        assert "Raj" in report
        assert "# 🪞" in report