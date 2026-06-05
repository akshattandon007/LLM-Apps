"""
heartbeat_id
============

A reference implementation of an ECG-based biometric identification system
("Heartbeat ID").

The package implements the classic biometric pipeline found in the ECG
biometrics literature:

    raw ECG -> preprocessing -> R-peak detection (Pan-Tompkins)
            -> beat segmentation -> feature extraction
            -> enrolment / identification / verification

It also ships an ECGSYN-style synthetic ECG generator (McSharry et al., 2003)
so the whole pipeline can be exercised end-to-end on reproducible dummy data
without needing access to a clinical recording database.

See docs/RESEARCH.md for the literature this implementation is based on.
"""

from .ecg_synth import SubjectProfile, generate_population, generate_subject_ecg
from .preprocessing import bandpass_filter, remove_baseline_wander, preprocess
from .qrs_detection import pan_tompkins_detect
from .segmentation import segment_beats
from .features import extract_features
from .biometric import HeartbeatID

__all__ = [
    "SubjectProfile",
    "generate_population",
    "generate_subject_ecg",
    "bandpass_filter",
    "remove_baseline_wander",
    "preprocess",
    "pan_tompkins_detect",
    "segment_beats",
    "extract_features",
    "HeartbeatID",
]

__version__ = "1.0.0"
