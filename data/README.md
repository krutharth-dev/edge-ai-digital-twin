# Data Management

**Status:** Local dataset directories are planned; full datasets are not stored in Git.

## Principles

- Raw recordings are immutable.
- Every recording has a run ID, label, timestamps, units, configuration, and hardware/firmware provenance.
- Derived data can be regenerated from raw data and versioned code/configuration.
- Training, validation, and test sets are assigned by complete run.
- Exclusions are documented rather than silently deleted.
- Personal, sensitive, licensed, or very large third-party data is not committed.

See [the data-collection protocol](../docs/DATA_COLLECTION_PROTOCOL.md).

## Suggested Local Layout

```text
data/
├── README.md
├── raw/          # Immutable local recordings; ignored by Git
├── processed/    # Reproducible derived windows/features; ignored by Git
├── manifests/    # Small metadata/split manifests suitable for review
└── examples/     # Optional small de-identified samples approved by the team
```

Do not create a public example until its units, label, provenance, license, and absence of secrets/private data have been reviewed.
