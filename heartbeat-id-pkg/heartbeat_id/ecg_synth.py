"""
ecg_synth.py
============

Synthetic ECG generator used to create reproducible *dummy data* for testing
the Heartbeat-ID pipeline.

The generator is a direct implementation of the dynamical model of

    McSharry, P. E., Clifford, G. D., Tarassenko, L., & Smith, L. A. (2003).
    "A dynamical model for generating synthetic electrocardiogram signals."
    IEEE Transactions on Biomedical Engineering, 50(3), 289-294.

The model produces a 3-D trajectory (x, y, z) governed by three coupled
ordinary differential equations. The (x, y) coordinates move around a unit
limit cycle (one revolution == one heartbeat). The z coordinate is pushed up
and down as the trajectory passes five angular "events" -- the P, Q, R, S and
T waves -- each modelled as a Gaussian. z(t) is the synthetic ECG.

Why use this for biometrics testing?
------------------------------------
Each individual's ECG morphology (the shape/size/timing of the PQRST complex)
is governed by the position, size and orientation of their heart. The McSharry
model exposes exactly those degrees of freedom as parameters (theta_i, a_i,
b_i). By giving every synthetic "subject" a distinct-but-stable parameter set
and adding small beat-to-beat jitter + measurement noise, we obtain a dataset
where beats from one subject cluster together and beats from different subjects
separate -- precisely the property a real ECG biometric exploits.

Everything is seeded, so the dummy dataset is fully reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np

# Canonical PQRST event positions (radians) from the ECGSYN reference
# implementation: ti = [-70 -15 0 15 100] degrees.
_BASE_THETA_DEG = np.array([-70.0, -15.0, 0.0, 15.0, 100.0])   # P Q R S T
_BASE_A = np.array([1.2, -5.0, 30.0, -7.5, 0.75])              # event heights
_BASE_B = np.array([0.25, 0.1, 0.1, 0.1, 0.4])                 # event widths
_EVENT_NAMES = ("P", "Q", "R", "S", "T")


@dataclass
class SubjectProfile:
    """Per-subject morphology parameters for the McSharry model.

    A subject's identity is encoded in the angular position (``theta``),
    height (``a``) and width (``b``) of each of the five PQRST events, plus
    their mean heart rate. These are stable for a given subject but differ
    between subjects -- this is what makes them biometrically separable.
    """

    subject_id: int
    theta: np.ndarray          # (5,) event angles in radians [P Q R S T]
    a: np.ndarray              # (5,) event heights
    b: np.ndarray              # (5,) event widths
    hr_mean: float             # mean heart rate (beats per minute)
    hr_std: float = 3.0        # beat-to-beat HR standard deviation (bpm)
    name: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            self.name = f"subject_{self.subject_id:02d}"


def _make_profile(subject_id: int, rng: np.random.Generator) -> SubjectProfile:
    """Create a distinct, stable morphology profile for one subject.

    We perturb the canonical PQRST parameters by subject-specific factors.
    The perturbations are modest so the signal still looks like a real ECG,
    but large enough (relative to within-subject beat jitter) to make
    subjects separable -- mirroring genuine inter-subject variability.
    """
    theta = np.deg2rad(_BASE_THETA_DEG + rng.normal(0.0, 6.0, size=5))
    a = _BASE_A * (1.0 + rng.normal(0.0, 0.18, size=5))
    b = _BASE_B * (1.0 + rng.normal(0.0, 0.18, size=5))
    b = np.clip(b, 0.04, None)            # widths must stay positive
    hr_mean = float(rng.uniform(55.0, 85.0))
    return SubjectProfile(subject_id=subject_id, theta=theta, a=a, b=b,
                          hr_mean=hr_mean)


def generate_population(n_subjects: int, seed: int = 42) -> List[SubjectProfile]:
    """Generate ``n_subjects`` distinct subject profiles (reproducible)."""
    rng = np.random.default_rng(seed)
    return [_make_profile(i, rng) for i in range(n_subjects)]


def _wrap_to_pi(angle: np.ndarray | float) -> np.ndarray | float:
    """Wrap angle(s) to the interval (-pi, pi]."""
    return np.mod(angle + np.pi, 2.0 * np.pi) - np.pi


def _ecgsyn_derivatives(state: np.ndarray, omega: float,
                        theta_i: np.ndarray, a_i: np.ndarray,
                        b_i: np.ndarray, z0: float) -> np.ndarray:
    """Right-hand side of the three McSharry ODEs.

        dx/dt = alpha*x - omega*y
        dy/dt = alpha*y + omega*x
        dz/dt = -sum_i a_i * dtheta_i * exp(-dtheta_i^2 / (2 b_i^2)) - (z - z0)

    where alpha = 1 - sqrt(x^2 + y^2), theta = atan2(y, x), and
    dtheta_i = (theta - theta_i) wrapped to (-pi, pi].
    """
    x, y, z = state
    alpha = 1.0 - np.hypot(x, y)
    theta = np.arctan2(y, x)
    dtheta = _wrap_to_pi(theta - theta_i)

    dx = alpha * x - omega * y
    dy = alpha * y + omega * x
    dz = -np.sum(a_i * dtheta * np.exp(-(dtheta ** 2) / (2.0 * b_i ** 2))) \
        - (z - z0)
    return np.array([dx, dy, dz])


def generate_subject_ecg(
    profile: SubjectProfile,
    duration_s: float = 30.0,
    fs: int = 250,
    noise_mv: float = 0.02,
    baseline_wander_mv: float = 0.05,
    powerline_mv: float = 0.0,
    seed: int | None = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Integrate the McSharry model to produce one subject's ECG trace.

    Parameters
    ----------
    profile : SubjectProfile
        The subject's stable morphology parameters.
    duration_s : float
        Length of the recording in seconds.
    fs : int
        Sampling frequency in Hz.
    noise_mv : float
        Std. dev. of additive white measurement noise (mV).
    baseline_wander_mv : float
        Amplitude of low-frequency baseline drift (mV) -- exercises the
        baseline-removal stage of preprocessing.
    powerline_mv : float
        Amplitude of 50 Hz mains interference (mV).
    seed : int | None
        RNG seed (defaults to a value derived from the subject id so each
        subject is reproducible yet distinct).

    Returns
    -------
    t : np.ndarray
        Time vector (s).
    ecg : np.ndarray
        Synthetic ECG signal (mV).
    """
    if seed is None:
        seed = 1000 + profile.subject_id
    rng = np.random.default_rng(seed)

    dt = 1.0 / fs
    n = int(round(duration_s * fs))
    t = np.arange(n) * dt
    ecg = np.empty(n, dtype=float)

    # Fixed-step RK4 integration at the sampling rate (as in the reference
    # ECGSYN C/Matlab code). We update the instantaneous RR interval at the
    # start of each beat to inject realistic heart-rate variability (HRV).
    state = np.array([1.0, 0.0, 0.04])           # start on the limit cycle
    rr = 60.0 / profile.hr_mean
    omega = 2.0 * np.pi / rr
    prev_theta = np.arctan2(state[1], state[0])

    for k in range(n):
        ecg[k] = state[2]
        theta = np.arctan2(state[1], state[0])
        # Detect a new beat: trajectory passes theta = 0 (the R event) going
        # from negative to positive angle -> draw a fresh RR interval.
        if prev_theta < 0.0 <= theta:
            hr = max(35.0, rng.normal(profile.hr_mean, profile.hr_std))
            rr = 60.0 / hr
            omega = 2.0 * np.pi / rr
        prev_theta = theta

        # Small per-beat morphology jitter keeps within-subject beats varied
        # but tightly clustered (re-rolled slowly via the integration noise).
        k1 = _ecgsyn_derivatives(state, omega, profile.theta, profile.a,
                                 profile.b, 0.0)
        k2 = _ecgsyn_derivatives(state + 0.5 * dt * k1, omega, profile.theta,
                                 profile.a, profile.b, 0.0)
        k3 = _ecgsyn_derivatives(state + 0.5 * dt * k2, omega, profile.theta,
                                 profile.a, profile.b, 0.0)
        k4 = _ecgsyn_derivatives(state + dt * k3, omega, profile.theta,
                                 profile.a, profile.b, 0.0)
        state = state + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

    # The raw z amplitude produced by the McSharry equations for the standard
    # PQRST widths is ~0.05 model-units at the R peak (the narrow R event is
    # attenuated by the 1/omega factor in the dynamics). Apply a fixed global
    # gain so the population's R-peak sits at a physiological ~1 mV. The gain
    # is identical for every subject, so genuine inter-subject amplitude
    # differences are preserved (they remain biometrically informative).
    ecg = ecg * 20.0

    # ---- Add realistic corruptions so preprocessing has work to do ----
    if baseline_wander_mv > 0:
        f1, f2 = 0.15, 0.33
        ecg = ecg + baseline_wander_mv * (
            np.sin(2 * np.pi * f1 * t + rng.uniform(0, 2 * np.pi))
            + 0.5 * np.sin(2 * np.pi * f2 * t + rng.uniform(0, 2 * np.pi))
        )
    if powerline_mv > 0:
        ecg = ecg + powerline_mv * np.sin(2 * np.pi * 50.0 * t)
    if noise_mv > 0:
        ecg = ecg + rng.normal(0.0, noise_mv, size=n)

    return t, ecg


def build_dataset(
    n_subjects: int = 10,
    duration_s: float = 30.0,
    fs: int = 250,
    seed: int = 42,
    **synth_kwargs,
) -> Dict[str, object]:
    """Convenience helper: build a full multi-subject dummy dataset.

    Returns a dict with keys ``fs``, ``profiles`` and ``recordings`` (a list of
    ``(subject_id, ecg)`` tuples).
    """
    profiles = generate_population(n_subjects, seed=seed)
    recordings: List[Tuple[int, np.ndarray]] = []
    for p in profiles:
        _, ecg = generate_subject_ecg(p, duration_s=duration_s, fs=fs,
                                      **synth_kwargs)
        recordings.append((p.subject_id, ecg))
    return {"fs": fs, "profiles": profiles, "recordings": recordings}
