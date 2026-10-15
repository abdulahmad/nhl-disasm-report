#!/usr/bin/env python3
"""Generate the NHL disassembly origin report into docs/.

Stdlib only. Shallow-clones (or updates) the source repos into .cache/src at
origin/main, READ-ONLY, then writes docs/index.html and docs/data/<game>.js.
Same source SHAs => byte-identical output.

  python3 tools/generate.py            # fetch latest main of every source repo, regenerate
  python3 tools/generate.py --offline  # use the cache as is (no network)
"""
import argparse, collections, csv, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, '.cache', 'src')
DOCS = os.path.join(ROOT, 'docs')
OWNER = 'abdulahmad'

# id, repo, platform, top-level source (Genesis) relative to src/
GAMES = [
    ('92G', 'NHL92Genesis', 'genesis', 'hockey.asm'),
    ('93G', 'NHLPA93Genesis', 'genesis', 'hockey93.asm'),
    ('94G', 'NHL94Genesis', 'genesis', 'nhl94.asm'),
    ('95G', 'NHL95Genesis', 'genesis', 'nhl95.asm'),
    ('96G', 'NHL96Genesis', 'genesis', 'nhl96.asm'),
    ('93S', 'NHLPA93SNES', 'snes', 'nhlpa93snes.asm'),
    ('94S', 'NHL94SNES', 'snes', 'nhl94snes.asm'),
]

def git(*a, cwd=None):
    return subprocess.run(['git', *a], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

def sync(repo, offline):
    d = os.path.join(CACHE, repo)
    url = f'https://github.com/{OWNER}/{repo}.git'
    if not os.path.isdir(os.path.join(d, '.git')):
        if offline:
            sys.exit(f'{repo} not in cache; run without --offline')
        os.makedirs(CACHE, exist_ok=True)
        git('clone', '-q', '--depth', '1', '--branch', 'main', '--single-branch', url, d)
    elif not offline:
        # local cache only: fetch main and move the cache's checkout to it. Nothing is ever pushed.
        git('fetch', '-q', '--depth', '1', 'origin', 'main', cwd=d)
        git('checkout', '-q', '--detach', 'FETCH_HEAD', cwd=d)
    return d, git('rev-parse', 'HEAD', cwd=d)

# ---------------------------------------------------------------- parsing
LBL = re.compile(r'^([A-Za-z_][\w]*)(:?)(?=\s|$|;)(.*)')
NOEMIT = re.compile(r'^\s*(equ|=|set|rs\.?\w*|macro|equr|reg|rsset|rsreset)\b', re.I)
KEYW = {'include', 'endm', 'end', 'if', 'else', 'endc', 'endif', 'incsrc', 'incbin', 'org', 'macro', 'endmacro'}

def read(p):
    with open(p, encoding='latin-1', newline='') as fh:
        return fh.read().replace('\r\n', '\n').replace('\r', '\n').split('\n')

def label_starts(L):
    out = []
    for i, l in enumerate(L):
        m = LBL.match(l)
        if m and not NOEMIT.match(m.group(3)) and m.group(1).lower() not in KEYW:
            out.append((i, m.group(1)))
    return out

def resolve(base, rel):
    """Case-insensitive path resolution (the sources come from Windows builds)."""
    cur = base
    for part in rel.replace('\\', '/').split('/'):
        if part in ('', '.'):
            continue
        if part == '..':
            cur = os.path.dirname(cur); continue
        nxt = os.path.join(cur, part)
        if not os.path.exists(nxt) and os.path.isdir(cur):
            hit = [x for x in sorted(os.listdir(cur)) if x.lower() == part.lower()]
            if not hit:
                return None
            nxt = os.path.join(cur, hit[0])
        cur = nxt
    return cur if os.path.isfile(cur) else None

def unit(name, names, lines, kind):
    return {'n': name, 'm': sorted(set(x.lower() for x in names)), 't': '\n'.join(lines), 'k': kind}

INC = re.compile(r'^\s*include\s+"?([^\s";]+)"?\s*(?:;\s*(\$[0-9A-Fa-f]+)(?:\s*-\s*(\$[0-9A-Fa-f]+))?)?', re.I)

def doc_ranges(repo_dir):
    """file -> (min addr, max end) from docs/function_origins.csv (file,address,size), when a repo has one."""
    p = os.path.join(repo_dir, 'docs', 'function_origins.csv')
    out = {}
    if os.path.isfile(p):
        with open(p, encoding='utf-8', errors='replace', newline='') as fh:
            for r in csv.DictReader(fh):
                try:
                    a = int((r.get('address') or '').strip().lstrip('$'), 16); n = int((r.get('size') or '0').strip() or 0)
                except ValueError:
                    continue
                f = (r.get('file') or '').strip().replace('\\', '/').lower()
                lo, hi = out.get(f, (a, a + max(n, 1) - 1))
                out[f] = (min(lo, a), max(hi, a + max(n, 1) - 1))
    return out

def fill_ranges(files, docr):
    """a = start, e = end, r = how it was derived. Explicit include comment > docs CSV > next file's start - 1.
    A file that includes others is widened to cover them."""
    for f in files:
        f['r'] = 'include comment' if f['a'] is not None else None
        if f['a'] is None and f['f'].lower() in docr:
            f['a'], f['e'] = docr[f['f'].lower()]; f['r'] = 'docs/function_origins.csv'
    for i, f in enumerate(files):
        if f['a'] is not None and f.get('e') is None:
            nxt = [g['a'] for g in files[i + 1:] if g['a'] is not None and g['a'] > f['a']]
            if nxt:
                f['e'] = nxt[0] - 1; f['r'] += '; end = next file start - 1'
    for i in range(len(files) - 1, -1, -1):
        f, d = files[i], files[i]['d']
        for g in files[i + 1:]:
            if g['d'] <= d:
                break
            if g['a'] is not None and g.get('e') is not None:
                if f['a'] is None or g['a'] < f['a']:
                    f['a'] = g['a']; f['r'] = 'covers its includes'
                if f.get('e') is None or g['e'] > f['e']:
                    f['e'] = g['e']
    for f in files:
        f.setdefault('e', None)

def genesis(src, top, docr):
    """Files in include order (pre-order walk from the top-level file). Units = label segments."""
    files, seen = [], set()
    def walk(p, addr, end, depth):
        rp = os.path.relpath(p, src).replace('\\', '/')
        if rp.lower() in seen:
            return
        seen.add(rp.lower())
        L = read(p)
        st = label_starts(L)
        entry = None
        incs = [m for m in map(INC.match, L) if m and m.group(1).lower().replace('\\', '/').endswith('.asm')
                and not m.group(1).lower().replace('\\', '/').startswith(('macros/', 'stubinc/'))]
        if not st and incs and depth >= 0 and p != os.path.join(src, top):
            entry = {'f': rp, 'a': addr, 'e': end, 'd': depth, 'u': []}  # include list only, kept so nesting shows
            files.append(entry)
        if st:
            us = []
            if st[0][0] > 0:
                us.append(unit('(file header)', [], L[:st[0][0]], 'pre'))
            for j, (i, n) in enumerate(st):
                e = st[j + 1][0] if j + 1 < len(st) else len(L)
                us.append(unit(n, [n], L[i:e], 'code'))
            entry = {'f': rp, 'a': addr, 'e': end, 'd': depth, 'u': us}
            files.append(entry)
        for l in L:
            m = INC.match(l)
            if not m:
                continue
            inc = m.group(1)
            low = inc.lower().replace('\\', '/')
            if not low.endswith('.asm') or low.startswith(('macros/', 'stubinc/')):
                continue
            q = resolve(src, inc)
            if q:
                walk(q, int(m.group(2)[1:], 16) if m.group(2) else None, int(m.group(3)[1:], 16) if m.group(3) else None, depth + (1 if entry else 0))
    walk(os.path.join(src, top), None, None, 0)
    fill_ranges(files, docr)
    return {'files': files}

INCSRC = re.compile(r'^\s*incsrc\s+"([^"]+)"', re.I)

def snes(src, top):
    """Two views: routine groups (src/routines/<group>/*.asm) and banks (src/banks/*.asm include lists)."""
    units, byfile = [], {}
    def file_unit(p):
        rp = os.path.relpath(p, src).replace('\\', '/')
        if rp not in byfile:
            L = read(p)
            stem = os.path.splitext(os.path.basename(p))[0]
            names = [stem] + [n for _, n in label_starts(L)]
            byfile[rp] = len(units)
            units.append(dict(unit(stem, names, L, 'routine' if rp.startswith('routines/') else 'data'), p=rp))
        return byfile[rp]
    banks = []
    for l in read(os.path.join(src, top)):
        m = INCSRC.match(l)
        if m and m.group(1).replace('\\', '/').startswith('banks/'):
            bp = resolve(src, m.group(1))
            if not bp:
                continue
            ids, pend, orgs = [], [], []
            def flush():
                body = [x for x in pend if x.strip() and not x.strip().startswith(';')]
                if body:
                    k = 'bin' if any(re.match(r'\s*incbin\b', x, re.I) for x in body) else 'inline'
                    rp = os.path.relpath(bp, src).replace('\\', '/')
                    units.append(dict(unit('(%s in %s)' % ('incbin' if k == 'bin' else 'inline', os.path.basename(bp)), [], pend, k), p=rp))
                    ids.append(len(units) - 1)
                pend.clear()
            for bl in read(bp):
                mo = re.match(r'\s*org\s+\$([0-9A-Fa-f]+)', bl, re.I)
                if mo:
                    orgs.append(int(mo.group(1), 16))
                mm = INCSRC.match(bl)
                q = resolve(os.path.dirname(bp), mm.group(1)) if mm else None
                if q:
                    flush(); ids.append(file_unit(q))
                else:
                    pend.append(bl)
            flush()
            banks.append({'f': os.path.relpath(bp, src).replace('\\', '/'), 'a': min(orgs) if orgs else None,
                          'e': (max(orgs) | 0x7FFF) if orgs else None, 'd': 0, 'r': 'org line, LoROM bank end' if orgs else None, 'u': ids})
    # routine groups, ordered by first appearance in the banks; never-included files last
    rdir = os.path.join(src, 'routines')
    allr = []
    if os.path.isdir(rdir):
        for dp, dn, fn in os.walk(rdir):
            dn.sort()
            for x in sorted(fn):
                if x.lower().endswith('.asm'):
                    allr.append(os.path.join(dp, x))
    order = {}
    for b in banks:
        for i in b['u']:
            order.setdefault(i, len(order))
    for p in allr:
        file_unit(p)
    grp = collections.OrderedDict()
    for i in sorted((i for i, u in enumerate(units) if u['k'] == 'routine'), key=lambda i: (order.get(i, 1 << 30), units[i]['p'])):
        g = os.path.dirname(units[i]['p'])
        grp.setdefault(g, []).append(i)
    inbank = collections.defaultdict(set)
    for b in banks:
        for i in b['u']:
            if b['a'] is not None:
                inbank[i].add(b['a'] >> 16)
    groups = [{'f': g + '/', 'a': None, 'e': None, 'd': 0, 'r': None, 'bk': sorted({x for i in ids for x in inbank[i]}), 'u': ids} for g, ids in sorted(grp.items(), key=lambda kv: (order.get(kv[1][0], 1 << 30), kv[0]))]
    return {'units': units, 'groups': groups, 'banks': banks}

# ---------------------------------------------------------------- name maps
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
    def finish(self):
        self.grp = collections.defaultdict(set)
        for k in list(self.par) + list(self.par.values()):
            self.grp[self.find(k)].add(k)
    def of(self, n):
        return self.grp.get(self.find(n), set()) | {n}

def load_maps(dirs):
    al, used = Alias(), []
    for gid, d in dirs:
        p = os.path.join(d, 'docs', 'name_map.csv')
        if not os.path.isfile(p):
            continue
        with open(p, encoding='utf-8', errors='replace', newline='') as fh:
            rows = list(csv.DictReader(fh))
        pairs = 0
        for r in rows:
            if 'old' in r and 'new' in r:
                a, b = (r.get('old') or '').strip().lower(), (r.get('new') or '').strip().lower()
            elif 'old_name' in r:
                a, b = (r.get('old_name') or '').strip().lower(), (r.get('name') or '').strip().lower()
            else:
                continue  # SNES maps: address -> name only, no lineage column
            if a and b and a != b:
                al.union(a, b); pairs += 1
        used.append((gid, pairs))
    al.finish()
    return al, used

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--offline', action='store_true', help='do not fetch; use .cache/src as is')
    a = ap.parse_args()
    meta, data, dirs = [], {}, []
    for gid, repo, plat, top in GAMES:
        d, sha = sync(repo, a.offline)
        dirs.append((gid, d))
        src = os.path.join(d, 'src')
        g = genesis(src, top, doc_ranges(d)) if plat == 'genesis' else snes(src, top)
        data[gid] = g
        meta.append({'id': gid, 'repo': repo, 'plat': plat, 'sha': sha})
    al, used = load_maps(dirs)

    # comparison targets: name -> set(file) indexes
    targets = collections.OrderedDict()
    for m in meta:
        g, gid = data[m['id']], m['id']
        if m['plat'] == 'genesis':
            idx = collections.defaultdict(set)
            for f in g['files']:
                for u in f['u']:
                    for n in u['m']:
                        idx[n].add(f['f'])
            targets[gid] = (gid, idx)
        else:
            for view in ('groups', 'banks'):
                idx = collections.defaultdict(set)
                for f in g[view]:
                    for i in f['u']:
                        for n in g['units'][i]['m']:
                            idx[n].add(f['f'])
                targets[f'{gid}:{view}'] = (gid, idx)

    def origins(names, idx):
        hit = set()
        for n in names:
            for x in al.of(n):
                hit |= idx.get(x, set())
        return sorted(hit)

    os.makedirs(os.path.join(DOCS, 'data'), exist_ok=True)
    for m in meta:
        gid, g = m['id'], data[m['id']]
        if m['plat'] == 'genesis':
            units = [u for f in g['files'] for u in f['u']]
            views = {'files': []}
            k = 0
            for f in g['files']:
                views['files'].append({'f': f['f'], 'a': f['a'], 'e': f['e'], 'd': f['d'], 'r': f['r'], 'u': list(range(k, k + len(f['u'])))})
                k += len(f['u'])
        else:
            units = g['units']
            views = {'groups': g['groups'], 'banks': g['banks']}
        tg = collections.OrderedDict()
        for tid, (owner, idx) in targets.items():
            if owner == gid:
                continue
            names = sorted({o for u in units for o in origins(u['m'], idx)})
            pos = {n: i for i, n in enumerate(names)}
            tg[tid] = {'files': names, 'o': [[pos[o] for o in origins(u['m'], idx)] if u['m'] else None for u in units]}
        out = {'id': gid, 'units': [{'n': u['n'], 't': u['t'], 'k': u['k'], **({'p': u['p']} if 'p' in u else {})} for u in units],
               'views': views, 'targets': tg}
        js = 'NDR.loaded(' + json.dumps(out, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + ');\n'
        with open(os.path.join(DOCS, 'data', gid + '.js'), 'w', encoding='ascii', newline='\n') as fh:
            fh.write(js)
        m['units'] = len(units)
        m['views'] = {v: len(fs) for v, fs in sorted(views.items())}
    manifest = {'games': meta, 'targets': list(targets), 'maps': used}
    tpl = open(os.path.join(ROOT, 'tools', 'template.html'), encoding='utf-8').read()
    html = tpl.replace('/*MANIFEST*/null', json.dumps(manifest, sort_keys=True, separators=(',', ':')))
    with open(os.path.join(DOCS, 'index.html'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(html)
    open(os.path.join(DOCS, '.nojekyll'), 'w').close()
    for m in meta:
        print(f"{m['id']:4} {m['repo']:16} {m['sha'][:10]} units={m['units']} views={m['views']}")

if __name__ == '__main__':
    main()
