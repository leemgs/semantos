"""Deterministic lexical embedding for the trace index.

Feature hashing of lower-cased tokens (SHA-256 bucket and sign) into DIM
dimensions, L2-normalized, so that inner-product search ranks traces by shared
tokens such as knob names, values and workload labels. This is a lexical
baseline, not a learned semantic encoder, and it is identical across processes
(unlike Python's randomized hash()).
"""
import hashlib
import re

import numpy as np

DIM = 128
VERSION = 'sha256-token-hash-v1'
TOKEN = re.compile(r'[a-z0-9_.\-]+')


def embed(text, dim=DIM):
    v = np.zeros(dim, dtype='float32')
    # "key=value" pairs contribute the pair and its value as separate features.
    for part in re.split(r'\s+', text.lower()):
        feats = TOKEN.findall(part)
        if '=' in part:
            feats.append(part)
        for tok in feats:
            h = hashlib.sha256(tok.encode()).digest()
            v[int.from_bytes(h[:4], 'little') % dim] += 1.0 if h[4] & 1 else -1.0
    norm = float(np.linalg.norm(v))
    return v / norm if norm else v
