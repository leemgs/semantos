import asyncio
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, patch
import httpx

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'safety-runtime'))
import app as runtime


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

reasoner=load('reasoner_test',ROOT/'reasoner/app.py')

class RuntimeHTTPTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory();runtime.TRACE_PATH=Path(self.tmp.name)/'trace.jsonl'
        runtime.state.update(active=False,rec_id=None,percent=0,bundle=[],history=[],vetoed=[])
        runtime.calibrator.tau=.5
        self.client=httpx.AsyncClient(transport=httpx.ASGITransport(app=runtime.app),base_url="http://test")
        self.rec=dict(id='a',bundle='bundle',knob='vm.swappiness',proposed='60',uncertainty=.1)
    async def asyncTearDown(self):
        await self.client.aclose()
        self.tmp.cleanup()
    async def request(self, method, path, **kwargs):
        # The restricted runner may not deliver cross-thread selector wakeups.
        # A timer keeps the event loop progressing; it does not mock the route.
        async def tick():
            while True:
                await asyncio.sleep(.01)
        ticker=asyncio.create_task(tick())
        try:
            return await asyncio.wait_for(self.client.request(method,path,**kwargs),timeout=3)
        finally:
            ticker.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await ticker
    async def test_complete_bundle_stage_contract(self):
        response=await self.request('POST','/apply',json={'recommendations':[self.rec]})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['applied'],[])
        self.assertEqual(response.json()['simulated'],['a'])
        for percent in [25,50,100,100]:
            self.assertEqual((await self.request('POST','/rollout/advance')).json()['percent'],percent)
        self.assertFalse((await self.request('GET','/status')).json()['active'])
    async def test_bad_calibration_is_transactional(self):
        n=runtime.calibrator.metrics()['n']
        response=await self.request('POST','/calibrate',json=[{'u':.1,'unsafe':True},{'u':.2,'unsafe':'false'}])
        self.assertEqual(response.status_code,422)
        self.assertEqual(runtime.calibrator.metrics()['n'],n)
    def test_failed_persistence_does_not_start_simulation(self):
        with patch.object(runtime,'trace',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):runtime.apply({'recommendations':[self.rec]})
        self.assertFalse(runtime.state['active'])

class ReasonerTests(unittest.IsolatedAsyncioTestCase):
    async def test_proxy_telemetry_abstains(self):
        with patch.object(reasoner,'rag_context',AsyncMock(return_value={'telemetry':{'end_to_end_latency_valid':False}})):
            result=await reasoner._recommend()
        self.assertEqual(result['recommendations'],[])
    async def test_empty_explicit_request_does_not_generate(self):
        client=AsyncMock()
        import httpx
        client.post.return_value=httpx.Response(200,json={'mode':'dry_run','applied':[]},request=httpx.Request('POST','http://runtime/apply'))
        with patch.object(reasoner,'_recommend',AsyncMock()) as recommend, patch.object(reasoner.httpx,'AsyncClient') as factory:
            factory.return_value.__aenter__.return_value=client
            result=await reasoner.apply({'recommendations':[]})
            recommend.assert_not_called()
            self.assertEqual(json.loads(result.body)['submitted'],0)
    async def test_failed_samples_do_not_inflate_agreement(self):
        ctx={'telemetry':{'metrics':{}},'dependency_graph':{}}
        rec={'knob':'vm.swappiness','proposed':'60'}
        result=reasoner.aggregate_self_consistency([{'recommendations':[rec]},None,None],ctx)
        self.assertEqual(result['recommendations'][0]['provenance']['self_consistency']['k'],3)
        self.assertGreater(result['recommendations'][0]['uncertainty'],.7)

class ConsoleTests(unittest.IsolatedAsyncioTestCase):
    async def test_console_forwards_all_bundle_members(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{'CONSOLE_DATA_DIR':d}):
            console=load('console_test',ROOT/'operator-console/app/main.py')
            recs=[{'id':'a','bundle':'b','status':'pending'},{'id':'c','bundle':'b','status':'pending'}]
            console._save_json(console.REC_FILE,recs)
            result={'mode':'dry_run','applied':[],'simulated':['a','c'],'vetoed':[]}
            with patch.object(console,'_post',AsyncMock(return_value=result)) as post:
                await console.approve('a')
            self.assertEqual(len(post.call_args.args[2]['recommendations']),2)
            self.assertTrue(all(r['status']=='simulated' for r in console._load_json(console.REC_FILE,[])))
