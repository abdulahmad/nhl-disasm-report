#!/usr/bin/env python3
"""Generate the NHL disassembly origin report into docs/.

Stdlib + node (for tools/classify_routines.js). Shallow-clones (or updates)
the source repos into .cache/src at origin/main, READ-ONLY, then writes
docs/index.html and docs/data/<game>.js. Classifies 93G/94G routines into
categories (heuristic). Same source SHAs => byte-identical output.

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
    Include-list-only parents (no units) are widened to cover their children; code segments are not."""
    for f in files:
        f['r'] = 'include comment' if f['a'] is not None else None
        if f['a'] is None and f['f'].lower() in docr:
            f['a'], f['e'] = docr[f['f'].lower()]; f['r'] = 'docs/function_origins.csv'
    # Start from the immediate previous end only (do not jump over siblings).
    for i, f in enumerate(files):
        if f['a'] is None and i > 0 and files[i - 1].get('e') is not None:
            f['a'] = files[i - 1]['e'] + 1
            f['r'] = (f['r'] or '') + '; start = prev end + 1'
    # End from the next known start, but stop if an intervening band already has an end.
    for i, f in enumerate(files):
        if f['a'] is not None and f.get('e') is None:
            for g in files[i + 1:]:
                if g['a'] is not None:
                    if g['a'] > f['a']:
                        f['e'] = g['a'] - 1
                        f['r'] = (f['r'] or '') + '; end = next file start - 1'
                    break
                if g.get('e') is not None:
                    break
    for i in range(len(files) - 1, -1, -1):
        f, d = files[i], files[i]['d']
        if f['u']:
            continue  # code / data segments keep their own range; do not swallow includes
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
    """Files in ROM/include order from the top-level file.

    Hub files (93G hockey93.asm, 92G hockey.asm) interleave their own code with
    includes: each include is emitted at depth+1 where it appears, and the
    parent's own label segments between includes are separate bands at the
    parent's depth. Include-list-only files (e.g. 95G engine95.asm) stay as an
    empty parent band covering their children. stubinc/ and macros/ are skipped.
    """
    files, seen = [], set()
    top_path = os.path.join(src, top)

    def is_rom_include(m):
        if not m:
            return False
        low = m.group(1).lower().replace('\\', '/')
        return low.endswith('.asm') and not low.startswith(('macros/', 'stubinc/'))

    def units_from_lines(lines):
        st = label_starts(lines)
        if not st:
            return []
        us = []
        if st[0][0] > 0:
            us.append(unit('(file header)', [], lines[:st[0][0]], 'pre'))
        for j, (i, n) in enumerate(st):
            e = st[j + 1][0] if j + 1 < len(st) else len(lines)
            us.append(unit(n, [n], lines[i:e], 'code'))
        return us

    def walk(p, addr, end, depth, first_child_addr=None):
        rp = os.path.relpath(p, src).replace('\\', '/')
        if rp.lower() in seen:
            return
        seen.add(rp.lower())
        L = read(p)
        rom_incs = [(i, m) for i, m in ((i, INC.match(L[i])) for i in range(len(L))) if is_rom_include(m)]
        st = label_starts(L)

        if not st:
            child_depth = depth if p == top_path else depth + 1
            if p != top_path and rom_incs:
                files.append({'f': rp, 'a': addr, 'e': end, 'd': depth, 'u': []})
            first = True
            for _, m in rom_incs:
                ia = int(m.group(2)[1:], 16) if m.group(2) else None
                ie = int(m.group(3)[1:], 16) if m.group(3) else None
                if ia is None and first and first_child_addr is not None:
                    ia = first_child_addr
                first = False
                q = resolve(src, m.group(1))
                if q:
                    walk(q, ia, ie, child_depth)
            return

        child_depth = depth + 1
        chunk_start = 0
        pending_start = addr  # start address for the next emitted parent segment
        emitted_own = False
        first_inc = True

        def flush(chunk_end, next_inc_addr):
            nonlocal pending_start, emitted_own, chunk_start
            lines = L[chunk_start:chunk_end]
            us = units_from_lines(lines)
            if not us:
                # No labels: glue non-empty trailing source onto the previous segment of this file.
                if emitted_own and files and files[-1]['f'] == rp and files[-1]['u'] and any(x.strip() for x in lines):
                    files[-1]['u'][-1]['t'] += '\n' + '\n'.join(lines)
                chunk_start = chunk_end
                return
            if next_inc_addr is not None:
                if pending_start is not None and next_inc_addr <= pending_start:
                    seg_end = None  # label sits at the same address as the following include
                else:
                    seg_end = next_inc_addr - 1
            else:
                seg_end = end
            files.append({'f': rp, 'a': pending_start, 'e': seg_end, 'd': depth, 'u': us})
            emitted_own = True
            pending_start = None
            chunk_start = chunk_end

        for li, m in rom_incs:
            ia = int(m.group(2)[1:], 16) if m.group(2) else None
            ie = int(m.group(3)[1:], 16) if m.group(3) else None
            if ia is None and first_inc and first_child_addr is not None:
                ia = first_child_addr
            first_inc = False
            flush(li, ia)
            q = resolve(src, m.group(1))
            if q:
                walk(q, ia, ie, child_depth)
            # Only the segment immediately after an include with a known end inherits ie+1.
            pending_start = (ie + 1) if ie is not None else None
            chunk_start = li + 1
        flush(len(L), None)

        if not emitted_own and not rom_incs:
            us = units_from_lines(L)
            if us:
                files.append({'f': rp, 'a': addr, 'e': end, 'd': depth, 'u': us})

    walk(top_path, None, None, 0, first_child_addr=0)
    fill_ranges(files, docr)
    return {'files': files}


INCSRC = re.compile(r'^\s*incsrc\s+"([^"]+)"', re.I)

def snes(src, top):
    """Two views: routine groups (src/routines/<group>/*.asm) and banks (src/banks/*.asm include lists).

    Groups: each subfolder of src/routines is a FILE; each .asm in that folder is a ROUTINE
    named by its stem. Nested subfolders are nested files (depth +1). Group order follows the
    first bank-include appearance of any routine in the folder, else alphabetical.
    Matching for routine units is by .asm stem only (not every label in the file).
    """
    units, byfile = [], {}
    def file_unit(p):
        rp = os.path.relpath(p, src).replace('\\', '/')
        if rp not in byfile:
            L = read(p)
            stem = os.path.splitext(os.path.basename(p))[0]
            # Routines match on the .asm stem only; other bank payloads keep labels too.
            if rp.startswith('routines/'):
                names = [stem]
                kind = 'routine'
            else:
                names = [stem] + [n for _, n in label_starts(L)]
                kind = 'data'
            byfile[rp] = len(units)
            units.append(dict(unit(stem, names, L, kind), p=rp))
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
    # All routine .asm files under src/routines/
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

    # Direct .asm members per folder; also keep ancestor folders for nesting.
    direct = collections.OrderedDict()
    folders = set()
    for i, u in enumerate(units):
        if u['k'] != 'routine':
            continue
        g = os.path.dirname(u['p']).replace('\\', '/').rstrip('/')
        direct.setdefault(g, []).append(i)
        # ancestors under routines/ (inclusive)
        parts = g.split('/')
        for k in range(2, len(parts) + 1):  # routines/X, routines/X/Y, ...
            folders.add('/'.join(parts[:k]))
    for g in sorted(folders):
        direct.setdefault(g, [])

    def folder_depth(g):
        # routines/hockey -> 0; routines/hockey/sub -> 1
        return max(0, len(g.split('/')) - 2)

    def folder_order_key(g):
        ids = direct.get(g) or []
        if ids:
            return (min(order.get(i, 1 << 30) for i in ids), g)
        # empty parent: earliest child order, else alpha
        child_keys = [folder_order_key(c) for c in folders if c.startswith(g + '/') and c.count('/') == g.count('/') + 1]
        if child_keys:
            return (min(k[0] for k in child_keys), g)
        return (1 << 30, g)

    inbank = collections.defaultdict(set)
    for b in banks:
        for i in b['u']:
            if b['a'] is not None:
                inbank[i].add(b['a'] >> 16)

    groups = []
    for g in sorted(folders, key=folder_order_key):
        ids = sorted(direct[g], key=lambda i: (order.get(i, 1 << 30), units[i]['p']))
        # banks that any direct routine (or, for empty parents, any descendant) appears in
        if ids:
            bset = {x for i in ids for x in inbank[i]}
        else:
            desc = [i for gg, lst in direct.items() if gg.startswith(g + '/') for i in lst]
            bset = {x for i in desc for x in inbank[i]}
        groups.append({
            'f': g + '/', 'a': None, 'e': None, 'd': folder_depth(g), 'r': None,
            'bk': sorted(bset), 'u': ids,
        })
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
    # Categories (93G / 94G): run classifier on the JS we just wrote, merge back.
    cat_meta = None
    cat_js = os.path.join(ROOT, 'tools', 'classify_routines.js')
    if os.path.isfile(cat_js):
        cat_json = os.path.join(DOCS, 'data', '_categories.json')
        subprocess.run(['node', cat_js, '--docs', DOCS, '--out', cat_json], check=True)
        with open(cat_json, encoding='utf-8') as fh:
            cat_data = json.load(fh)
        os.remove(cat_json)
        cat_meta = {
            'order': cat_data.get('order'),
            'colors': cat_data.get('colors'),
            'placement_rule': cat_data.get('placement_rule'),
            'games': sorted(cat_data.get('games', {})),
        }
        for gid, gcat in sorted(cat_data.get('games', {}).items()):
            path = os.path.join(DOCS, 'data', gid + '.js')
            with open(path, encoding='ascii') as fh:
                raw = fh.read()
            payload = json.loads(raw[raw.index('(') + 1:raw.rindex(')')])
            # Compact per-unit: [c,s,confidence,placement,address] or null
            compact = []
            for u in gcat['units']:
                if u is None:
                    compact.append(None)
                else:
                    compact.append([u['c'], u['s'], u['n'], u.get('p') or '', u.get('a') or ''])
            payload['cat'] = {
                'u': compact,
                'summary': {
                    'routines': gcat['summary']['routines'],
                    'lines': gcat['summary']['lines'],
                    'low': gcat['summary']['low'],
                    'yellow': gcat['summary']['yellow'],
                    'red': gcat['summary']['red'],
                    'categories': gcat['summary']['categories'],
                    'files': gcat['summary']['files'],
                },
            }
            js = 'NDR.loaded(' + json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + ');\n'
            with open(path, 'w', encoding='ascii', newline='\n') as fh:
                fh.write(js)
            for m in meta:
                if m['id'] == gid:
                    m['categorised'] = True
                    break
        for m in meta:
            m.setdefault('categorised', False)

    manifest = {'games': meta, 'targets': list(targets), 'maps': used, 'categories': cat_meta}
    tpl = open(os.path.join(ROOT, 'tools', 'template.html'), encoding='utf-8').read()
    html = tpl.replace('/*MANIFEST*/null', json.dumps(manifest, sort_keys=True, separators=(',', ':')))
    with open(os.path.join(DOCS, 'index.html'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(html)
    open(os.path.join(DOCS, '.nojekyll'), 'w').close()
    for m in meta:
        print(f"{m['id']:4} {m['repo']:16} {m['sha'][:10]} units={m['units']} views={m['views']}")

if __name__ == '__main__':
    main()
