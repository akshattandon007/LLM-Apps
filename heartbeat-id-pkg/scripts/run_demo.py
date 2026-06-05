#!/usr/bin/env python3
"""
run_demo.py
===========

End-to-end demonstration of the Heartbeat-ID system on synthetic dummy data.

It will:
  1. synthesise a population of distinct subjects (ECGSYN model);
  2. create two independent recordings per subject (enrol + test);
  3. enrol the subjects and run identification (1:N) and verification (1:1);
  4. report accuracy and Equal Error Rate;
  5. save illustrative figures to ``figures/`` and the dataset to ``data/``.

Usage
-----
    python scripts/run_demo.py --subjects 10 --enroll-seconds 30 --test-seconds 15

All randomness is seeded, so results are reproducible.
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

# Allow running the script directly from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from heartbeat_id.ecg_synth import generate_population, generate_subject_ecg
from heartbeat_id.preprocessing import preprocess
from heartbeat_id.qrs_detection import pan_tompkins_detect, heart_rate_bpm
from heartbeat_id.segmentation import segment_beats
from heartbeat_id.biometric import (
    HeartbeatID, identification_accuracy, equal_error_rate,
)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(HERE, "figures")
DATA_DIR = os.path.join(HERE, "data")


def build_recordings(n_subjects, enroll_s, test_s, fs, seed):
    profiles = generate_population(n_subjects, seed=seed)
    enroll, test = [], []
    for p in profiles:
        _, e = generate_subject_ecg(p, duration_s=enroll_s, fs=fs,
                                    seed=1000 + p.subject_id)
        _, t = generate_subject_ecg(p, duration_s=test_s, fs=fs,
                                    seed=5000 + p.subject_id)
        enroll.append((p.subject_id, e))
        test.append((p.subject_id, t))
    return profiles, enroll, test


def fig_subject_signals(profiles, enroll, fs):
    """Show that different subjects have visibly different ECG morphology."""
    k = min(4, len(profiles))
    fig, axes = plt.subplots(k, 1, figsize=(10, 2.0 * k), sharex=True)
    if k == 1:
        axes = [axes]
    secs = 4
    for ax, (label, ecg) in zip(axes, enroll[:k]):
        ax.plot(np.arange(secs * fs) / fs, ecg[:secs * fs], lw=0.9)
        ax.set_ylabel(f"{profiles[label].name}\n(mV)")
        ax.grid(alpha=0.3)
    axes[-1].set_xlabel("time (s)")
    axes[0].set_title("Synthetic ECG: distinct morphology per subject (ECGSYN)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "01_subject_signals.png"), dpi=130)
    plt.close(fig)


def fig_qrs_detection(enroll, fs):
    """Visualise the Pan-Tompkins detection on one subject."""
    label, ecg = enroll[0]
    clean = preprocess(ecg, fs)
    rpeaks, stages = pan_tompkins_detect(clean, fs, return_stages=True)
    secs = 6
    n = secs * fs
    t = np.arange(n) / fs
    fig, axes = plt.subplots(3, 1, figsize=(10, 6), sharex=True)
    axes[0].plot(t, clean[:n], lw=0.9)
    rp = rpeaks[rpeaks < n]
    axes[0].plot(rp / fs, clean[rp], "rv", ms=7, label="detected R peaks")
    axes[0].set_title(f"Pan-Tompkins R-peak detection "
                      f"(HR \u2248 {heart_rate_bpm(rpeaks, fs):.0f} bpm)")
    axes[0].legend(loc="upper right"); axes[0].grid(alpha=0.3)
    axes[0].set_ylabel("ECG (mV)")
    axes[1].plot(t, stages["squared"][:n], lw=0.8, color="tab:orange")
    axes[1].set_ylabel("squared\nderivative"); axes[1].grid(alpha=0.3)
    axes[2].plot(t, stages["integrated"][:n], lw=0.8, color="tab:green")
    axes[2].set_ylabel("MW\nintegrated"); axes[2].set_xlabel("time (s)")
    axes[2].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "02_qrs_detection.png"), dpi=130)
    plt.close(fig)


def fig_beat_templates(profiles, enroll, fs):
    """Overlay individual beats + mean template for a few subjects."""
    k = min(4, len(profiles))
    fig, axes = plt.subplots(1, k, figsize=(3.0 * k, 3.2), sharey=True)
    if k == 1:
        axes = [axes]
    for ax, (label, ecg) in zip(axes, enroll[:k]):
        clean = preprocess(ecg, fs)
        rpeaks = pan_tompkins_detect(clean, fs)
        beats = segment_beats(clean, rpeaks, fs)
        tt = (np.arange(beats.shape[1]) - 0.25 * fs) / fs * 1000
        for beat in beats[:40]:
            ax.plot(tt, beat, color="tab:blue", alpha=0.12, lw=0.7)
        ax.plot(tt, beats.mean(0), color="black", lw=1.8)
        ax.set_title(profiles[label].name, fontsize=10)
        ax.set_xlabel("ms from R"); ax.grid(alpha=0.3)
    axes[0].set_ylabel("normalised amplitude")
    fig.suptitle("R-aligned heartbeats and per-subject template", y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "03_beat_templates.png"),
                dpi=130, bbox_inches="tight")
    plt.close(fig)


def fig_confusion(system, test, profiles):
    labels = sorted(system.subjects)
    idx = {l: i for i, l in enumerate(labels)}
    M = np.zeros((len(labels), len(labels)), dtype=int)
    for true_label, ecg in test:
        pred = system.identify(ecg, method="svm")["label"]
        M[idx[true_label], idx[pred]] += 1
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(M, cmap="Blues")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels([profiles[l].name.replace("subject_", "S")
                        for l in labels], rotation=90, fontsize=8)
    ax.set_yticklabels([profiles[l].name.replace("subject_", "S")
                        for l in labels], fontsize=8)
    ax.set_xlabel("predicted"); ax.set_ylabel("true")
    ax.set_title("Identification confusion matrix (multi-beat fusion)")
    for i in range(len(labels)):
        for j in range(len(labels)):
            if M[i, j]:
                ax.text(j, i, M[i, j], ha="center", va="center",
                        color="white" if M[i, j] > M.max() / 2 else "black",
                        fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "04_confusion_matrix.png"), dpi=130)
    plt.close(fig)


def fig_verification(system, test):
    gen, imp = [], []
    for label, ecg in test:
        for claim in system.subjects:
            s = system.verification_score(ecg, claim)
            (gen if claim == label else imp).append(s)
    gen, imp = np.array(gen), np.array(imp)
    eer, thr = equal_error_rate(gen, imp)
    fig, ax = plt.subplots(figsize=(7, 4))
    bins = np.linspace(-1, 1, 41)
    ax.hist(imp, bins=bins, alpha=0.6, label="impostor", color="tab:red",
            density=True)
    ax.hist(gen, bins=bins, alpha=0.6, label="genuine", color="tab:green",
            density=True)
    ax.axvline(thr, color="black", ls="--",
               label=f"EER threshold = {thr:.2f}\nEER = {eer*100:.2f}%")
    ax.set_xlabel("match score (cosine similarity)")
    ax.set_ylabel("density")
    ax.set_title("Verification: genuine vs impostor score distributions")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "05_verification_scores.png"), dpi=130)
    plt.close(fig)
    return eer, thr


def main():
    ap = argparse.ArgumentParser(description="Heartbeat-ID demo")
    ap.add_argument("--subjects", type=int, default=10)
    ap.add_argument("--enroll-seconds", type=float, default=30.0)
    ap.add_argument("--test-seconds", type=float, default=15.0)
    ap.add_argument("--fs", type=int, default=250)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    os.makedirs(FIG_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    print(f"Synthesising {args.subjects} subjects (fs={args.fs} Hz)...")
    profiles, enroll, test = build_recordings(
        args.subjects, args.enroll_seconds, args.test_seconds,
        args.fs, args.seed)

    # Persist the dummy dataset so experiments are reproducible / inspectable.
    np.savez_compressed(
        os.path.join(DATA_DIR, "dummy_ecg_dataset.npz"),
        fs=args.fs,
        enroll_labels=np.array([l for l, _ in enroll]),
        enroll_signals=np.array([s for _, s in enroll], dtype=object),
        test_labels=np.array([l for l, _ in test]),
        test_signals=np.array([s for _, s in test], dtype=object),
        allow_pickle=True,
    )

    print("Enrolling subjects...")
    names = {p.subject_id: p.name for p in profiles}
    system = HeartbeatID(fs=args.fs).fit(enroll, names=names)

    print("Evaluating identification (1:N)...")
    svm_acc = identification_accuracy(system, test, method="svm")["accuracy"]
    tpl_acc = identification_accuracy(system, test, method="template")["accuracy"]

    print("Rendering figures...")
    fig_subject_signals(profiles, enroll, args.fs)
    fig_qrs_detection(enroll, args.fs)
    fig_beat_templates(profiles, enroll, args.fs)
    fig_confusion(system, test, profiles)
    eer, thr = fig_verification(system, test)

    print("\n" + "=" * 56)
    print("HEARTBEAT-ID RESULTS")
    print("=" * 56)
    print(f"  subjects enrolled            : {len(system.subjects)}")
    print(f"  identification acc (SVM)     : {svm_acc * 100:6.2f}%  "
          f"[multi-beat fusion]")
    print(f"  identification acc (template): {tpl_acc * 100:6.2f}%  "
          f"[multi-beat fusion]")
    print(f"  verification EER             : {eer * 100:6.2f}%  "
          f"(threshold {thr:.3f})")
    print("=" * 56)
    print(f"  figures saved to : {os.path.relpath(FIG_DIR, HERE)}/")
    print(f"  dataset saved to : "
          f"{os.path.relpath(DATA_DIR, HERE)}/dummy_ecg_dataset.npz")


if __name__ == "__main__":
    main()
