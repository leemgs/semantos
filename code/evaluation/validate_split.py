"""Validate disjoint acquisition groups and artifact lineage before evaluation."""
import argparse
import json
from pathlib import Path

ROLES = {'train', 'retrieval', 'calibration', 'test'}
ALLOWED = {'model': {'train'}, 'graph': {'train'}, 'retrieval_index': {'retrieval'},
           'calibrator': {'calibration'}, 'evaluation': {'test'}}


def validate(manifest):
    records = {}
    group_roles = {}
    for row in manifest['records']:
        rid, group, role = row['id'], row['group'], row['role']
        if not rid or not group or role not in ROLES or rid in records:
            raise ValueError('invalid/duplicate record or role')
        digest = row['sha256']
        if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('invalid source digest')
        if group in group_roles and group_roles[group] != role:
            raise ValueError(f'group leakage: {group}')
        group_roles[group] = role
        records[rid] = row
    if not records:
        raise ValueError('empty manifest')
    hashes = {}
    for row in records.values():
        if row['sha256'] in hashes and hashes[row['sha256']] != row['role']:
            raise ValueError('identical content assigned across roles')
        hashes[row['sha256']] = row['role']
    for artifact in manifest['artifacts']:
        kind = artifact['kind']
        if kind not in ALLOWED or not artifact['sources']:
            raise ValueError('invalid or missing lineage')
        for source in artifact['sources']:
            if source not in records or records[source]['role'] not in ALLOWED[kind]:
                raise ValueError(f'forbidden source {source} for {kind}')
    return {'records':len(records), 'groups':len(group_roles), 'status':'manifest_consistent',
            'limitation':'checks declared lineage; does not authenticate acquisition or hidden inputs'}

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);args=p.parse_args()
    print(json.dumps(validate(json.loads(args.manifest.read_text())),indent=2))
