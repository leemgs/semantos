"""Package the current research artifact; exclude historical numerical claims."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[2]
EXCLUDED={'legacy','__pycache__','.git','.venv','node_modules','outputs'}
SUFFIXES={'.py','.md','.txt','.yaml','.yml','.sh','.json','.jsonl','.csv','.tex','.bib','.bst','.sty','.png','.pdf'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.error('choose a new output path')
    selected=[ROOT/'README.md']
    for base in ['code','paper']:
        for f in (ROOT/base).rglob('*'):
            rel=f.relative_to(ROOT)
            if not f.is_file() or EXCLUDED.intersection(rel.parts):continue
            if 'data' in rel.parts and 'operator-console' in rel.parts:continue
            if f.name=='main_bluelink.pdf':continue
            if f.suffix in SUFFIXES or f.name in {'Makefile','Dockerfile'}:selected.append(f)
    manifest={}
    with zipfile.ZipFile(a.out,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for f in sorted(selected):
            content=f.read_bytes();name=f.relative_to(ROOT).as_posix()
            manifest[name]=hashlib.sha256(content).hexdigest();z.writestr(name,content)
        z.writestr('SHA256SUMS.json',json.dumps(manifest,indent=2))
    print(json.dumps({'archive':str(a.out),'files':len(manifest),'sha256':hashlib.sha256(a.out.read_bytes()).hexdigest()},indent=2))

if __name__=='__main__':main()
