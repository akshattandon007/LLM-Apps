"""
Test suite for the Heartbeat-ID pipeline.

Run with:  pytest -q

The tests exercise every stage on reproducible synthetic dummy data and assert
sensible behaviour (correct heart rate recovery, plausible beat counts, and
high closed-set identification accuracy with very low verification error).
"""

import numpy as np
import pytest

from heartbeat_id.ecg_synth import generate_population, generate_subject_ecg
from heartbeat_id.preprocessing import preprocess
from heartbeat_id.qrs_detection import pan_tompkins_detect, heart_rate_bpm
from heartbeat_id.segmentation import segment_beats
from heartbeat_id.features import extract_features
from heartbeat_id.biometric import (
    HeartbeatID, identification_accuracy, equal_error_rate,
)

FS = 250


@pytest.fixture(scope="module")
def population():
    return generate_population(8, seed=7)


@pytest.fixture(scope="module")
def split(population):
    enroll, test = [], []
    for p in population:
        _, e = generate_subject_ecg(p, duration_s=30, fs=FS,
                                    seed=1000 + p.subject_id)
        _, t = generate_subject_ecg(p, duration_s=15, fs=FS,
                                    seed=5000 + p.subject_id)
        enroll.append((p.subject_id, e))
        test.append((p.subject_id, t))
    return enroll, test


@pytest.fixture(scope="module")
def system(split, population):
    enroll, _ = split
    names = {p.subject_id: p.name for p in population}
    return HeartbeatID(fs=FS).fit(enroll, names=names)


# ----------------------------- synthesis ------------------------------ #
def test_distinct_profiles(population):
    # Different subjects must have different morphology parameters.
    a = population[0].a
    b = population[1].a
    assert not np.allclose(a, b)


def test_signal_shape_and_scale(population):
    _, ecg = generate_subject_ecg(population[0], duration_s=5, fs=FS)
    assert len(ecg) == 5 * FS
    assert 0.4 < np.max(ecg) < 3.0          # physiological R-peak ~1 mV


# ----------------------------- detection ------------------------------ #
def test_heart_rate_recovery(population):
    p = population[0]
    _, ecg = generate_subject_ecg(p, duration_s=20, fs=FS,
                                  noise_mv=0.01, baseline_wander_mv=0.03)
    clean = preprocess(ecg, FS)
    rpeaks = pan_tompkins_detect(clean, FS)
    hr = heart_rate_bpm(rpeaks, FS)
    # Recovered heart rate should be within 8 bpm of the configured mean.
    assert abs(hr - p.hr_mean) < 8.0


def test_beat_count_plausible(population):
    p = population[1]
    _, ecg = generate_subject_ecg(p, duration_s=30, fs=FS)
    clean = preprocess(ecg, FS)
    rpeaks = pan_tompkins_detect(clean, FS)
    expected = 30 * p.hr_mean / 60.0
    assert 0.7 * expected < len(rpeaks) < 1.3 * expected


# --------------------------- segmentation ----------------------------- #
def test_segmentation_shapes(population):
    p = population[2]
    _, ecg = generate_subject_ecg(p, duration_s=20, fs=FS)
    clean = preprocess(ecg, FS)
    rpeaks = pan_tompkins_detect(clean, FS)
    beats = segment_beats(clean, rpeaks, FS)
    assert beats.ndim == 2 and beats.shape[0] >= 5
    # z-scored beats: near-zero mean per beat.
    assert np.allclose(beats.mean(axis=1), 0.0, atol=1e-6)


def test_feature_extraction_nonempty(population):
    p = population[3]
    _, ecg = generate_subject_ecg(p, duration_s=20, fs=FS)
    clean = preprocess(ecg, FS)
    rpeaks = pan_tompkins_detect(clean, FS)
    beats = segment_beats(clean, rpeaks, FS)
    X = extract_features(beats, FS)
    assert X.shape[0] == beats.shape[0] and X.shape[1] > 10
    assert np.isfinite(X).all()


# ----------------------- identification / verification ----------------- #
def test_identification_accuracy(system, split):
    _, test = split
    for method in ("svm", "template"):
        acc = identification_accuracy(system, test, method=method)["accuracy"]
        assert acc >= 0.85, f"{method} accuracy too low: {acc}"


def test_verification_eer(system, split):
    _, test = split
    gen, imp = [], []
    for label, ecg in test:
        for claim in system.subjects:
            s = system.verification_score(ecg, claim)
            (gen if claim == label else imp).append(s)
    eer, _ = equal_error_rate(np.array(gen), np.array(imp))
    assert eer <= 0.10, f"EER too high: {eer}"
    # Genuine scores should exceed impostor scores on average.
    assert np.mean(gen) > np.mean(imp)


def test_impostor_is_rejected_relatively(system, split):
    # A probe should match its own template better than a random other one.
    _, test = split
    label, ecg = test[0]
    own = system.verification_score(ecg, label)
    others = [system.verification_score(ecg, c)
              for c in system.subjects if c != label]
    assert own > max(others)
