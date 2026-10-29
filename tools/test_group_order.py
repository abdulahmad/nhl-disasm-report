#!/usr/bin/env python3
"""Check SNES groups views re-sort to each Genesis game's include order.

Reads docs/data/*.js (run generate.py first). 93S and 94S vs 92G/93G/94G/95G/96G:
matched modules follow that game's `seq`; unmatched keep first-ROM order after them.
Banks targets must not be used as a groups-sort key (empty overlap is fine).
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs', 'data')
SNES = ('93S', '94S')
GENESIS = ('92G', '93G', '94G', '95G', '96G')

def file_key(f):
    parts = f.rstrip('/').split('/')
    if parts[0] == 'routines' and len(parts) > 1:
        parts = parts[:2]
    b = parts[-1]
    if not f.endswith('/') and len(parts) == len(f.rstrip('/').split('/')):
        b = os.path.splitext(b)[0]
    b = b.lower()
    m = re.match(r'^(.+?)9[2-6](?:snes|s)?(?:_.*)?$', b)
    return m.group(1) if m else b

def load(gid):
    raw = open(os.path.join(DOCS, gid + '.js'), encoding='ascii').read()
    return json.loads(raw[raw.index('(') + 1:raw.rindex(')')])

def modules(groups):
    return [file_key(g['f']) for g in groups if not (g.get('d') or 0)]

def sort_modules(mods, seq):
    pos = {}
    for i, k in enumerate(seq or []):
        pos.setdefault(k, i)
    keyed = [(i, k) for i, k in enumerate(mods)]
    keyed.sort(key=lambda x: (pos.get(x[1], 10**9), x[0]))
    return [k for _, k in keyed]

def main():
    failed = 0
    for sid in SNES:
        d = load(sid)
        stored = modules(d['views']['groups'])
        bank = [b['f'] for b in d['views']['banks']]
        for gid in GENESIS:
            tg = d['targets'].get(gid) or {}
            seq = tg.get('seq') or []
            if not seq:
                print(f'FAIL {sid} vs {gid}: missing seq'); failed += 1; continue
            after = sort_modules(stored, seq)
            matched = [k for k in seq if k in set(stored)]
            got = [k for k in after if k in set(seq)]
            unmatched_before = [k for k in stored if k not in set(seq)]
            unmatched_after = [k for k in after if k not in set(seq)]
            ok = got == matched and unmatched_after == unmatched_before
            print(f'{"OK  " if ok else "FAIL"} {sid} vs {gid}: {after}')
            if not ok:
                print(f'      expected matched {matched} unmatched {unmatched_before}')
                failed += 1
        for tid, tg in d['targets'].items():
            if tid.endswith(':banks'):
                overlap = set(stored) & set(tg.get('seq') or [])
                if overlap:
                    print(f'FAIL {sid} vs {tid}: banks seq overlaps groups {sorted(overlap)}')
                    failed += 1
        if [b['f'] for b in d['views']['banks']] != bank:
            print(f'FAIL {sid}: banks view mutated'); failed += 1
    if failed:
        print(f'{failed} failure(s)'); sys.exit(1)
    print('all 93S/94S × Genesis groups orders OK')

if __name__ == '__main__':
    main()
