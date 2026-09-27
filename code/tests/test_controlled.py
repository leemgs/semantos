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
from model_audit import api_backend, evidence, experiment, heldout, validate_answer
from cited_deletion_probe import controls_for
from summarize_model_audit import numbers_grounded


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

    def test_heldout_scoring_matches_selector_replay(self):
        root = ROOT/'evaluation/results/controlled-2026-09-26'
        reported = {(c['period_ms'], c['method']): c for c in
                    json.loads((root/'analysis.json').read_text())['comparisons']}
        scored = heldout(root, [{'status': 'valid', 'variant': 'full', 'seed': 1,
                                 'answer': {'config': 's50000_aall'}},
                                {'status': 'failed', 'variant': 'full', 'seed': 2}])
        self.assertEqual(len(scored), 2)  # failed calls are never scored
        for row in scored:
            ref = reported[row['period_ms'], 'control']
            self.assertAlmostEqual(row['p95_us']['mean'], ref['p95_us']['mean'], places=6)
            self.assertEqual(row['reduction_pct']['mean'], 0.0)
            self.assertTrue(row['same_as_control'])

    def test_probe_controls_match_cited_retrieval_kind_and_config(self):
        _, items = evidence(ROOT/'evaluation/results/controlled-2026-09-26')
        retrieval = [i for i in items if i['kind'] == 'retrieval']
        cited = {'training-table', retrieval[0]['id'], retrieval[1]['id']}
        controls = controls_for(cited, items)
        self.assertEqual(len(controls), 2)
        self.assertTrue(all(c['kind'] == 'retrieval' and c['id'] not in cited for c in controls))
        self.assertEqual(len({c['id'] for c in controls}), 2)
        by_id = {i['id']: i for i in items}
        self.assertEqual(sorted(c['config'] for c in controls),
                         sorted(by_id[i]['config'] for i in cited if i != 'training-table'))

    def test_api_backend_sends_schema_retries_and_records_metadata(self):
        import io as _io
        import urllib.error
        sent = []
        body = {'id': 'r1', 'model': 'm-reported', 'provider': 'P', 'system_fingerprint': 'fp',
                'choices': [{'finish_reason': 'stop', 'message': {'content':
                    '```json\n{"config": "a", "cited_ids": [], "explanation": "x"}\n```'}}]}

        class Response(_io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        def opener(request, timeout):
            sent.append(json.loads(request.data))
            if len(sent) == 1:
                raise urllib.error.HTTPError(request.full_url, 429, 'rate', {}, _io.BytesIO(b'slow down'))
            return Response(json.dumps(body).encode())

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'sk-test-secret'}), patch('time.sleep'):
            backend, manifest = api_backend('openrouter', 'm', min_interval=0, opener=opener)
            out = backend('sys', json.dumps({'allowed_configs': ['a', 'b'], 'evidence': [{'id': 'e1'}]}), 7)
        self.assertEqual(len(sent), 2)
        self.assertEqual(sent[1]['seed'], 7)
        self.assertEqual(sent[1]['temperature'], 0)
        schema = sent[1]['response_format']['json_schema']['schema']
        self.assertEqual(schema['properties']['config']['enum'], ['a', 'b'])
        self.assertEqual(schema['properties']['cited_ids']['items']['enum'], ['e1'])
        self.assertTrue(sent[1]['provider']['require_parameters'])
        self.assertEqual(json.loads(out['content'])['config'], 'a')
        self.assertTrue(out['meta']['fence_stripped'])
        self.assertEqual(out['meta']['reported_model'], 'm-reported')
        self.assertEqual(out['meta']['retried_errors'][0]['status'], 429)
        self.assertIsNone(manifest['sha256'])
        self.assertNotIn('sk-test-secret', json.dumps(manifest))

    def test_numbers_grounded_is_lexical(self):
        record = {'prompt': '{"p95_us": 126.36}',
                  'answer': {'explanation': 'mean 126.36 us, not 99.9 us'}}
        self.assertEqual(numbers_grounded(record), (2, 1))

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
