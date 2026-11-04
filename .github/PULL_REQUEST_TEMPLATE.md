<!-- Open a draft PR until implementation and tests are complete. Use Ready for review afterward. See docs/PR_GUIDE.md. -->

## Summary

Describe what this pull request changes, why it is needed, and which project milestone it supports.

## Related Issue

Issue link / number (or None):

## Affected Area

- [ ] Motor rig, wiring, or safety
- [ ] ESP32 firmware or sensors
- [ ] MQTT or Mac-hosted backend services
- [ ] Dataset or storage
- [ ] Feature extraction or machine learning
- [ ] Digital Twin or health logic
- [ ] Dashboard or alerts
- [ ] Tests, documentation, or tooling

## Interfaces Changed

List changed pin assignments, units, sample rates, MQTT topics/payloads, data columns, model features, configuration keys, or Digital Twin fields. Write "None" if no interface changed.

## Validation Evidence

List the commands, tests, controlled experiments, or manual checks performed and their results. For hardware work, describe only safe, repeatable tests.

## Data and ML Integrity

If applicable, document the dataset/run IDs, labels, preprocessing, run-based split, metrics, limitations, model artifact, and training-to-inference compatibility.

## Safety Review

If hardware or abnormal-condition testing changed, identify the guard, power isolation, fuse/switch, rated limits, stop conditions, and supervision used.

## Checklist

- [ ] I kept this pull request focused on one logical change.
- [ ] I reviewed my own changes and removed debug credentials and private data.
- [ ] I updated relevant documentation, tests, schemas, and examples.
- [ ] I did not commit raw datasets, generated model binaries, local databases, or unrelated outputs.
- [ ] Adjacent windows from one experimental run are not split across training and test data.
- [ ] Unimplemented features and unmeasured results are clearly labelled as planned.
- [ ] This change preserves local Mac-hosted inference and the MQTT contract.
- [ ] Any physical test follows the repository safety plan.
- [ ] I agree to follow the Code of Conduct.
