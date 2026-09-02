# Monitoring Dashboard

**Status:** Planned scaffold; dashboard code has not yet been committed.

## Version 1 Goal

Provide a clear live view of the operational Digital Twin without implying unsupported precision or industrial certification.

Minimum views:

- Connection and data-freshness status
- Live vibration, current, temperature, and RPM where available
- Units and last-updated timestamp
- Predicted state and confidence when valid
- `UNKNOWN / HEALTHY / WARNING / FAULT` state
- Transparent maintenance/warning message
- Historical sensor and state trends
- Alert/event history
- Model and feature version
- Clear unavailable or stale indication

## Technology

Streamlit or Node-RED is appropriate for the first working version. Grafana and 3D/Three.js visualization are optional after core validation.

## Design Rules

- Do not display fabricated demo numbers when telemetry is missing.
- Do not label the health score as Remaining Useful Life.
- Keep model confidence separate from rule-based health state.
- Show invalid, disconnected, or stale data visibly.
- Avoid motor-control buttons unless a separately reviewed safety design exists.
- Make the normal-to-abnormal-to-recovery sequence easy to demonstrate.

## Acceptance Evidence

The dashboard is ready when it reflects the same timestamped Digital Twin state, survives data interruptions without showing false health, and clearly displays the end-to-end demonstration transitions.
