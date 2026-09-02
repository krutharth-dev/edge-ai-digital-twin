# Security Policy

## Supported Version

This project is under active development. Security fixes are applied only to the latest code on the `main` branch. Older commits, local experiments, and unofficial forks are not supported.

## Reporting a Vulnerability

Do **not** disclose a suspected vulnerability in a public issue, discussion, pull request, dataset, or log.

Use GitHub private vulnerability reporting from the repository's **Security** tab when available. Otherwise, contact the maintainer privately through the [maintainer's GitHub profile](https://github.com/krutharth-dev) before sharing technical details.

Include, where possible:

- Affected component, branch, commit, and configuration
- Impact and realistic attack or failure scenario
- Safe reproduction steps or a minimal proof of concept
- Relevant logs with credentials, network details, and personal data removed
- Suggested mitigation

The maintainer aims to acknowledge a complete report within seven days and coordinate investigation, remediation, and responsible disclosure.

## Secrets and Configuration

Never commit:

- Wi-Fi SSIDs or passwords
- MQTT usernames, passwords, certificates, or broker tokens
- SSH keys, API keys, private keys, or remote-access credentials
- Personally identifying experimental or contributor data
- Real deployment addresses or unrestricted firewall rules

Use `.env.example` for documented placeholders and keep the real `.env` local. Rotate any credential immediately if it is accidentally committed; removing it from the latest file does not remove it from Git history.

## Local-Network Security

The core system is designed for a trusted local network, but local does not mean automatically secure.

- Do not expose Mosquitto, Streamlit, Node-RED, Grafana, SSH, or database ports to the public internet.
- Bind services only to the interfaces required for the experiment.
- Use broker authentication and authorization when devices other than the project components can access the network.
- Restrict publish/subscribe permissions by topic where practical.
- Validate payload type, size, schema version, asset ID, timestamp, and numeric ranges before storage or inference.
- Treat unexpected or stale telemetry as invalid rather than silently updating the Digital Twin.
- Avoid dashboard controls that can energize or alter the motor unless a separately reviewed safety mechanism exists.

## Data and Model Security

- Treat imported datasets and model files as untrusted inputs.
- Do not load unknown pickle or Joblib artifacts; these formats can execute code during deserialization.
- Record the expected model hash, feature schema, and source commit for deployed artifacts.
- Sanitize file paths and reject oversized or malformed uploads.
- Remove credentials and private metadata before sharing logs, screenshots, or datasets.

## Dependency Security

Use a virtual environment, review new dependencies, keep lock or version records once the prototype environment stabilizes, and apply security updates after testing them against the Raspberry Pi environment.
