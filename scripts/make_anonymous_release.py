#!/usr/bin/env python3
"""Build an anonymized copy of this repository for double-blind review.

The copy contains the tracked files of a git revision (default HEAD) minus the
paths in EXCLUDE, which hold author names, the earlier venue's submission and
review history, or internal notes. Every remaining text file is then scanned
for FORBIDDEN patterns and the build fails if any match, so the output can be
mirrored (e.g., on anonymous.4open.science) or uploaded as supplementary
material without revealing the authors. Git history is not included.

Usage:
    python3 scripts/make_anonymous_release.py --out /tmp/semantos-anon
    python3 scripts/make_anonymous_release.py --out /tmp/semantos-anon --zip
"""
import argparse
import fnmatch
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Paths (glob patterns on repository-relative paths) left out of the copy.
EXCLUDE = [
    'archive/*',                         # earlier submission, slides with author names
    'ppt/*',                             # pointer to the archived slides
    'REVIEW_*.md',                       # responses to the earlier venue's reviews
    'code/legacy/*',                     # superseded prototype; names the earlier submission
    'paper/aaai2027.bib',                # leftover template file from the earlier venue
    'paper/responsible-nlp-checklist.md',  # internal notes for the submission form
    'paper/anonymous-review.md',           # instructions that refer to the excluded material
    'scripts/make_anonymous_release.py',   # lists the identifying terms itself
]

# Patterns that must not appear in any released text file (case-insensitive).
FORBIDDEN = [
    r'geunsik', r'leemgs', r'\bG\.\s*Lim\b', r'\bLim,\s*G', r'@gmail\.com',
    r'\bAAAI\b', r'openreview', r'submission\s+4088', r'github\.com/leemgs',
    r'claude-session', r'/home/[a-z][\w.-]*', r'/Users/\w+',
]


def tracked_files(rev):
    out = subprocess.run(['git', '-C', str(ROOT), 'ls-tree', '-r', '--name-only', rev],
                         check=True, capture_output=True, text=True).stdout
    return [p for p in out.splitlines() if p]


def excluded(path):
    return any(fnmatch.fnmatch(path, pat) for pat in EXCLUDE)


def is_text(data):
    return b'\0' not in data[:8192]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True, type=Path, help='output directory (must not exist)')
    ap.add_argument('--rev', default='HEAD', help='git revision to export')
    ap.add_argument('--zip', action='store_true', help='also write <out>.zip')
    a = ap.parse_args()
    if a.out.exists():
        ap.error(f'{a.out} exists; choose a new path')

    files = [p for p in tracked_files(a.rev) if not excluded(p)]
    patterns = [re.compile(p, re.I) for p in FORBIDDEN]
    hits, binaries = [], []
    for rel in files:
        data = subprocess.run(['git', '-C', str(ROOT), 'show', f'{a.rev}:{rel}'],
                              check=True, capture_output=True).stdout
        dest = a.out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        if is_text(data):
            text = data.decode('utf-8', errors='replace')
            for pat in patterns:
                for m in pat.finditer(text):
                    line = text.count('\n', 0, m.start()) + 1
                    hits.append(f'{rel}:{line}: {m.group(0)!r}')
        else:
            binaries.append(rel)

    if hits:
        shutil.rmtree(a.out)
        print('Identifying content found; nothing written:', *hits, sep='\n  ', file=sys.stderr)
        sys.exit(1)
    if a.zip:
        shutil.make_archive(str(a.out), 'zip', root_dir=a.out)
    print(f'{len(files)} files written to {a.out}' + (f' and {a.out}.zip' if a.zip else ''))
    print('Binary files (not text-scanned; check metadata by hand):', *binaries, sep='\n  ')


if __name__ == '__main__':
    main()
