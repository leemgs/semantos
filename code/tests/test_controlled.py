"""Regression fixtures, not performance or model evidence."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'evaluation'))
import controlled_kernel as ck
from analyze_controlled import analyze
from model_audit import experiment, validate_answer


class ControlledTests(unittest.TestCase):
    def test_partial_application_restores_original_bundle(self):
        old = {'slack_ns': 50000, 'cpus': [0, 1]}
        case = {'role': 'staged'}
        with patch.object(ck, 'snapshot', return_value=old), \
             patch.object(ck, 'set_bundle', side_effect=OSError('second write fails')), \
             patch.object(ck, 'restore') as restore:
            with self.assertRaises(OSError):
                ck.child(case)
            restore.assert_called_once_with(old)

    def test_missing_or_invented_citation_rejected(self):
        with self.assertRaises(ValueError):
            validate_answer({'config': 'x', 'cited_ids': ['deleted'], 'explanation': 'x'},
                            ['x'], [{'id': 'actual'}])

    def test_model_inputs_exclude_test_and_failure_is_recorded(self):
        root = ROOT/'evaluation/results/controlled-2026-09-26'
        def failed(system, prompt, seed):
            context = json.loads(prompt)
            for row in context['evidence']:
                self.assertFalse(row['id'].startswith(('test-', 'calibration-', 'staged-')))
            raise PermissionError('fixture endpoint unavailable')
        records = experiment(root, failed, [1, 2])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['status'], 'failed')
        self.assertNotIn('answer', records[0])

    def test_context_deletion_uses_same_kind_controls(self):
        root = ROOT/'evaluation/results/controlled-2026-09-26'
        def fixture(system, prompt, seed):
            context = json.loads(prompt)
            retrieved = [i for i in context['evidence'] if i['kind'] == 'retrieval']
            return json.dumps({'config': context['allowed_configs'][0],
                               'cited_ids': [retrieved[0]['id']] if retrieved else [],
                               'explanation': 'unit test fixture'})
        records = experiment(root, fixture, [1])
        faithfulness = next(r for r in records if r['variant'] == 'faithfulness')
        self.assertEqual(faithfulness['status'], 'valid')
        self.assertFalse(faithfulness['cited_action_changed'])
        self.assertNotEqual(faithfulness['cited_deleted'], faithfulness['uncited_deleted'])

    def test_raw_tampering_prevents_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)/'data'
            shutil.copytree(ROOT/'evaluation/results/controlled-2026-09-26', dest)
            with (dest/'runs.jsonl').open('a') as f:
                f.write('{}\n')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                analyze(dest)

    def test_recorded_analysis_reproduces_counts(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)/'data'
            shutil.copytree(ROOT/'evaluation/results/controlled-2026-09-26', dest)
            with contextlib.redirect_stdout(io.StringIO()):
                result = analyze(dest)
            self.assertEqual(result['runs'], 280)
            self.assertEqual(result['grid_events'], 8000)
            self.assertEqual(sum(r['restored'] for r in result['staged_execution']), 80)
