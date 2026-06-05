"""
biometric.py
============

The Heartbeat-ID biometric engine.

It supports the two canonical biometric tasks:

* **Identification (1:N)** -- "Who is this?" Given an unknown set of heartbeats,
  return the most likely enrolled subject.
* **Verification (1:1)** -- "Is this who they claim to be?" Given heartbeats and
  a claimed identity, accept or reject. Performance is summarised by the Equal
  Error Rate (EER), the operating point where the false-accept and false-reject
  rates are equal.

Two complementary matchers are implemented:

* a **template matcher** (per-subject mean feature vector + cosine similarity),
  which is transparent and needs no training beyond averaging;
* an **SVM classifier** (RBF kernel) over the feature vectors, which typically
  gives the strongest identification accuracy.

Robustness is improved with **multi-beat fusion**: several beats are classified
and combined by majority vote (identification) or score averaging
(verification), reflecting the literature finding that fusing a few heartbeats
sharply increases accuracy.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from .preprocessing import preprocess
from .qrs_detection import pan_tompkins_detect
from .segmentation import segment_beats
from .features import extract_features


@dataclass
class EnrolledSubject:
    label: int
    name: str
    template: np.ndarray          # mean (scaled) feature vector
    n_beats: int


class HeartbeatID:
    """End-to-end ECG biometric identification / verification system."""

    def __init__(self, fs: int = 250, powerline: float | None = 50.0,
                 pre_ms: float = 250.0, post_ms: float = 450.0):
        self.fs = fs
        self.powerline = powerline
        self.pre_ms = pre_ms
        self.post_ms = post_ms

        self.scaler: StandardScaler | None = None
        self.svm: SVC | None = None
        self.subjects: Dict[int, EnrolledSubject] = {}
        self._names: Dict[int, str] = {}

    # ------------------------------------------------------------------ #
    # Signal -> beats -> features
    # ------------------------------------------------------------------ #
    def beats_from_signal(self, ecg: np.ndarray) -> np.ndarray:
        """Run the full front-end: preprocess -> detect R peaks -> segment."""
        clean = preprocess(ecg, self.fs, powerline=self.powerline)
        rpeaks = pan_tompkins_detect(clean, self.fs)
        beats = segment_beats(clean, rpeaks, self.fs,
                              pre_ms=self.pre_ms, post_ms=self.post_ms)
        return beats

    def features_from_signal(self, ecg: np.ndarray) -> np.ndarray:
        beats = self.beats_from_signal(ecg)
        return extract_features(beats, self.fs, pre_ms=self.pre_ms)

    # ------------------------------------------------------------------ #
    # Training / enrolment
    # ------------------------------------------------------------------ #
    def fit(self, samples: List[Tuple[int, np.ndarray]],
            names: Dict[int, str] | None = None) -> "HeartbeatID":
        """Enrol subjects from labelled ECG recordings.

        Parameters
        ----------
        samples : list of (label, ecg)
            Each tuple is one enrolment recording for a subject ``label``.
        names : dict, optional
            Optional mapping from label -> human-readable name.
        """
        self._names = names or {}
        X_list, y_list = [], []
        per_subject_feats: Dict[int, List[np.ndarray]] = {}

        for label, ecg in samples:
            feats = self.features_from_signal(ecg)
            if feats.shape[0] == 0:
                continue
            X_list.append(feats)
            y_list.append(np.full(feats.shape[0], label))
            per_subject_feats.setdefault(label, []).append(feats)

        if not X_list:
            raise ValueError("No beats could be extracted from enrolment data.")

        X = np.vstack(X_list)
        y = np.concatenate(y_list)

        # Standardise features (zero mean / unit variance) before matching.
        self.scaler = StandardScaler().fit(X)
        Xs = self.scaler.transform(X)

        # Per-subject template = mean scaled feature vector.
        self.subjects = {}
        for label, feat_chunks in per_subject_feats.items():
            feats = self.scaler.transform(np.vstack(feat_chunks))
            self.subjects[label] = EnrolledSubject(
                label=label,
                name=self._names.get(label, f"subject_{label:02d}"),
                template=feats.mean(axis=0),
                n_beats=feats.shape[0],
            )

        # Train an SVM classifier over individual beats.
        self.svm = SVC(kernel="rbf", C=10.0, gamma="scale", probability=True)
        self.svm.fit(Xs, y)
        return self

    # ------------------------------------------------------------------ #
    # Identification (1:N)
    # ------------------------------------------------------------------ #
    def _template_scores(self, feat_scaled: np.ndarray) -> Dict[int, float]:
        """Cosine similarity of one scaled feature vector to every template."""
        scores = {}
        for label, subj in self.subjects.items():
            a, b = feat_scaled, subj.template
            denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-12
            scores[label] = float(np.dot(a, b) / denom)
        return scores

    def identify(self, ecg: np.ndarray, method: str = "svm") -> Dict[str, object]:
        """Identify the subject behind an unknown ECG recording (1:N).

        Uses multi-beat fusion: every beat votes and the winner is returned.

        Returns a dict with the predicted ``label``, ``name``, ``confidence``
        (vote fraction) and the per-beat ``votes``.
        """
        feats = self.features_from_signal(ecg)
        if feats.shape[0] == 0:
            return {"label": None, "name": None, "confidence": 0.0,
                    "votes": {}, "n_beats": 0}
        Xs = self.scaler.transform(feats)

        if method == "svm":
            preds = self.svm.predict(Xs)
        elif method == "template":
            preds = np.array([
                max(self._template_scores(x).items(), key=lambda kv: kv[1])[0]
                for x in Xs
            ])
        else:
            raise ValueError("method must be 'svm' or 'template'")

        votes = Counter(int(p) for p in preds)
        winner, count = votes.most_common(1)[0]
        return {
            "label": winner,
            "name": self.subjects[winner].name,
            "confidence": count / len(preds),
            "votes": dict(votes),
            "n_beats": int(len(preds)),
        }

    # ------------------------------------------------------------------ #
    # Verification (1:1)
    # ------------------------------------------------------------------ #
    def verification_score(self, ecg: np.ndarray, claimed_label: int) -> float:
        """Mean cosine similarity between the probe's beats and the claimed
        subject's template -- a 1:1 match score in [-1, 1]."""
        feats = self.features_from_signal(ecg)
        if feats.shape[0] == 0 or claimed_label not in self.subjects:
            return -1.0
        Xs = self.scaler.transform(feats)
        template = self.subjects[claimed_label].template
        tn = np.linalg.norm(template) + 1e-12
        sims = [float(np.dot(x, template) / ((np.linalg.norm(x) + 1e-12) * tn))
                for x in Xs]
        return float(np.mean(sims))


# ---------------------------------------------------------------------- #
# Evaluation helpers
# ---------------------------------------------------------------------- #
def identification_accuracy(
    system: HeartbeatID,
    test_samples: List[Tuple[int, np.ndarray]],
    method: str = "svm",
) -> Dict[str, object]:
    """Closed-set identification accuracy over a list of (label, ecg) probes."""
    correct = 0
    results = []
    for true_label, ecg in test_samples:
        res = system.identify(ecg, method=method)
        ok = (res["label"] == true_label)
        correct += int(ok)
        results.append((true_label, res["label"], res["confidence"], ok))
    acc = correct / len(test_samples) if test_samples else 0.0
    return {"accuracy": acc, "n": len(test_samples), "details": results}


def equal_error_rate(genuine: np.ndarray, impostor: np.ndarray
                     ) -> Tuple[float, float]:
    """Compute the Equal Error Rate (EER) and its threshold from match scores.

    Parameters
    ----------
    genuine : scores from same-subject (legitimate) comparisons.
    impostor : scores from different-subject (attack) comparisons.

    Returns
    -------
    (eer, threshold)
    """
    genuine = np.asarray(genuine, dtype=float)
    impostor = np.asarray(impostor, dtype=float)
    if genuine.size == 0 or impostor.size == 0:
        return float("nan"), float("nan")

    # Sweep every candidate threshold and find where FAR and FRR cross.
    thresholds = np.unique(np.concatenate([genuine, impostor]))
    best_gap = np.inf
    best_eer, best_thr = 1.0, float(thresholds[0])
    for thr in thresholds:
        far = float(np.mean(impostor >= thr))   # impostors wrongly accepted
        frr = float(np.mean(genuine < thr))     # genuine wrongly rejected
        gap = abs(far - frr)
        if gap < best_gap:
            best_gap = gap
            best_eer = (far + frr) / 2.0
            best_thr = float(thr)
    return float(best_eer), best_thr
