"""
preprocessing.py
================

ECG preprocessing stage of the biometric pipeline.

Raw ECG is corrupted by several well-characterised artefacts:

* baseline wander  -- low-frequency drift (< 0.5 Hz) from respiration and
  electrode motion;
* powerline interference -- 50/60 Hz mains pickup;
* high-frequency noise -- muscle (EMG) activity and electronics.

The functions here remove those artefacts. Two filter goals are supported:

* a *morphology* band (~0.5-40 Hz) that preserves the PQRST shape used for
  biometric feature extraction;
* a *QRS-emphasis* band (~5-15 Hz) used inside the Pan-Tompkins R-peak
  detector (see qrs_detection.py).

References
----------
Pan & Tompkins (1985); ECG biometrics surveys recommend z-score / R-peak
amplitude normalisation after filtering (see docs/RESEARCH.md).
"""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, filtfilt, iirnotch


def bandpass_filter(signal: np.ndarray, fs: int,
                    low: float = 0.5, high: float = 40.0,
                    order: int = 4) -> np.ndarray:
    """Zero-phase Butterworth band-pass filter.

    ``filtfilt`` is used so the filter introduces no phase distortion -- this
    matters because the biometric features depend on the relative timing of
    the P, Q, R, S and T deflections.
    """
    nyq = 0.5 * fs
    high = min(high, nyq * 0.99)
    b, a = butter(order, [low / nyq, high / nyq], btype="band")
    return filtfilt(b, a, signal)


def remove_baseline_wander(signal: np.ndarray, fs: int,
                           cutoff: float = 0.5, order: int = 2) -> np.ndarray:
    """High-pass filter to suppress low-frequency baseline drift."""
    nyq = 0.5 * fs
    b, a = butter(order, cutoff / nyq, btype="high")
    return filtfilt(b, a, signal)


def notch_filter(signal: np.ndarray, fs: int,
                 freq: float = 50.0, q: float = 30.0) -> np.ndarray:
    """Remove powerline interference at ``freq`` Hz (50 Hz EU / 60 Hz US)."""
    b, a = iirnotch(freq / (0.5 * fs), q)
    return filtfilt(b, a, signal)


def preprocess(signal: np.ndarray, fs: int,
               powerline: float | None = 50.0,
               low: float = 0.5, high: float = 40.0) -> np.ndarray:
    """Full preprocessing chain for morphology-preserving biometric use.

    Steps: optional powerline notch -> band-pass (baseline + HF noise removal).
    The output is suitable both for R-peak detection and for beat
    segmentation / feature extraction.
    """
    out = np.asarray(signal, dtype=float)
    if powerline is not None and powerline < 0.5 * fs:
        out = notch_filter(out, fs, freq=powerline)
    out = bandpass_filter(out, fs, low=low, high=high)
    return out
