import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

import numpy as np

PATH = Path(__file__).resolve().parents[1]/'kb-service'/'embedding.py'
spec = importlib.util.spec_from_file_location('kb_embedding', PATH)
emb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(emb)


class EmbeddingTests(unittest.TestCase):
    def test_deterministic_across_processes(self):
        code = (f"import importlib.util as u;s=u.spec_from_file_location('e',{str(PATH)!r});"
                "m=u.module_from_spec(s);s.loader.exec_module(m);print(m.embed('knob=vm.dirty_ratio value=15').tolist())")
        runs = {subprocess.run([sys.executable, '-c', code], capture_output=True, text=True,
                               env={'PYTHONHASHSEED': seed}).stdout for seed in ('1', '2')}
        self.assertEqual(len(runs), 1)

    def test_shared_tokens_rank_above_unrelated_text(self):
        q = emb.embed('workload=sqlite knob=vm.dirty_ratio value=15')
        near = emb.embed('workload=sqlite server=a knob=vm.dirty_ratio value=20 delta_p95=-3')
        far = emb.embed('workload=zlib server=b knob=kernel.sched_min_granularity_ns value=3000000')
        self.assertGreater(float(q @ near), float(q @ far))
        self.assertAlmostEqual(float(np.linalg.norm(q)), 1.0, places=5)

    def test_empty_text_is_zero_vector(self):
        self.assertEqual(float(np.linalg.norm(emb.embed(''))), 0.0)


if __name__ == '__main__':
    unittest.main()
