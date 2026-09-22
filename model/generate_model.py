"""Build the deterministic toy autoregressive ONNX model."""

from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "model" / "toy_impression_generator.onnx"
VOCAB_SIZE = 8
CONTEXT_SIZE = 4


def build_model() -> onnx.ModelProto:
    weights = np.zeros((CONTEXT_SIZE + VOCAB_SIZE, VOCAB_SIZE), dtype=np.float32)

    # Context rows: opacity, left, right, confidence. Context only selects the
    # first generated token; subsequent transitions are token-driven.
    weights[0, 1] = -6.0  # opacity suppresses the normal-path token NO
    weights[1, 4] = 8.0   # left -> LEFT
    weights[2, 5] = 8.0   # right -> RIGHT

    token_offset = CONTEXT_SIZE
    weights[token_offset + 0, 1] = 3.0   # START -> NO by default
    weights[token_offset + 1, 2] = 10.0  # NO -> ACUTE
    weights[token_offset + 2, 3] = 10.0  # ACUTE -> FINDING
    weights[token_offset + 3, 7] = 10.0  # FINDING -> END
    weights[token_offset + 4, 6] = 10.0  # LEFT -> OPACITY
    weights[token_offset + 5, 6] = 10.0  # RIGHT -> OPACITY
    weights[token_offset + 6, 7] = 10.0  # OPACITY -> END
    weights[token_offset + 7, 7] = 10.0  # END -> END

    bias = np.zeros((VOCAB_SIZE,), dtype=np.float32)
    graph = helper.make_graph(
        [
            helper.make_node("Concat", ["context", "previous_token"], ["features"], axis=1),
            helper.make_node("MatMul", ["features", "weights"], ["raw_logits"]),
            helper.make_node("Add", ["raw_logits", "bias"], ["logits"]),
        ],
        "toy-impression-generator",
        [
            helper.make_tensor_value_info("context", TensorProto.FLOAT, [1, CONTEXT_SIZE]),
            helper.make_tensor_value_info("previous_token", TensorProto.FLOAT, [1, VOCAB_SIZE]),
        ],
        [helper.make_tensor_value_info("logits", TensorProto.FLOAT, [1, VOCAB_SIZE])],
        [numpy_helper.from_array(weights, "weights"), numpy_helper.from_array(bias, "bias")],
    )
    model = helper.make_model(
        graph,
        producer_name="E.S.L SOFTWARE LAB LTD",
        producer_version="1.0.0",
        domain="com.eswlab.demo",
        model_version=1,
        opset_imports=[helper.make_opsetid("", 13)],
    )
    model.ir_version = 8
    metadata = {
        "model_name": "Toy Impression Generator",
        "model_version": "1.0.0",
        "license": "MIT",
        "intended_use": "Non-clinical AI/ML supply-chain and change-control demonstration",
        "training_data": "None; handcrafted deterministic weights",
    }
    for key, value in metadata.items():
        entry = model.metadata_props.add()
        entry.key = key
        entry.value = value
    onnx.checker.check_model(model, full_check=True)
    return model


if __name__ == "__main__":
    model = build_model()
    onnx.save_model(model, OUTPUT)
    print(f"Wrote validated ONNX model: {OUTPUT}")
