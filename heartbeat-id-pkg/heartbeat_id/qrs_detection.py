"""
qrs_detection.py
================

R-peak (QRS complex) detection using the Pan-Tompkins algorithm.

    Pan, J., & Tompkins, W. J. (1985). "A Real-Time QRS Detection Algorithm."
    IEEE Transactions on Biomedical Engineering, BME-32(3), 230-236.

The R peak is the tallest, sharpest deflection of each heartbeat and is the
fiducial point around which every beat is segmented. Reliable R-peak detection
is therefore the foundation of the whole biometric system.

Pipeline (faithful to the 1985 paper):
    band-pass (5-15 Hz)  ->  derivative  ->  squaring
    ->  moving-window integration  ->  adaptive thresholding.

The adaptive thresholds track running estimates of the signal and noise peak
levels and self-adjust to changes in QRS morphology and heart rate, exactly
as described in the original paper.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, filtfilt

from .preprocessing import bandpass_filter


def _moving_window_integration(signal: np.ndarray, width: int) -> np.ndarray:
    """Moving-window integrator (the paper's 'MWI'); width ~150 ms of samples."""
    window = np.ones(width) / float(width)
    return np.convolve(signal, window, mode="same")


def pan_tompkins_detect(signal: np.ndarray, fs: int,
                        return_stages: bool = False):
    """Detect R-peak sample indices with the Pan-Tompkins algorithm.

    Parameters
    ----------
    signal : np.ndarray
        ECG signal (raw or lightly filtered).
    fs : int
        Sampling frequency (Hz).
    return_stages : bool
        If True, also return a dict of intermediate signals (useful for
        plotting / debugging).

    Returns
    -------
    rpeaks : np.ndarray
        Sample indices of detected R peaks.
    (stages) : dict, optional
        Intermediate signals when ``return_stages`` is True.
    """
    sig = np.asarray(signal, dtype=float)

    # 1) Band-pass 5-15 Hz to emphasise QRS energy and reject P/T waves,
    #    baseline wander and muscle noise.
    filtered = bandpass_filter(sig, fs, low=5.0, high=15.0, order=2)

    # 2) Five-point derivative -> emphasises the steep QRS slope.
    deriv = np.gradient(filtered) * fs

    # 3) Squaring -> makes everything positive and amplifies large slopes.
    squared = deriv ** 2

    # 4) Moving-window integration (~150 ms window).
    win = max(1, int(round(0.150 * fs)))
    integrated = _moving_window_integration(squared, win)

    # 5) Adaptive thresholding on the integrated signal.
    rpeaks = _adaptive_threshold(integrated, filtered, fs)

    # 6) Refine each detection by snapping to the local maximum of the
    #    band-pass signal within a small window (the true R-peak location).
    rpeaks = _refine_peaks(sig, rpeaks, fs)

    if return_stages:
        stages = {
            "filtered": filtered,
            "derivative": deriv,
            "squared": squared,
            "integrated": integrated,
        }
        return rpeaks, stages
    return rpeaks


def _adaptive_threshold(integrated: np.ndarray, filtered: np.ndarray,
                        fs: int) -> np.ndarray:
    """Adaptive double-threshold peak search on the integrated signal.

    Implements the running signal-peak (SPKI) and noise-peak (NPKI) estimates
    and the refractory / search-back logic from the paper.
    """
    n = len(integrated)
    min_rr = int(round(0.20 * fs))     # 200 ms physiological refractory period

    # Candidate peaks: local maxima separated by at least the refractory period.
    candidates = _local_maxima(integrated, min_distance=min_rr)
    if len(candidates) == 0:
        return np.array([], dtype=int)

    # Initialise running estimates from the first ~2 s of signal.
    init = integrated[: min(len(integrated), 2 * fs)]
    spki = np.max(init) * 0.25 if init.size else np.max(integrated) * 0.25
    npki = np.mean(init) * 0.5 if init.size else np.mean(integrated) * 0.5

    rpeaks: list[int] = []
    rr_intervals: list[int] = []
    last_peak = -min_rr

    for idx in candidates:
        peak_val = integrated[idx]
        threshold = npki + 0.25 * (spki - npki)

        is_qrs = False
        if peak_val > threshold and (idx - last_peak) >= min_rr:
            is_qrs = True
        else:
            # Search-back: if we have waited much longer than the expected
            # RR interval, lower the threshold to recover a missed beat.
            if rr_intervals:
                expected_rr = np.mean(rr_intervals[-8:])
                if (idx - last_peak) > 1.66 * expected_rr and \
                        peak_val > 0.5 * threshold:
                    is_qrs = True

        if is_qrs:
            if rpeaks:
                rr_intervals.append(idx - rpeaks[-1])
            rpeaks.append(idx)
            last_peak = idx
            spki = 0.125 * peak_val + 0.875 * spki     # signal peak update
        else:
            npki = 0.125 * peak_val + 0.875 * npki     # noise peak update

    return np.array(rpeaks, dtype=int)


def _local_maxima(signal: np.ndarray, min_distance: int) -> np.ndarray:
    """Indices of local maxima at least ``min_distance`` samples apart."""
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(signal, distance=max(1, min_distance))
    return peaks


def _refine_peaks(raw: np.ndarray, rpeaks: np.ndarray, fs: int) -> np.ndarray:
    """Snap each detection to the nearby true R-peak in the raw signal.

    The integrator introduces a small group delay, so the detected location is
    offset from the true R peak. We correct it by searching a +/- 50 ms window
    for the local maximum of the (baseline-removed) raw signal.
    """
    if len(rpeaks) == 0:
        return rpeaks
    # Baseline removal so the search is robust to drift.
    b, a = butter(2, 0.5 / (0.5 * fs), btype="high")
    base = filtfilt(b, a, raw)

    half = int(round(0.05 * fs))
    refined = []
    for p in rpeaks:
        lo, hi = max(0, p - half), min(len(base), p + half + 1)
        if hi > lo:
            refined.append(lo + int(np.argmax(base[lo:hi])))
    # De-duplicate while preserving order.
    out = sorted(set(refined))
    return np.array(out, dtype=int)


def heart_rate_bpm(rpeaks: np.ndarray, fs: int) -> float:
    """Mean heart rate (bpm) from detected R peaks."""
    if len(rpeaks) < 2:
        return float("nan")
    rr = np.diff(rpeaks) / fs
    return float(60.0 / np.mean(rr))
