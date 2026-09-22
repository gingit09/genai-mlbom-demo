"""Generate deterministic model-change and rebenchmark evidence from two ML-BOMs."""

import argparse
import json
from pathlib import Path


SUITES_BY_BEHAVIOR_CLASS = {
    "model_weights": {"baseline-performance", "safety-regression"},
    "safety_guardrails": {"safety-regression", "adversarial-safety"},
    "clinical_content": {"baseline-performance", "clinical-content-safety"},
    "output_format": {"output-contract"},
    "input_contract": {"input-contract", "baseline-performance"},
    "training_data": {"baseline-performance", "bias-and-fairness", "safety-regression"},
    "unknown": {"full-benchmark-suite"},
}


def _properties(component: dict) -> dict[str, str]:
    return {
        item["name"]: str(item.get("value", ""))
        for item in component.get("properties", [])
        if isinstance(item, dict) and item.get("name")
    }


def _model(sbom: dict, path: str) -> dict:
    matches = [
        component for component in sbom.get("components", [])
        if component.get("type") == "machine-learning-model"
        and _properties(component).get("SrcFile") == path
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one model component for {path!r}; found {len(matches)}")
    component = matches[0]
    hashes = {
        item.get("alg"): str(item.get("content", "")).lower()
        for item in component.get("hashes", []) if isinstance(item, dict)
    }
    sha256 = hashes.get("SHA-256", "")
    if len(sha256) != 64:
        raise ValueError(f"Model component for {path!r} has no valid SHA-256")
    return {
        "bom_ref": str(component.get("bom-ref") or ""),
        "version": str(component.get("version") or ""),
        "sha256": sha256,
        "model_card": component.get("modelCard"),
    }


def generate_evidence(baseline_sbom: dict, current_sbom: dict, declaration: dict) -> tuple[dict, dict]:
    path = declaration["model_path"]
    baseline = _model(baseline_sbom, path)
    current = _model(current_sbom, path)
    observed = []
    if baseline["sha256"] != current["sha256"]:
        observed.append("content_hash")
    if baseline["version"] != current["version"]:
        observed.append("version")
    if baseline["model_card"] != current["model_card"]:
        observed.append("model_card")

    consistent = (
        baseline["version"] == declaration["from_version"]
        and current["version"] == declaration["to_version"]
        and bool(observed)
    )
    assessment = {
        "schema_version": 1,
        "change_id": declaration["change_id"],
        "model_path": path,
        "baseline": {key: baseline[key] for key in ("bom_ref", "version", "sha256")},
        "current": {key: current[key] for key in ("bom_ref", "version", "sha256")},
        "observed_changes": observed,
        "declared_behavior_classes": sorted(declaration["behavior_classes"]),
        "declaration_consistent": consistent,
    }

    reason_codes = []
    suites = set()
    if "content_hash" in observed:
        reason_codes.append("model-content-hash-changed")
        suites.add("model-integrity")
    if "version" in observed:
        reason_codes.append("model-version-changed")
    if not consistent:
        reason_codes.append("change-declaration-inconsistent")
        suites.add("full-benchmark-suite")
    for behavior_class in declaration["behavior_classes"]:
        suites.update(SUITES_BY_BEHAVIOR_CLASS[behavior_class])

    trigger = {
        "schema_version": 1,
        "change_id": declaration["change_id"],
        "required": bool(reason_codes),
        "reason_codes": sorted(reason_codes),
        "required_suites": sorted(suites),
    }
    return assessment, trigger


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--declaration", type=Path, required=True)
    parser.add_argument("--assessment-output", type=Path, required=True)
    parser.add_argument("--trigger-output", type=Path, required=True)
    args = parser.parse_args()
    assessment, trigger = generate_evidence(
        _load(args.baseline), _load(args.current), _load(args.declaration)
    )
    _write(args.assessment_output, assessment)
    _write(args.trigger_output, trigger)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
