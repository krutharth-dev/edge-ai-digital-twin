# Machine-Learning Pipeline

**Status:** Planned scaffold; no trained or validated model is currently included.

## Objective

Classify safe controlled motor conditions using engineered sensor features. The initial baseline is Random Forest.

MVP:

`NORMAL | ABNORMAL`

Complete prototype target:

`NORMAL | IMBALANCE | INCREASED_LOAD | THERMAL_ABNORMALITY`

## Candidate Inputs

Vibration window features:

- RMS
- Standard deviation
- Peak and peak-to-peak
- Kurtosis
- Crest factor
- Dominant frequency
- FFT-band energy

Context features may include current, temperature, RPM, and changes from a run or speed-specific baseline.

## Required Workflow

1. Load only runs with valid labels and metadata.
2. Preserve run ID through every transformation.
3. Split by complete runs or sessions.
4. Fit learned preprocessing only on training runs.
5. Train a simple baseline.
6. Evaluate Random Forest first.
7. Compare Gradient Boosting or SVM only when useful.
8. Inspect per-class errors, false alarms, and failure cases.
9. Export model plus preprocessing/feature metadata.
10. Verify Raspberry Pi feature parity and latency.

## Evaluation

Report accuracy, macro-F1, per-class precision/recall, confusion matrix, false alarms, run/class distribution, split membership, and inference latency. Never report window-randomized performance as the primary result.

## Artifact Contract

A deployable model must have:

- Model/version identifier
- Ordered feature list
- Window and filtering configuration
- Label mapping
- Library/runtime versions
- Dataset/run manifest reference
- Training source commit
- Validation metrics and known limitations
- Integrity hash where practical

Joblib/pickle files must be treated as trusted-code artifacts and loaded only from a verified source.

## Planned Layout

```text
ai/
├── README.md
├── notebooks/          # Exploration; not the only source of production logic
├── feature-extraction/ # Reusable deterministic functions
├── training/           # Reproducible training/evaluation entry points
└── models/             # Metadata only in Git unless artifact policy is approved
```

Deep learning and RUL are optional later investigations, not requirements for the core project.
