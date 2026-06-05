# Heartbeat ID — ECG Biometric Identification

Identify a person from their heartbeat. This repository is a clean, documented
reference implementation of an **ECG-based biometric system**: it takes a raw
electrocardiogram (ECG) signal, finds the heartbeats, and recognises *whose*
heart produced them.

It implements the full, literature-standard pipeline end-to-end and ships a
**synthetic ECG generator** so you can run and test everything immediately —
no clinical database or special hardware required.

```
 raw ECG ─▶ preprocess ─▶ R-peak detection ─▶ beat segmentation
        ─▶ feature extraction ─▶ enrol / identify / verify
```

The scientific basis (with full citations) is in
[`docs/RESEARCH.md`](docs/RESEARCH.md).

---

## How it works

| Stage | Module | Method |
|-------|--------|--------|
| Preprocessing | `heartbeat_id/preprocessing.py` | Butterworth band-pass (0.5–40 Hz) + 50 Hz notch |
| R-peak detection | `heartbeat_id/qrs_detection.py` | **Pan–Tompkins (1985)** with adaptive thresholds |
| Segmentation | `heartbeat_id/segmentation.py` | R-aligned fixed windows, z-score, outlier rejection |
| Features | `heartbeat_id/features.py` | Hybrid: fiducial (PQRST) + autocorrelation/DCT + raw beat |
| Matching | `heartbeat_id/biometric.py` | Cosine template **and** RBF-SVM, with multi-beat fusion |
| Dummy data | `heartbeat_id/ecg_synth.py` | **ECGSYN** dynamical model (McSharry et al., 2003) |

Two biometric tasks are supported:

* **Identification (1:N)** — `HeartbeatID.identify(ecg)` → "who is this?"
* **Verification (1:1)** — `HeartbeatID.verification_score(ecg, claimed_id)` →
  "are you who you claim?", evaluated by **Equal Error Rate (EER)**.

## Quick start

```bash
# 1. install dependencies
pip install -r requirements.txt

# 2. run the full demo on synthetic data (generates figures + metrics)
python scripts/run_demo.py --subjects 10

# 3. run the tests
pytest -q
```

### Minimal API example

```python
from heartbeat_id import HeartbeatID
from heartbeat_id.ecg_synth import generate_population, generate_subject_ecg

fs = 250
profiles = generate_population(5, seed=42)

# one enrolment + one (independent) test recording per subject
enroll, test = [], []
for p in profiles:
    _, e = generate_subject_ecg(p, duration_s=30, fs=fs, seed=1000 + p.subject_id)
    _, t = generate_subject_ecg(p, duration_s=15, fs=fs, seed=5000 + p.subject_id)
    enroll.append((p.subject_id, e)); test.append((p.subject_id, t))

system = HeartbeatID(fs=fs).fit(enroll)

label, ecg = test[0]
result = system.identify(ecg)          # 1:N identification
print(result["name"], result["confidence"])
```

## Results on the synthetic demo (10 subjects)

| Metric | Value |
|--------|-------|
| Identification accuracy (SVM, multi-beat) | **100 %** |
| Identification accuracy (template, multi-beat) | **100 %** |
| Single-beat identification accuracy (SVM) | ~99 % |
| Verification Equal Error Rate | **~0 %** |

Generated figures (in `figures/`):

* `01_subject_signals.png` — different subjects look different.
* `02_qrs_detection.png` — Pan–Tompkins stages and detected R peaks.
* `03_beat_templates.png` — within-subject beats cluster around a per-subject template.
* `04_confusion_matrix.png` — identification confusion matrix.
* `05_verification_scores.png` — genuine vs impostor score distributions + EER.

> ⚠️ **These numbers reflect synthetic, cleanly separable subjects** and
> demonstrate that the pipeline mechanics are correct — not real-world
> performance. On real ECG, intra-subject variability across sessions, exercise
> and time pushes equal error rates to a few percent. See the caveat in
> [`docs/RESEARCH.md`](docs/RESEARCH.md) and the listed public datasets
> (ECG-ID, MIT-BIH, PTB-XL) to evaluate on real data.

## Using your own / real ECG

The system is data-agnostic. Provide `(label, signal)` pairs at the right
sampling rate:

```python
system = HeartbeatID(fs=YOUR_FS).fit([(subject_id, ecg_array), ...])
```

Public benchmark databases are available from
[PhysioNet](https://physionet.org).

## Project layout

```
heartbeat-id/
├── heartbeat_id/        # the library
│   ├── ecg_synth.py     # ECGSYN synthetic data generator
│   ├── preprocessing.py # filtering / denoising
│   ├── qrs_detection.py # Pan-Tompkins R-peak detection
│   ├── segmentation.py  # beat extraction + normalisation
│   ├── features.py      # fiducial + AC/DCT feature extraction
│   └── biometric.py     # enrol / identify / verify + metrics
├── scripts/run_demo.py  # end-to-end demonstration
├── tests/test_pipeline.py
├── docs/                # RESEARCH.md (literature review) + references.bib
├── data/                # generated dummy dataset (.npz)
├── figures/             # generated plots
├── requirements.txt
└── LICENSE
```

## Ethics & scope

ECG is sensitive health data and a biometric identifier. This project is a
**research / educational reference** that runs on synthetic data by default. If
you apply it to real recordings, obtain informed consent, comply with applicable
data-protection law (e.g. GDPR/HIPAA), and remember that an ECG can also reveal
medical conditions — handle it accordingly.

## License

Code is released under the MIT License (see [`LICENSE`](LICENSE)). The cited
research papers remain under their respective publishers' copyright and are
**not** redistributed here; see the note in `docs/RESEARCH.md`.
