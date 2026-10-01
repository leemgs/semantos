import contextlib
import io
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'evaluation'))
from analyze_kernel_local import analyze

class KernelMeasurementTests(unittest.TestCase):
    def test_measured_artifact_and_tamper_rejection(self):
        source=Path(__file__).resolve().parents[1]/'evaluation/results/kernel-local-2026-09-26'
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'result'
            shutil.copytree(source,target)
            with contextlib.redirect_stdout(io.StringIO()):
                analyze(target)
            with (target/'runs.jsonl').open('a') as stream:
                stream.write('{}\n')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):
                analyze(target)
