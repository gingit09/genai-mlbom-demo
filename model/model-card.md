# Model Card: Toy Impression Generator

## Model details

- **Name:** Toy Impression Generator
- **Version:** 1.0.0
- **Format:** ONNX
- **License:** MIT
- **Developer:** E.S.L SOFTWARE LAB LTD
- **Model type:** Handcrafted autoregressive token generator
- **Training data:** None; the weights are deterministic constants

## Intended use

The model exists solely to demonstrate inventory, integrity, change detection,
and rebenchmark controls for AI-enabled software. It provides a small model
artifact whose behavior and evaluation results can be reproduced exactly.

## Prohibited use

Do not use this model for diagnosis, treatment, patient care, clinical decision
support, research conclusions, or assessment of real medical images or records.

## Inputs

The ONNX graph accepts:

1. `context`: one row of four floating-point synthetic features:
   `opacity`, `left`, `right`, and `confidence`.
2. `previous_token`: one row containing a one-hot vector over the eight-token
   vocabulary.

No input represents a patient or a real clinical observation.

## Outputs

`logits` contains scores for the next token. The reference evaluator performs
greedy autoregressive decoding until `<END>` or six generated tokens.

Vocabulary: `<START>`, `NO`, `ACUTE`, `FINDING`, `LEFT`, `RIGHT`, `OPACITY`,
`<END>`.

## Evaluation

The fixed synthetic dataset contains three branch-coverage cases. The release
baseline requires 3/3 exact generated-sequence matches. This is a software
regression check, not evidence of clinical performance.

## Limitations

- The vocabulary and outputs are deliberately tiny.
- The model was not trained and does not generalize.
- The evaluation dataset is synthetic and is not statistically meaningful.
- Exact-match success does not establish safety, efficacy, or clinical utility.
