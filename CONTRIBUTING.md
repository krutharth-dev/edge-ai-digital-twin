# Contributing to Edge-AI Digital Twin

Thank you for your interest in improving this project. Contributions to the documentation, system design, firmware, data pipeline, machine-learning workflow, dashboard, and testing are welcome.

## Before You Start

- Search existing issues and pull requests to avoid duplicate work.
- Open an issue before a substantial change so the approach can be discussed.
- Use the security policy for vulnerabilities; do not report them publicly.
- Keep claims accurate: features that have not been implemented or validated must be described as planned work.

## Development Workflow

1. Fork the repository and create a focused branch from `main`.
2. Make one logically related change at a time.
3. Follow the architecture, naming, and setup guidance in the README.
4. Add or update documentation and tests relevant to your change.
5. Commit with a short, descriptive message.
6. Open a pull request and complete the checklist.

## Project Guidelines

- Separate ESP32 firmware, Raspberry Pi services, model-training code, dashboard code, and documentation clearly.
- Never commit credentials, Wi-Fi passwords, API keys, raw personal data, or generated secrets.
- Document hardware assumptions, pin assignments, units, sampling rates, dependencies, and reproducible setup steps.
- For machine-learning changes, describe the dataset, preprocessing, evaluation method, metrics, and limitations.
- Treat alert thresholds and maintenance recommendations as prototype outputs unless they have been validated.
- Follow electrical and rotating-equipment safety guidance in the README.

## Pull Request Checklist

Before submitting, confirm that:

- The change is scoped and clearly explained.
- Relevant code, documentation, diagrams, and configuration agree with one another.
- Tests or manual validation steps are included.
- No generated build artefacts, secrets, or unrelated files are committed.
- New dependencies are necessary and documented.
- The change follows the Code of Conduct.

By contributing, you agree that your contribution is licensed under the repository's MIT License.
