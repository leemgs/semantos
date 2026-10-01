import importlib.util
import itertools
import math
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'safety-runtime'))
from safety_core import ADWIN, SlidingCalibrator, conformal_threshold, gate_counts, select_tau_by_cost
import app as runtime


class RankGateTests(unittest.TestCase):
    def test_exact_exchangeable_rank_bound(self):
        # Exhaust all held-out ranks, not noise matched to a desired result.
        for n, alpha in itertools.product([1, 3, 9, 19], [.05, .1, .3]):
            values = [i / (n + 2) for i in range(1, n + 2)]
            misses = 0
            for i, test in enumerate(values):
                train = values[:i] + values[i + 1:]
                tau = conformal_threshold(train, [True] * n, alpha)
                misses += test < tau
            self.assertLessEqual(misses / (n + 1), alpha + 1e-12)

    def test_small_samples_empty_and_ties_fail_closed(self):
        self.assertEqual(conformal_threshold([], [], .1), 0)
        self.assertEqual(conformal_threshold([.2], [True], .1), 0)
        self.assertEqual(conformal_threshold([.2] * 20, [True] * 20, .1), .2)
        self.assertEqual(gate_counts([.2] * 20, [True] * 20, .2)['fn'], 0)

    def test_reject_bad_input(self):
        for u,y in [([math.nan],[True]), ([1.1],[True]), ([.2],['false']), ([.2],[])]:
            with self.assertRaises(ValueError):
                conformal_threshold(u, y, .1)

    def test_cost_does_not_relax_rank_cap(self):
        c = SlidingCalibrator(dslo_of_tau=lambda t: 0, cost={'c_fn':0, 'c_fp':100, 'lam':0, 'slo_budget_delta':1})
        for i in range(20): c.observe(i / 20, True)
        for _ in range(20): c.observe(.5, False)
        self.assertLessEqual(c.recalibrate(), conformal_threshold(list(c._u), list(c._y), .1))
        self.assertEqual(select_tau_by_cost([.2],[True],lambda t:2,{'c_fn':1,'c_fp':1,'lam':1,'slo_budget_delta':1}),0)

    def test_detector_sum_after_eviction(self):
        d = ADWIN(max_buckets=8)
        for _ in range(100): d.update(.5)
        self.assertAlmostEqual(d.total, sum(d.window))

    def test_denominators(self):
        c = SlidingCalibrator()
        self.assertIsNone(c.metrics()['precision'])
        self.assertEqual(gate_counts([.1,.8,.2,.9],[True,True,False,False],.5),dict(tp=1,fp=1,fn=1,tn=1))


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        runtime.TRACE_PATH = Path(self.tmp.name) / 'trace.jsonl'
        runtime.state.update(active=False, rec_id=None, percent=0, bundle=[], history=[], vetoed=[])
        runtime.calibrator.tau = .5
        self.recs = [dict(id='a',knob='vm.dirty_background_ratio',proposed='5',uncertainty=.1,bundle='b'),
                     dict(id='b',knob='vm.dirty_ratio',proposed='15',uncertainty=.2,bundle='b')]

    def tearDown(self): self.tmp.cleanup()

    def test_atomic_veto(self):
        self.recs[1]['uncertainty'] = .9
        r = runtime.apply({'recommendations':self.recs})
        self.assertEqual(r['vetoed'], ['a','b'])
        self.assertEqual(r['simulated'], [])
        self.assertFalse(runtime.state['active'])

    def test_simulate_and_cancel_whole_bundle(self):
        r = runtime.apply({'recommendations':self.recs})
        self.assertEqual(r['applied'], [])
        self.assertEqual(r['simulated'], ['a','b'])
        self.assertEqual(len(runtime.state['bundle']), 2)
        runtime.rollback()
        self.assertEqual(runtime.state['bundle'], [])

    def test_invalid_bundle_and_duplicate_active(self):
        from fastapi import HTTPException
        for mutate in [lambda r:r[0].update(knob='sched_wake_affinity'),
                       lambda r:r[1].update(uncertainty=float('nan')),
                       lambda r:r[0].update(proposed='20'),
                       lambda r:r[1].update(bundle='other')]:
            recs=[dict(r) for r in self.recs]; mutate(recs)
            with self.assertRaises(HTTPException): runtime.apply({'recommendations':recs})
        runtime.apply({'recommendations':self.recs})
        with self.assertRaises(HTTPException): runtime.apply({'recommendations':self.recs})

    def test_dry_run_outcome_does_not_train_gate(self):
        before = runtime.calibrator.metrics()['n']
        runtime.log_outcome({'u':.1,'unsafe':False})
        self.assertEqual(runtime.calibrator.metrics()['n'], before)
