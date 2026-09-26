# Proposed training configuration

`config.yaml` is a design example, not an executed pipeline. There is no released
trained checkpoint, training log or verified model revision. Llama 3.1 has 8B,
70B and 405B variants; the former 13B claim was erroneous. The 8B-Instruct example
does not assert that it was used for the rejected paper.

Before any experiment, record the actual model ID, immutable revision/digest,
license, tokenizer, prompt, inference parameters and input-data hashes. If using
fine-tuning, also record executable training code, run logs and output checkpoint
hashes. Exclude held-out groups from training, graph induction, retrieval and
calibration (see `evaluation/README.md`). Quarantined synthetic data is not evidence.
