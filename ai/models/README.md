# Model Artifacts

Trained model binaries are ignored by default.

For each locally stored model, keep a small metadata record containing:

- Model ID and filename
- SHA-256 hash
- Training source commit
- Dataset/run manifest and split
- Ordered feature schema and preprocessing version
- Label mapping
- Python and library versions
- Evaluation metrics and limitations
- Raspberry Pi compatibility/latency check

Do not commit Joblib, pickle, ONNX, or TensorFlow Lite artifacts without explicit team approval and a clear size, license, provenance, and security review.
