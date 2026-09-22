# AI/ML BOM Model-Change Demonstration

## Purpose and scope

This package demonstrates a machine-checkable model-change workflow for a
synthetic ONNX model. It is evidence that the proposed mechanism can be built
with current tools; it is not clinical evidence and is not an FDA submission
for a medical device.

The fixture contains no patient data. The model is handcrafted, is not
clinically validated, and must not be used for diagnosis, treatment, patient
care, or clinical decision support.

## Evidence flow

```text
model v1.0.0 + model card ──> baseline CycloneDX 1.7 AI/ML BOM
             │
             └──────────────> baseline deterministic evaluation

declared model-weight change
             │
             ▼
model v1.1.0 + model card ──> current CycloneDX 1.7 AI/ML BOM
             │
             └──────────────> current deterministic evaluation

baseline BOM + current BOM + declaration
             │
             └──────────────> change assessment ──> rebenchmark trigger
```

## Demonstrated change

| Field | Baseline | Current |
|---|---|---|
| Model version | `1.0.0` | `1.1.0` |
| ONNX SHA-256 | `17e341bde16199eea432a840f27f071cb30baa7a06314e1eea4427d2b52ea59c` | `fb30420e66ab9850a7d740b29bdc04f0c1bc92a325d71156b4f230aadb99e248` |
| Declared behavior class | — | `model_weights` |
| Evaluation result | 3/3 exact sequences | 3/3 exact sequences |

The content hash and semantic version changed while the documented output
contract remained stable on the fixed synthetic evaluation set. The generated
assessment confirms that the declaration matches the observed BOM difference.
The deterministic trigger requires `baseline-performance`, `model-integrity`,
and `safety-regression` suites.

## Review the artifacts

1. Compare the machine-learning-model component in
   `artifacts/baseline/device-sbom.cdx.json` and
   `artifacts/current/device-sbom.cdx.json`.
2. Review the supplier declaration in
   `changes/model-change-declaration.json`.
3. Review the observed change and declaration consistency result in
   `artifacts/model-change-assessment.json`.
4. Review the deterministic decision and required suites in
   `artifacts/rebenchmark-trigger-report.json`.
5. Review the complete generation provenance in
   `artifacts/generation-manifest.json`.
6. Run `python validators/validate_artifacts.py` to validate schemas, hashes,
   evaluation equivalence, evidence cross-references, and `SHA256SUMS`.

## Reproduce and verify

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python model\generate_model.py
.venv\Scripts\python scripts\evaluate.py --check
.venv\Scripts\python -m pytest -q
.venv\Scripts\python validators\validate_artifacts.py
```

The exact SBOMator generation command and tool revisions are recorded in
`artifacts/generation-manifest.json`. CycloneDX serial numbers and metadata
timestamps are unique per run; remove those fields before byte-level comparison.

## Format boundaries and limitations

- The AI/ML BOMs conform to CycloneDX 1.7 and include the model as a
  `machine-learning-model` component with a model card, version, supplier,
  license, and content hash.
- The conventional vulnerability VEX documents conform to CycloneDX 1.6 and
  contain no vulnerability statements because online vulnerability lookup was
  disabled for this deterministic fixture.
- The model-change declaration, assessment, and rebenchmark trigger use open
  project JSON Schemas. They are inspired by VEX's machine-readable
  component/status/analysis pattern but are not represented as CycloneDX VEX
  vulnerability statements.
- Stable output on three synthetic examples does not establish model safety,
  efficacy, generalization, or clinical performance.
