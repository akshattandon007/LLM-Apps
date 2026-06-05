"""
segmentation.py
===============

Segment a continuous ECG into individual heartbeats, each aligned on its
R peak.

A biometric "sample" is a single heartbeat (or a small group of heartbeats).
We extract a fixed-length window around every detected R peak so that all
beats are the same length and are R-aligned -- a prerequisite for comparing
their morphology.

Following common practice in the ECG-biometrics literature, each beat is:
  * windowed roughly 250 ms before to 450 ms after the R peak (covers the full
    PQRST complex across the physiological heart-rate range);
  * amplitude-normalised (z-score) to remove gain/electrode differences;
  * optionally screened as an outlier (ectopic beats / artefacts) by
    correlation against the median beat.
"""

from __future__ import annotations

import numpy as np


def segment_beats(
    signal: np.ndarray,
    rpeaks: np.ndarray,
    fs: int,
    pre_ms: float = 250.0,
    post_ms: float = 450.0,
    normalize: bool = True,
    reject_outliers: bool = True,
    corr_threshold: float = 0.8,
) -> np.ndarray:
    """Extract R-aligned, fixed-length, normalised heartbeats.

    Parameters
    ----------
    signal : np.ndarray
        Preprocessed ECG (morphology band).
    rpeaks : np.ndarray
        R-peak sample indices.
    fs : int
        Sampling frequency (Hz).
    pre_ms, post_ms : float
        Window extent before/after each R peak in milliseconds.
    normalize : bool
        If True, z-score each beat (zero mean, unit variance).
    reject_outliers : bool
        If True, discard beats poorly correlated with the median beat
        (ectopic beats, motion artefacts).
    corr_threshold : float
        Minimum Pearson correlation with the median beat to keep a beat.

    Returns
    -------
    beats : np.ndarray, shape (n_beats, beat_len)
        Matrix of segmented heartbeats (one per row).
    """
    pre = int(round(pre_ms / 1000.0 * fs))
    post = int(round(post_ms / 1000.0 * fs))
    beat_len = pre + post

    beats = []
    for r in rpeaks:
        start, end = r - pre, r + post
        if start < 0 or end > len(signal):
            continue                      # drop truncated edge beats
        beat = signal[start:end].astype(float)
        if normalize:
            std = beat.std()
            beat = (beat - beat.mean()) / std if std > 1e-8 else beat - beat.mean()
        beats.append(beat)

    if not beats:
        return np.empty((0, beat_len))
    beats = np.vstack(beats)

    if reject_outliers and len(beats) >= 3:
        beats = _reject_outliers(beats, corr_threshold)

    return beats


def _reject_outliers(beats: np.ndarray, corr_threshold: float) -> np.ndarray:
    """Drop beats whose correlation with the median template is too low."""
    template = np.median(beats, axis=0)
    t = template - template.mean()
    t_norm = np.linalg.norm(t) + 1e-12

    keep = []
    for beat in beats:
        b = beat - beat.mean()
        corr = float(np.dot(b, t) / ((np.linalg.norm(b) + 1e-12) * t_norm))
        keep.append(corr >= corr_threshold)

    kept = beats[np.array(keep)]
    # Never throw everything away; fall back to all beats if too aggressive.
    return kept if len(kept) >= max(2, int(0.3 * len(beats))) else beats
