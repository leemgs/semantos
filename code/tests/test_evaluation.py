import copy
import importlib.util
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'evaluation'))
from validate_split import validate
from safety_counts import summarize
from induce_graph import induce

class EvaluationTests(unittest.TestCase):
    def manifest(self):
        return {'records':[{'id':'a','group':'train-host','role':'train','sha256':'a'*64},
                           {'id':'b','group':'test-host','role':'test','sha256':'b'*64}],
                'artifacts':[{'kind':'graph','sources':['a']},{'kind':'evaluation','sources':['b']}]}
    def test_split_leakage(self):
        validate(self.manifest())
        for modify in [lambda m:m['records'][1].update(group='train-host'),
                       lambda m:m['artifacts'][0].update(sources=['b']),
                       lambda m:m['records'][1].update(sha256='a'*64)]:
            m=self.manifest();modify(m)
            with self.assertRaises(ValueError):validate(m)
    def test_unknown_and_veto_are_not_rollback(self):
        x=summarize([{'bundle_id':'a','decision':'vetoed','unsafe':None,'rolled_back':False},
                     {'bundle_id':'b','decision':'accepted','unsafe':True,'rolled_back':True}])
        self.assertEqual(x['counts']['unknown'],1)
        self.assertEqual(x['counts']['tp'],0)
        self.assertIsNone(x['veto_precision'])
        self.assertEqual(x['rollback_precision_labeled_only'],1)
    def test_measured_interaction_and_test_exclusion(self):
        rows=[{'id':str(i),'run':i,'split':'train','source':'measured','group':'g','pair':['a','b'],
               'losses':{'baseline':100,'a':90,'b':90,'joint':70}} for i in range(10)]
        self.assertEqual(induce(rows)[0]['edge_type'],'synergizes_with')
        rows[0]['split']='test'
        with self.assertRaises(ValueError):induce(rows)
    def test_no_edge_for_additive_effects(self):
        rows=[{'id':str(i),'run':i,'split':'train','source':'measured','group':'g','pair':['a','b'],
               'losses':{'baseline':100,'a':90,'b':90,'joint':80}} for i in range(10)]
        self.assertEqual(induce(rows),[])
