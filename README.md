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
- `artifacts/baseline/` - version 1.0.0 SBOM, VEX, and model metrics
- `artifacts/current/` - version 1.1.0 SBOM, VEX, and model metrics
- `changes/model-change-declaration.json` - supplier's machine-readable change declaration
- `artifacts/model-change-assessment.json` - observed BOM difference and declaration check
- `artifacts/rebenchmark-trigger-report.json` - deterministic rebenchmark decision and scope
- `validators/` - evidence generator and complete bundle validator
- `WALKTHROUGH.md` and `walkthrough.pdf` - reviewer-oriented explanation of the evidence flow
- `SHA256SUMS` - integrity hashes for the distributable evidence files

## Reproduce

Python 3.13 is used for the reference environment.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python model\generate_model.py
.venv\Scripts\python scripts\evaluate.py --check
.venv\Scripts\python -m pytest
.venv\Scripts\python validators\validate_artifacts.py
```

The generator validates the ONNX graph before writing it. The evaluator checks
the model against the fixed data and compares the complete result, including
the model SHA-256, with the committed baseline.

## Reproduce the evidence bundle

The checked-in baseline represents model `1.0.0`; the current artifact represents
model `1.1.0`. Check out the corresponding local tag before each SBOM generation:

```powershell
python <SBOMATOR>\cli-only\esl_sbomator_cli.py <DEMO_REPOSITORY> `
  --ai-sbom --ai-check-level maximum --cyclonedx-version 1.7 `
  --skip-db-update --no-cve --no-grype --no-report `
  --manufacturer "E.S.L SOFTWARE LAB LTD" --product-version <MODEL_VERSION> `
  -o <OUTPUT_PATH>
```

Generate the model-change evidence after both SBOMs exist:

```powershell
.venv\Scripts\python validators\generate_change_evidence.py `
  --baseline artifacts\baseline\device-sbom.cdx.json `
  --current artifacts\current\device-sbom.cdx.json `
  --declaration changes\model-change-declaration.json `
  --assessment-output artifacts\model-change-assessment.json `
  --trigger-output artifacts\rebenchmark-trigger-report.json
```

The SBOMs use CycloneDX 1.7. SBOMator's conventional vulnerability VEX output
uses CycloneDX 1.6. The bundle validator performs strict schema validation for
each document's declared CycloneDX version and verifies the model hashes,
versions, model card, evaluation results, evidence cross-references, and
`SHA256SUMS`.

CycloneDX `serialNumber` and `metadata.timestamp` values are intentionally
different on every generation. Remove those two fields before byte-level SBOM
comparisons. The generation command, tool revisions, and normalization list are
recorded in `artifacts/generation-manifest.json`.

## License

The code, synthetic data, generated model, and documentation are licensed under
the MIT License. See `LICENSE`.
