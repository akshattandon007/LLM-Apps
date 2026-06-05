"""
features.py
===========

Feature extraction from segmented heartbeats.

The ECG-biometrics literature splits features into:

* **fiducial** features -- amplitudes and intervals measured at the P, Q, R, S,
  T landmarks (e.g. QRS width, R-S amplitude, area under the complex);
* **non-fiducial** features -- representations that do not require precise
  landmark detection, e.g. the autocorrelation (AC) of the beat combined with a
  discrete cosine transform (DCT) -- the well-known AC/DCT approach -- or simply
  the normalised beat samples themselves.

This module computes a compact **hybrid** feature vector that combines both,
which is robust and works well with simple classifiers. See docs/RESEARCH.md.
"""

from __future__ import annotations

import numpy as np
from scipy.fftpack import dct


def _autocorr_dct(beat: np.ndarray, n_lags: int = 60, n_dct: int = 20) -> np.ndarray:
    """Autocorrelation followed by DCT (the classic non-fiducial AC/DCT feature).

    The autocorrelation is shift-invariant, so it tolerates small R-peak
    misalignment; the DCT compresses it into a few decorrelated coefficients.
    """
    b = beat - beat.mean()
    ac = np.correlate(b, b, mode="full")
    ac = ac[ac.size // 2:]                       # keep non-negative lags
    ac = ac[:n_lags]
    if ac[0] > 1e-12:
        ac = ac / ac[0]                          # normalise by zero-lag energy
    coeffs = dct(ac, type=2, norm="ortho")[:n_dct]
    return coeffs


def _fiducial_features(beat: np.ndarray, fs: int, pre_ms: float = 250.0) -> np.ndarray:
    """Simple fiducial features measured relative to the central R peak.

    The beat is R-aligned, so the R peak sits at sample ``pre`` (= pre_ms).
    We locate Q and S as the minima immediately around R, and P and T as the
    maxima in the windows before Q and after S respectively, then derive a
    handful of amplitude / interval / area descriptors.
    """
    pre = int(round(pre_ms / 1000.0 * fs))
    n = len(beat)
    r_idx = int(np.clip(pre, 1, n - 2))

    # Q: minimum in the 50 ms just before R; S: minimum in 50 ms just after R.
    w = max(1, int(round(0.05 * fs)))
    q_lo = max(0, r_idx - w)
    s_hi = min(n, r_idx + w + 1)
    q_idx = q_lo + int(np.argmin(beat[q_lo:r_idx + 1])) if r_idx > q_lo else r_idx
    s_idx = r_idx + int(np.argmin(beat[r_idx:s_hi])) if s_hi > r_idx else r_idx

    # P: max in the window before Q; T: max in the window after S.
    p_win = beat[max(0, q_idx - int(0.2 * fs)):max(1, q_idx)]
    t_win = beat[min(n - 1, s_idx + int(0.05 * fs)):min(n, s_idx + int(0.4 * fs))]
    p_amp = float(p_win.max()) if p_win.size else 0.0
    t_amp = float(t_win.max()) if t_win.size else 0.0

    r_amp = float(beat[r_idx])
    q_amp = float(beat[q_idx])
    s_amp = float(beat[s_idx])

    qrs_width = (s_idx - q_idx) / fs                 # seconds
    rs_amp = r_amp - s_amp
    rq_amp = r_amp - q_amp
    qrs_area = float(np.trapezoid(np.abs(beat[q_idx:s_idx + 1]))) / fs \
        if s_idx > q_idx else 0.0

    return np.array([
        r_amp, q_amp, s_amp, p_amp, t_amp,
        rs_amp, rq_amp, qrs_width, qrs_area,
        (s_idx - r_idx) / fs, (r_idx - q_idx) / fs,
    ], dtype=float)


def extract_features(
    beats: np.ndarray,
    fs: int,
    pre_ms: float = 250.0,
    use_fiducial: bool = True,
    use_ac_dct: bool = True,
    use_raw: bool = True,
    raw_downsample: int = 4,
) -> np.ndarray:
    """Compute a feature matrix from a matrix of beats.

    Parameters
    ----------
    beats : np.ndarray, shape (n_beats, beat_len)
        Segmented, normalised heartbeats.
    fs : int
        Sampling frequency.
    use_fiducial, use_ac_dct, use_raw : bool
        Which feature families to include in the (concatenated) vector.
    raw_downsample : int
        Decimation factor applied to the raw normalised beat when ``use_raw``.

    Returns
    -------
    X : np.ndarray, shape (n_beats, n_features)
    """
    if beats.ndim != 2 or beats.shape[0] == 0:
        return np.empty((0, 0))

    rows = []
    for beat in beats:
        parts = []
        if use_raw:
            parts.append(beat[::raw_downsample])
        if use_ac_dct:
            parts.append(_autocorr_dct(beat))
        if use_fiducial:
            parts.append(_fiducial_features(beat, fs, pre_ms=pre_ms))
        rows.append(np.concatenate(parts))
    return np.vstack(rows)
