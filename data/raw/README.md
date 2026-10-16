# Raw Data

Raw experimental recordings belong here locally and are ignored by Git.

Do not modify raw files after collection. Record run metadata, configuration, firmware commit, and a checksum where practical. If a run is invalid, preserve it locally and mark the reason in the manifest rather than rewriting it.

Store each experiment under a unique run ID. Keep the original sensor units and acquisition timestamps, including a time-sync flag where needed. Never patch readings in place or silently discard an interrupted run. See the [collection protocol](../../docs/DATA_COLLECTION_PROTOCOL.md).

