# Synthetic Medical AI Change-Control Demo

This repository is a small, reproducible fixture for demonstrating AI/ML bill
of materials generation and model change controls with ESL SBOMator.

It contains a real ONNX autoregressive token generator. Given four synthetic
numeric findings, the model generates one of three short toy impressions:

- `NO ACUTE FINDING`
- `LEFT OPACITY`
- `RIGHT OPACITY`

## Safety statement

This is **not a medical device**, is **not clinically validated**, and must not
be used for diagnosis, treatment, patient care, or clinical decision support.
The model is handcrafted rather than trained, and all evaluation inputs are
synthetic. Its only purpose is software supply-chain and change-control testing.

## Contents

- `model/toy_impression_generator.onnx` — generated ONNX model artifact
- `model/model-card.md` — intended use, limitations, inputs, and outputs
- `model/generate_model.py` — deterministic model generation source
- `data/evaluation.csv` — fixed synthetic evaluation set
- `scripts/evaluate.py` — ONNX Runtime evaluator
- `artifacts/baseline-metrics.json` — checked-in expected evaluation result

## Reproduce

Python 3.13 is used for the reference environment.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python model\generate_model.py
.venv\Scripts\python scripts\evaluate.py --check
```

The generator validates the ONNX graph before writing it. The evaluator checks
the model against the fixed data and compares the complete result, including
the model SHA-256, with the committed baseline.

## Planned evidence bundle

This fixture will be used to produce a CycloneDX 1.7 AI/ML BOM, conventional
vulnerability VEX, a model-change assessment, and a deterministic rebenchmark
trigger report. Those generated artifacts are intentionally not part of this
preparation step.

## License

The code, synthetic data, generated model, and documentation are licensed under
the MIT License. See `LICENSE`.
