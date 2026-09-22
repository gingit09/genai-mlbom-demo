"""Validate the complete checked-in demonstration evidence bundle."""

import hashlib
import json
from pathlib import Path

from cyclonedx.schema import SchemaVersion
from cyclonedx.validation.json import JsonStrictValidator
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = "model/toy_impression_generator.onnx"
CYCLONEDX_DOCUMENTS = (
    "artifacts/baseline/device-sbom.cdx.json",
    "artifacts/baseline/device-sbom.cdx_VEX.json",
    "artifacts/current/device-sbom.cdx.json",
    "artifacts/current/device-sbom.cdx_VEX.json",
)
SCHEMA_DOCUMENTS = (
    ("changes/model-change-declaration.json", "schemas/model-change-declaration.schema.json"),
    ("artifacts/model-change-assessment.json", "schemas/model-change-assessment.schema.json"),
    ("artifacts/rebenchmark-trigger-report.json", "schemas/rebenchmark-trigger-report.schema.json"),
)


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def model_component(sbom: dict) -> dict:
    models = [
        component
        for component in sbom.get("components", [])
        if component.get("type") == "machine-learning-model"
        and any(
            prop.get("name") == "SrcFile" and prop.get("value") == MODEL_PATH
            for prop in component.get("properties", [])
        )
    ]
    assert len(models) == 1, f"Expected one {MODEL_PATH} component, found {len(models)}"
    return models[0]


def component_sha256(component: dict) -> str:
    matches = [item["content"].lower() for item in component["hashes"] if item["alg"] == "SHA-256"]
    assert len(matches) == 1, "Model component must contain exactly one SHA-256"
    return matches[0]


def validate_cyclonedx() -> None:
    for relative_path in CYCLONEDX_DOCUMENTS:
        path = ROOT / relative_path
        document = json.loads(path.read_text(encoding="utf-8"))
        version = SchemaVersion.from_version(document["specVersion"])
        errors = list(JsonStrictValidator(version).validate_str(path.read_text(encoding="utf-8"), all_errors=True) or [])
        assert not errors, f"{relative_path}: {errors}"


def validate_project_schemas() -> None:
    for document_path, schema_path in SCHEMA_DOCUMENTS:
        schema = load(schema_path)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(load(document_path))


def validate_cross_references() -> None:
    baseline_sbom = load("artifacts/baseline/device-sbom.cdx.json")
    current_sbom = load("artifacts/current/device-sbom.cdx.json")
    baseline_model = model_component(baseline_sbom)
    current_model = model_component(current_sbom)
    baseline_hash = component_sha256(baseline_model)
    current_hash = component_sha256(current_model)
    declaration = load("changes/model-change-declaration.json")
    assessment = load("artifacts/model-change-assessment.json")
    trigger = load("artifacts/rebenchmark-trigger-report.json")
    baseline_metrics = load("artifacts/baseline/model-metrics.json")
    current_metrics = load("artifacts/current/model-metrics.json")

    assert declaration["from_version"] == baseline_model["version"] == assessment["baseline"]["version"]
    assert declaration["to_version"] == current_model["version"] == assessment["current"]["version"]
    assert baseline_hash == assessment["baseline"]["sha256"] == baseline_metrics["model_sha256"]
    assert current_hash == assessment["current"]["sha256"] == current_metrics["model_sha256"]
    assert current_hash == sha256(ROOT / MODEL_PATH)
    assert baseline_hash != current_hash
    assert assessment["declaration_consistent"] is True
    assert declaration["change_id"] == assessment["change_id"] == trigger["change_id"]
    assert trigger["required"] is True

    comparable_fields = ("dataset", "sample_count", "exact_match_count", "exact_sequence_accuracy", "results")
    assert all(baseline_metrics[field] == current_metrics[field] for field in comparable_fields)

    metadata = load("model/toy_impression_generator.onnx.metadata.json")
    assert metadata["version"] == current_model["version"]
    assert metadata["modelCard"] == current_model["modelCard"]

    for label, sbom in (("baseline", baseline_sbom), ("current", current_sbom)):
        for component in sbom["components"]:
            assert component.get("version"), f"{label}: component without version: {component.get('name')}"
            assert component.get("licenses"), f"{label}: component without license: {component.get('name')}"


def validate_checksums() -> None:
    for line in (ROOT / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        expected, relative_path = line.split("  ", 1)
        assert sha256(ROOT / relative_path) == expected, f"Checksum mismatch: {relative_path}"


def main() -> int:
    validate_cyclonedx()
    validate_project_schemas()
    validate_cross_references()
    validate_checksums()
    print("Validated 4 CycloneDX documents, 3 project schemas, cross-references, and checksums.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
