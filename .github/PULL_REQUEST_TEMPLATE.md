## Summary

Describe what this pull request changes, why it is needed, and which project milestone it supports.

## Related Issue

Closes #

## Affected Area

- [ ] Motor rig, wiring, or safety
- [ ] ESP32 firmware or sensors
- [ ] MQTT or Raspberry Pi services
- [ ] Dataset or storage
- [ ] Feature extraction or machine learning
- [ ] Digital Twin or health logic
- [ ] Dashboard or alerts
- [ ] Tests, documentation, or tooling

## Interfaces Changed

List changed pin assignments, units, sample rates, MQTT topics/payloads, data columns, model features, configuration keys, or Digital Twin fields. Write "None" if no interface changed.

## Change Type

- [ ] Documentation or project setup
- [ ] Implemented software or firmware
- [ ] Hardware integration
- [ ] Experimental protocol or measured results

## Validation Evidence

List the exact commands, tests, controlled experiments, or manual checks performed and their results. For hardware work, describe only safe, repeatable tests. If the change is documentation-only, say so; do not claim that the scaffold tests validate physical hardware.

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
- [ ] This change preserves local Raspberry Pi inference for the core system.
- [ ] Any physical test follows the repository safety plan.
- [ ] I agree to follow the Code of Conduct.
