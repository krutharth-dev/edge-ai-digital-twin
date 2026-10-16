# Processed Data

Processed windows and feature tables belong here locally and are ignored by Git.

Every derived file should be reproducible from identified raw run IDs, a source commit, and versioned preprocessing/feature configuration. Preserve run ID and split membership in the output.

Keep fitted preprocessing parameters and feature ordering alongside each output. **Never** calculate a dataset-wide normalization before assigning run-level training, validation and test splits; that leaks information into evaluation. See the [ML guide](../../ai/README.md).

