"""Evaluate the toy model against the fixed synthetic baseline."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "model" / "toy_impression_generator.onnx"
DATASET = ROOT / "data" / "evaluation.csv"
BASELINE = ROOT / "artifacts" / "baseline-metrics.json"
VOCAB = ["<START>", "NO", "ACUTE", "FINDING", "LEFT", "RIGHT", "OPACITY", "<END>"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def generate(session: ort.InferenceSession, context: np.ndarray) -> str:
    previous = np.zeros((1, len(VOCAB)), dtype=np.float32)
    previous[0, 0] = 1.0
    generated = []
    for _ in range(6):
        logits = session.run(None, {"context": context, "previous_token": previous})[0]
        token_id = int(np.argmax(logits[0]))
        token = VOCAB[token_id]
        if token == "<END>":
            break
        generated.append(token)
        previous.fill(0.0)
        previous[0, token_id] = 1.0
    return " ".join(generated)


def evaluate() -> dict:
    session = ort.InferenceSession(str(MODEL), providers=["CPUExecutionProvider"])
    results = []
    with DATASET.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            context = np.array([[
                float(row["opacity"]),
                float(row["left"]),
                float(row["right"]),
                float(row["confidence"]),
            ]], dtype=np.float32)
            actual = generate(session, context)
            expected = row["expected_text"]
            results.append({
                "case_id": row["case_id"],
                "expected": expected,
                "actual": actual,
                "exact_match": actual == expected,
            })
    matches = sum(result["exact_match"] for result in results)
    return {
        "schema_version": 1,
        "model": "model/toy_impression_generator.onnx",
        "model_sha256": sha256(MODEL),
        "dataset": "data/evaluation.csv",
        "sample_count": len(results),
        "exact_match_count": matches,
        "exact_sequence_accuracy": matches / len(results),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="compare with the committed baseline")
    parser.add_argument("--write-baseline", action="store_true", help="replace the baseline result")
    args = parser.parse_args()
    result = evaluate()

    if args.write_baseline:
        BASELINE.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote baseline: {BASELINE}")
    elif args.check:
        expected = json.loads(BASELINE.read_text(encoding="utf-8"))
        if result != expected:
            print(json.dumps(result, indent=2))
            print("Evaluation does not match the committed baseline.")
            return 1
        print("Evaluation matches the committed baseline.")
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
