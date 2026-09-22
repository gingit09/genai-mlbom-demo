import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "validators" / "generate_change_evidence.py"
SPEC = importlib.util.spec_from_file_location("generate_change_evidence", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _sbom(version: str, digest: str, task: str = "text-generation") -> dict:
    return {
        "components": [{
            "type": "machine-learning-model",
            "bom-ref": f"model:model/toy.onnx@{version}",
            "name": "toy.onnx",
            "version": version,
            "hashes": [{"alg": "SHA-256", "content": digest}],
            "properties": [{"name": "SrcFile", "value": "model/toy.onnx"}],
            "modelCard": {"modelParameters": {"task": task}},
        }],
    }


def _declaration() -> dict:
    return {
        "change_id": "change-1",
        "model_path": "model/toy.onnx",
        "from_version": "1.0.0",
        "to_version": "1.1.0",
        "behavior_classes": ["model_weights"],
    }


def test_hash_and_version_change_trigger_targeted_rebenchmarking():
    assessment, trigger = MODULE.generate_evidence(
        _sbom("1.0.0", "a" * 64),
        _sbom("1.1.0", "b" * 64),
        _declaration(),
    )

    assert assessment["observed_changes"] == ["content_hash", "version"]
    assert assessment["declaration_consistent"] is True
    assert trigger == {
        "schema_version": 1,
        "change_id": "change-1",
        "required": True,
        "reason_codes": ["model-content-hash-changed", "model-version-changed"],
        "required_suites": ["baseline-performance", "model-integrity", "safety-regression"],
    }


def test_inconsistent_declaration_requires_full_suite():
    declaration = _declaration()
    declaration["from_version"] = "wrong"

    assessment, trigger = MODULE.generate_evidence(
        _sbom("1.0.0", "a" * 64),
        _sbom("1.1.0", "b" * 64),
        declaration,
    )

    assert assessment["declaration_consistent"] is False
    assert "change-declaration-inconsistent" in trigger["reason_codes"]
    assert "full-benchmark-suite" in trigger["required_suites"]


def test_unchanged_model_with_false_version_claim_is_not_cleared():
    assessment, trigger = MODULE.generate_evidence(
        _sbom("1.0.0", "a" * 64),
        _sbom("1.0.0", "a" * 64),
        _declaration(),
    )

    assert assessment["observed_changes"] == []
    assert assessment["declaration_consistent"] is False
    assert trigger["required"] is True
    assert trigger["required_suites"] == [
        "baseline-performance",
        "full-benchmark-suite",
        "safety-regression",
    ]
