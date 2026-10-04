"""Dry-run bundle gate and rollout state machine. Never writes kernel settings.

A bundle is validated, vetoed, staged and cancelled as a unit. 'simulated' never
means applied. No telemetry proxy is treated as an end-to-end SLO measurement.
"""
import json
import math
import os
import threading
import time
from pathlib import Path

from fastapi import FastAPI, Body, HTTPException
from safety_core import SlidingCalibrator

app = FastAPI(title='GroundKern dry-run runtime', version='2.0.0')
calibrator = SlidingCalibrator(
    alpha=float(os.environ.get('CONFORMAL_ALPHA', '0.1')),
    window=int(os.environ.get('CAL_WINDOW', '400')),
    tau_floor=float(os.environ.get('TAU', '0.55')))
ROLL = [5, 25, 50, 100]
TRACE_PATH = Path(os.environ.get('TRACE_PATH', '/app/outputs/optimization_trace.jsonl'))
lock = threading.RLock()
# Deliberately narrow example policy. These are policy bounds, not universal
# kernel admissible ranges or a claim that these values improve performance.
BOUNDS = {'vm.dirty_background_ratio': (0, 100), 'vm.dirty_ratio': (1, 100),
          'vm.swappiness': (0, 200)}
state = {'mode': 'dry_run', 'active': False, 'rec_id': None, 'percent': 0,
         'bundle': [], 'history': [], 'vetoed': []}


def trace(event, **payload):
    record = dict(ts=time.time(), mode='dry_run', event=event, **payload)
    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TRACE_PATH.open('a') as f:
        f.write(json.dumps(record, allow_nan=False) + '\n')
    return record


def validate_bundle(recs):
    if not isinstance(recs, list):
        raise ValueError('recommendations must be a list')
    ids, knobs, bundles = set(), {}, set()
    for rec in recs:
        if not isinstance(rec, dict):
            raise ValueError('recommendation must be an object')
        rid, knob, bid = rec.get('id'), rec.get('knob'), rec.get('bundle')
        if not isinstance(rid, str) or not rid or rid in ids:
            raise ValueError('nonempty unique recommendation ids required')
        if not isinstance(bid, str) or not bid:
            raise ValueError('explicit bundle id required')
        if knob not in BOUNDS or knob in knobs:
            raise ValueError('unsupported or duplicate knob')
        proposed = rec.get('proposed')
        if isinstance(proposed, bool) or not isinstance(proposed, (str, int)):
            raise ValueError('proposed must be an integer or integer string')
        value = int(proposed)
        lo, hi = BOUNDS[knob]
        if not lo <= value <= hi:
            raise ValueError('value outside example policy bounds')
        u = rec.get('uncertainty')
        if isinstance(u, bool) or not isinstance(u, (int, float)) or not math.isfinite(u) or not 0 <= u <= 1:
            raise ValueError('finite uncertainty in [0,1] required')
        ids.add(rid); bundles.add(bid); knobs[knob] = value
    if len(bundles) > 1:
        raise ValueError('submit one atomic bundle per request')
    dirty = {'vm.dirty_ratio', 'vm.dirty_background_ratio'}
    if dirty & knobs.keys():
        if not dirty <= knobs.keys():
            raise ValueError('include both dirty ratio values for joint validation')
        if knobs['vm.dirty_background_ratio'] >= knobs['vm.dirty_ratio']:
            raise ValueError('policy requires background ratio < dirty ratio')
    return [r['id'] for r in recs]


@app.get('/healthz')
def healthz():
    return {'ok': True, 'mode': 'dry_run', 'kernel_writes': False, 'tau': calibrator.tau}


@app.post('/apply')
def apply(body: dict = Body(...)):
    try:
        recs = body.get('recommendations', [])
        ids = validate_bundle(recs)
    except (TypeError, ValueError) as e:
        raise HTTPException(422, str(e)) from e
    with lock:
        if state['active']:
            raise HTTPException(409, 'finish or cancel the active bundle first')
        veto = bool(recs) and any(r['uncertainty'] >= calibrator.tau for r in recs)
        record = trace('gate', recommendations=recs, tau=calibrator.tau,
                       decision='veto' if veto else 'simulate', bundle_atomic=True)
        if veto:
            state['vetoed'].extend(ids)
        elif recs:
            state.update(active=True, rec_id=recs[0]['bundle'], percent=ROLL[0], bundle=recs)
        state['history'].append(record)
        return dict(mode='dry_run', applied=[], simulated=[] if veto else ids,
                    vetoed=ids if veto else [], tau=calibrator.tau)


@app.post('/rollout/advance')
def advance():
    with lock:
        if not state['active']:
            return {'ok': False, 'mode': 'dry_run', 'reason': 'no_active_bundle'}
        idx = ROLL.index(state['percent'])
        complete = idx == len(ROLL) - 1
        next_percent = 100 if complete else ROLL[idx + 1]
        record = trace('simulated_complete' if complete else 'simulated_stage',
                       bundle_id=state['rec_id'], percent=next_percent)
        state.update(active=not complete, percent=next_percent)
        state['history'].append(record)
        return {'ok': True, 'mode': 'dry_run', 'percent': next_percent, 'completed': complete}


@app.post('/rollback')
def rollback():
    with lock:
        record = trace('simulated_cancel', bundle_id=state['rec_id'], recommendations=state['bundle'])
        state.update(active=False, percent=0, bundle=[])
        state['history'].append(record)
        return {'ok': True, 'mode': 'dry_run', 'kernel_rollback': False}


@app.get('/status')
def status():
    with lock:
        return {**state, 'calibration': calibrator.metrics()}


@app.post('/calibrate')
def calibrate(records: list = Body(...)):
    # Validate the entire request before mutating the calibration window.
    from safety_core import validate_records
    try:
        for r in records:
            validate_records([r['u']], [r['unsafe']])
    except (KeyError, TypeError, ValueError) as e:
        raise HTTPException(422, 'records require finite u and boolean unsafe') from e
    with lock:
        trace('calibration_input', records=records, scope='unverified_external_labels')
        for r in records:
            calibrator.observe(r['u'], r['unsafe'])
        calibrator.recalibrate()
        return calibrator.metrics()


@app.post('/log_outcome')
def log_outcome(body: dict = Body(...)):
    # Dry-run outcomes are not evidence of a real action's safety.
    with lock:
        trace('unverified_outcome', payload=body)
    return {'ok': True, 'mode': 'dry_run', 'used_for_calibration': False}
