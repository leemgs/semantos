# Quarantined historical synthetic artifacts

NOT measured results, a benchmark, a trained model, or independent reproduction.
`reproduce/response_model.py` injects manuscript targets and Gaussian noise;
`spec.py`, `calibration.py`, `controllers.py` and theory checks likewise embed
assumptions or targets. Their PASS output does not validate the paper.
`data/` is generated, not 1,000 measured workload/hardware pairs.
The historical code is retained for audit, including its known mathematical errors.
It is not used by the current runtime, evaluation tools or build targets.
Do not train or evaluate a claimed empirical system on these artifacts.
