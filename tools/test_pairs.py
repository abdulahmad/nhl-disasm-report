#!/usr/bin/env python3
"""Pairing gate: checks that the disassemblies still line up, next to each repo's MATCH.

It fails (exit 1) when
  * a row of tools/known_pairs.csv no longer pairs (both names must exist and be the same name or linked
    by a name map), or
  * a count below is higher than in tools/baseline.json.

Counts (each is a list of routines, printed with --list):
  94S~94G   a 94S routine file whose name is a 94G label, in a 94S folder that is not that 94G file
  94S~93S   a 94S routine that is also a 93S routine, placed differently from 93S where 94G does not explain it
            (94G puts it where 93S does, or 94G does not have it)
  93S~93G   a 93S routine in a module folder that is not its 93G file
  93S-area  a 93S routines/hockey/<area>/ routine whose 94G file is not the one the area is named after
  lineage   a 93S or 94S name that 94G renamed (94G docs/name_map.csv old -> new) while 94G has the new name
  stale94   a text file in any repo that still names a 94G file that no longer exists (checks94, input94, ...)
  95S~95G   a 95S routine file whose name is a 95G label, in a 95S folder that is not that 95G file (95S mirrors 95G:
            routines/engine/collide/ is engine/collide95.asm, routines/hockey/ is hockey95.asm)
  95S~94S   a 95S routine with no 95G partner that is also a 94S routine, not in the 94S folder (read as the 95G file of
            that name when 95G has one: 94S video/ is 95S engine/video/)
Lines in tools/pair_exceptions.csv (count,name,reason) are left out of a count on purpose. For lineage the name is
'<game> <old name>', for the others the routine file stem.

  python3 tools/test_pairs.py                    # sources in .cache/src (run generate.py first)
  python3 tools/test_pairs.py --src ~/work       # sibling checkouts instead (DIR/<repo>)
  python3 tools/test_pairs.py --list 94S~94G     # show the routines behind one count
  python3 tools/test_pairs.py --write-baseline   # after a step lowers a count
"""
import argparse, collections, csv, glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPOS = {'92G': 'NHL92Genesis', '93G': 'NHLPA93Genesis', '94G': 'NHL94Genesis', '95G': 'NHL95Genesis',
         '96G': 'NHL96Genesis', '93S': 'NHLPA93SNES', '94S': 'NHL94SNES', '95S': 'NHL95SNES',
         '94PC': 'NHL94PC', '95PC': 'NHL95PC', '96PC': 'NHL96PC'}
GENESIS = ('92G', '93G', '94G', '95G', '96G')
SNES = ('93S', '94S')
# 94G files merged on 2026-10-31 (NHL94Genesis 0fe607c): checks/assign/input -> logic94, data/attract -> setup94,
# old video94 -> middle94, display94 -> video94.
STALE94 = re.compile(r'\b(checks94|assign94|input94|attract94|data94|display94)(\.asm)?\b')
# 93S hockey/<area> -> 94G file key the area is named after
AREA_KEY = {'game': 'hockey', 'password': 'setup', 'playoffs': 'setup'}

def year_key(name):
    b = os.path.splitext(os.path.basename(name))[0].lower()
    m = re.match(r'^(.+?)9[2-6](?:snes|s)?(?:_.*)?$', b)
    return m.group(1) if m else b

def genesis_labels(d):
    """lowercase label -> top-level source file (sega/, sound/, segacd/, macros/ and ram files skipped)."""
    out = {}
    for p in sorted(glob.glob(os.path.join(d, 'src', '*.asm'))):
        if os.path.basename(p).lower().startswith('ram'):
            continue
        for line in open(p, encoding='latin-1'):
            m = re.match(r'^([A-Za-z_]\w*)\b(.*)', line)
            if not m:
                continue
            rest = m.group(2).lstrip(': \t').lower()
            if re.match(r'(equ|=|rs|set|macro|equr|reg)\b', rest) or rest.startswith('='):
                continue
            out.setdefault(m.group(1).lower(), os.path.basename(p))
    return out

def genesis_symbols(d):
    out = set()
    for p in glob.glob(os.path.join(d, 'src', '**', '*.asm'), recursive=True):
        if '/segacd/' in p.replace('\\', '/'):
            continue
        for line in open(p, encoding='latin-1'):
            m = re.match(r'^([A-Za-z_]\w*)\b', line)
            if m:
                out.add(m.group(1).lower())
    return out

def genesis95_labels(d):
    """lowercase label -> 95G file key ('engine/collide', 'front/season', 'hockey'); sega/, sound/ and the RAM file
    are left out (SNES jobs follow 94S, not 95G)."""
    out = {}
    for p in sorted(glob.glob(os.path.join(d, 'src', '**', '*.asm'), recursive=True)):
        rel = os.path.relpath(p, os.path.join(d, 'src')).replace('\\', '/')
        parts = rel.split('/')
        if (len(parts) == 2 and parts[0] not in ('engine', 'front')) or len(parts) > 2 or parts[-1].lower().startswith('ram'):
            continue
        key = '/'.join(parts[:-1] + [year_key(parts[-1])])
        for line in open(p, encoding='latin-1'):
            m = re.match(r'^([A-Za-z_]\w*)\b(.*)', line)
            if not m:
                continue
            rest = m.group(2).lstrip(': \t').lower()
            if re.match(r'(equ|=|rs|set|macro|equr|reg)\b', rest) or rest.startswith('='):
                continue
            out.setdefault(m.group(1).lower(), key)
    return out

def snes95_key(rel):
    """95S routine path below src/routines -> its 95G file key (two parts under engine/ and front/, else one)."""
    parts = rel.split('/')
    return '/'.join(parts[:2]) if parts[0] in ('engine', 'front') and len(parts) > 2 else parts[0]

def snes_routines(d):
    """lowercase routine stem -> path below src/routines (one routine per file)."""
    base = os.path.join(d, 'src', 'routines')
    out = {}
    for p in sorted(glob.glob(os.path.join(base, '**', '*.asm'), recursive=True)):
        rel = os.path.relpath(p, base).replace('\\', '/')
        out.setdefault(os.path.splitext(os.path.basename(p))[0].lower(), rel)
    return out

def snes_symbols(d):
    out = set()
    for p in glob.glob(os.path.join(d, 'src', '**', '*.*'), recursive=True):
        if not p.endswith(('.asm', '.inc', '.mac')):
            continue
        for line in open(p, encoding='latin-1'):
            m = re.match(r'^([A-Za-z_]\w*)(:|\s*=)', line)
            if m:
                out.add(m.group(1).lower())
    return out

class Alias:
    def __init__(self):
        self.par = {}
    def find(self, x):
        while self.par.get(x, x) != x:
            x = self.par[x]
        return x
    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            lo, hi = sorted((a, b))
            self.par[hi] = lo
    def same(self, a, b):
        return a == b or self.find(a) == self.find(b)

def name_maps(dirs):
    """Union of every old/new pair in docs/name_map.csv and docs/history/name_map.csv (Genesis and 93S style)."""
    al, renames94 = Alias(), []
    for gid, d in dirs.items():
        for rel in ('docs/name_map.csv', 'docs/history/name_map.csv'):
            p = os.path.join(d, rel)
            if not os.path.isfile(p):
                continue
            for r in csv.DictReader(open(p, encoding='utf-8', errors='replace', newline='')):
                if 'old' in r and 'new' in r:
                    a, b = (r.get('old') or '').strip().lower(), (r.get('new') or '').strip().lower()
                elif 'old_name' in r:
                    a, b = (r.get('old_name') or '').strip().lower(), (r.get('name') or '').strip().lower()
                else:
                    continue
                if not a or not b or a == b or a.startswith('(') or a == 'old':
                    continue
                al.union(a, b)
                if gid == '94G' and rel == 'docs/name_map.csv':
                    renames94.append((a, b))
    return al, renames94

def stale_files(dirs):
    hits = []
    for gid, d in sorted(dirs.items()):
        for p in glob.glob(os.path.join(d, '**', '*'), recursive=True):
            rp = os.path.relpath(p, d).replace('\\', '/')
            if not os.path.isfile(p) or rp.startswith(('.git/', 'output/', 'Extracted/', 'lst/', 'node_modules/')):
                continue
            if not rp.endswith(('.md', '.csv', '.json', '.txt', '.asm', '.inc', '.py', '.js', '.c', '.h', '.mdc')):
                continue
            try:
                s = open(p, encoding='utf-8', errors='replace').read()
            except OSError:
                continue
            if STALE94.search(s):
                # 94G's own name map and segment-matching history (SEGMENT_AGENT.md) keep the old names on purpose
                # name maps, rules and the plan name the old files on purpose
                if rp in ('docs/name_map.csv', 'docs/RULES.md') or rp.startswith(('docs/ALIGNMENT', 'docs/project/')) \
                        or (gid == 'report' and rp == 'tools/test_pairs.py') \
                        or (gid == '94G' and rp == 'SEGMENT_AGENT.md'):
                    continue
                hits.append(f'{gid}:{rp}')
    return hits

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', help='directory holding the repos (default .cache/src)')
    ap.add_argument('--list', action='append', default=[], help='print the items behind a count')
    ap.add_argument('--write-baseline', action='store_true')
    ap.add_argument('--report-dir', default=ROOT, help='this repo (for the stale-name scan)')
    a = ap.parse_args()
    src = a.src or os.path.join(ROOT, '.cache', 'src')
    dirs = {g: os.path.join(src, r) for g, r in REPOS.items() if os.path.isdir(os.path.join(src, r))}
    for need in ('93G', '94G', '93S', '94S'):
        if need not in dirs:
            sys.exit(f'{REPOS[need]} not found under {src}')
    al, renames94 = name_maps(dirs)
    g93, g94 = genesis_labels(dirs['93G']), genesis_labels(dirs['94G'])
    s93, s94 = snes_routines(dirs['93S']), snes_routines(dirs['94S'])
    sym = {g: (genesis_symbols(dirs[g]) if g in GENESIS else snes_symbols(dirs[g])) for g in ('93G', '94G', '93S', '94S')}

    def lookup(labels, n):
        if n in labels:
            return labels[n]
        for k, v in labels.items():
            if al.same(k, n):
                return v
        return None

    exc = collections.defaultdict(set)
    p = os.path.join(ROOT, 'tools', 'pair_exceptions.csv')
    if os.path.isfile(p):
        for r in csv.DictReader(open(p, encoding='utf-8', newline='')):
            exc[r['count'].strip()].add(r['name'].strip().lower())

    items = collections.OrderedDict((k, []) for k in ('94S~94G', '94S~93S', '93S~93G', '93S-area', 'lineage', 'stale94',
                                                      '95S~95G', '95S~94S'))
    if '95S' in dirs and '95G' in dirs:
        g95, s95 = genesis95_labels(dirs['95G']), snes_routines(dirs['95S'])
        g95keys = sorted(set(g95.values()))
        def map94(top):
            # a 94S folder named like a 95G file is that 95G file (video -> engine/video, main -> main)
            hit = [k for k in g95keys if k.split('/')[-1] == top]
            return hit[0] if hit else top
        for n, rel in s95.items():
            f95 = lookup(g95, n)
            if f95 and f95 != snes95_key(rel):
                items['95S~95G'].append(f'{rel} (95G {f95})')
            elif not f95 and n in s94 and map94(s94[n].split('/')[0]) != snes95_key(rel):
                items['95S~94S'].append(f'{rel} (94S {s94[n]})')
    for n, rel in s94.items():
        top = rel.split('/')[0]
        f94 = lookup(g94, n)
        if f94 and year_key(f94) != top:
            items['94S~94G'].append(f'{rel} (94G {f94})')
        if n in s93:
            p93 = s93[n].split('/')
            # 93S hockey/<area>/: since B2 each area is named after one 94G file
            m93 = AREA_KEY.get(p93[1], p93[1]) if p93[0] == 'hockey' and len(p93) > 2 else p93[0]
            if top != m93 and (not f94 or year_key(f94) == m93):
                items['94S~93S'].append(f'{rel} (93S {s93[n]})')
    for n, rel in s93.items():
        parts = rel.split('/')
        f93 = lookup(g93, n)
        if f93 and year_key(f93) != parts[0]:
            items['93S~93G'].append(f'{rel} (93G {f93})')
        if parts[0] == 'hockey' and len(parts) > 2:
            f94 = lookup(g94, n)
            if f94 and AREA_KEY.get(parts[1], parts[1]) != year_key(f94):
                items['93S-area'].append(f'{rel} (94G {f94})')
    for old, new in renames94:
        if new in sym['94G']:
            for gid in SNES:
                if old in sym[gid] and new not in sym[gid]:
                    items['lineage'].append(f'{gid} {old} (94G {new})')
    sdirs = dict(dirs)
    sdirs['report'] = a.report_dir
    items['stale94'] = stale_files(sdirs)
    for k in items:
        def key_of(x):
            if k == 'lineage':
                return ' '.join(x.split(' ')[:2]).lower()
            return x.split(' ')[0].split('/')[-1].replace('.asm', '').lower()
        items[k] = sorted(x for x in items[k] if key_of(x) not in exc[k])

    fails = []
    kp = os.path.join(ROOT, 'tools', 'known_pairs.csv')
    pairs = list(csv.DictReader(open(kp, encoding='utf-8', newline=''))) if os.path.isfile(kp) else []
    allsym = dict(sym)
    for r in pairs:
        ga, na, gb, nb = r['a_game'], r['a_name'].lower(), r['b_game'], r['b_name'].lower()
        for g in (ga, gb):
            if g not in allsym and g in dirs:
                allsym[g] = genesis_symbols(dirs[g]) if g in GENESIS else snes_symbols(dirs[g])
        if ga not in allsym or gb not in allsym:
            fails.append(f'known pair {ga}:{na} ~ {gb}:{nb}: repo missing')
        elif na not in allsym[ga]:
            fails.append(f'known pair {ga}:{na} ~ {gb}:{nb}: {na} is gone from {ga}')
        elif nb not in allsym[gb]:
            fails.append(f'known pair {ga}:{na} ~ {gb}:{nb}: {nb} is gone from {gb}')
        elif not al.same(na, nb):
            fails.append(f'known pair {ga}:{na} ~ {gb}:{nb}: names differ and no name map links them')

    counts = {k: len(v) for k, v in items.items()}
    bp = os.path.join(ROOT, 'tools', 'baseline.json')
    base = json.load(open(bp)) if os.path.isfile(bp) else {}
    print(f'{"count":10} {"now":>5} {"baseline":>8}')
    for k, v in counts.items():
        b = base.get(k)
        flag = ''
        if b is not None and v > b and not a.write_baseline:
            flag = '  UP'
            fails.append(f'{k}: {v} > baseline {b} (run with --list {k})')
        print(f'{k:10} {v:5} {"" if b is None else b:>8}{flag}')
    print(f'known pairs: {len(pairs)} checked')
    for k in a.list:
        print(f'\n{k}:')
        for x in items.get(k, []):
            print('  ' + x)
    if a.write_baseline:
        with open(bp, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(counts, fh, indent=1, sort_keys=True)
            fh.write('\n')
        print('baseline written')
    if fails:
        print('\nPAIRING FAILED')
        for f in fails:
            print('  ' + f)
        sys.exit(1)
    print('PAIRING OK')

if __name__ == '__main__':
    main()
