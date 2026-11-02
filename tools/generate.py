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
NOEMIT = re.compile(r'^\s*(equ|=|set|rs\.?\w*|macro|equr|reg|rsset|rsreset)(?![\w])', re.I)
KEYW = {'include', 'endm', 'end', 'if', 'else', 'endc', 'endif', 'incsrc', 'incbin', 'org', 'macro', 'endmacro'}

def read(p):
    with open(p, encoding='latin-1', newline='') as fh:
        return fh.read().replace('\r\n', '\n').replace('\r', '\n').split('\n')

# Include tree only: equates are listed as routine-like rows there (the RAM files expand).
# Symbol definitions (`name equ v`, `name = v`, `name set v`, with spaces or tabs, optional `:`) are all
# listed the same way, and so are `name rs.b/w/l n` RAM layout lines (the Genesis RAM files are mostly
# `rs`, the SNES ones `=`; both must be rows or a RAM symbol never matches across platforms).
# Only `==` (a comparison), the bare rs-counter directives and the macro / register forms are excluded.
TREE_NOEMIT = re.compile(r'^\s*(?:(rsset|rsreset|macro|equr|reg)\b|==)', re.I)

def label_starts(L, noemit=NOEMIT):
    out = []
    for i, l in enumerate(L):
        m = LBL.match(l)
        if m and not noemit.match(m.group(3)) and m.group(1).lower() not in KEYW:
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
    named by its stem. Nested subfolders are nested files (depth +1). Bands are contiguous
    one band per folder, ordered by first ROM appearance (module, then its areas); routines inside
    a band stay in ROM order. The banks view is the ROM-order view. Matching for routine units is by .asm stem only.
    """
    units, byfile = [], {}
    def file_unit(p):
        rp = os.path.relpath(p, src).replace('\\', '/')
        if rp not in byfile:
            L = read(p)
            stem = os.path.splitext(os.path.basename(p))[0]
            if rp.startswith('routines/'):
                names, kind = [stem], 'routine'
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

    inbank = collections.defaultdict(set)
    for b in banks:
        for i in b['u']:
            if b['a'] is not None:
                inbank[i].add(b['a'] >> 16)

    def folder_of(i):
        return os.path.dirname(units[i]['p']).replace('\\', '/').rstrip('/')

    def folder_depth(g):
        return max(0, len(g.split('/')) - 2)

    # ROM order: first appearance in banks, then never-included routines alphabetically.
    seen, ordered = set(), []
    for b in banks:
        for i in b['u']:
            if units[i]['k'] == 'routine' and i not in seen:
                ordered.append(i); seen.add(i)
    for i in sorted((i for i, u in enumerate(units) if u['k'] == 'routine' and i not in seen), key=lambda i: units[i]['p']):
        ordered.append(i)

    # One group per folder (no repeats). Folders form a tree under src/routines; siblings are ordered by the first
    # ROM appearance of any routine in their subtree, so a module's areas always sit directly under the module.
    # Routines inside a group stay in ROM order (never-included ones last, by path). The page re-sorts the modules
    # by the comparison game's include order (groups / rom:groups / layout / include tree; see target 'seq', tree 'gb').
    rank = {i: n for n, i in enumerate(ordered)}
    byf = collections.OrderedDict()
    for i in ordered:
        byf.setdefault(folder_of(i), []).append(i)
    first = {}
    for g, ids in byf.items():
        parts = g.split('/')
        for k in range(2, len(parts) + 1):
            a = '/'.join(parts[:k])
            first[a] = min(first.get(a, len(ordered)), rank[ids[0]])
    kids = collections.defaultdict(list)
    for a in first:
        kids['/'.join(a.split('/')[:-1])].append(a)
    groups = []
    def walk(parent):
        for a in sorted(kids.get(parent, []), key=lambda x: (first[x], x)):
            ids = byf.get(a, [])
            bset = {x for i in ids for x in inbank[i]}
            groups.append({'f': a + '/', 'a': None, 'e': None, 'd': folder_depth(a), 'r': None, 'bk': sorted(bset), 'u': ids})
            walk(a)
    walk('routines')
    return {'units': units, 'groups': groups, 'banks': banks}


# ---------------------------------------------------------------- include tree
# Tree nodes (pre-order, source order): [depth, 0, path, kind] for a file (kind '' or 'data'),
# [depth, 1, name, comment, home] for a routine. home = the file the routine is matched as living in
# (Genesis: the file that defines it; SNES: its src/routines/<group>/ folder).
SEP = re.compile(r'^[\s;\-=*_#~+.<>]*$')

def code_comment(s):
    """Text after the first ';' outside quotes, or None."""
    q = None
    for i, c in enumerate(s):
        if q:
            if c == q:
                q = None
        elif c in '\'"':
            q = c
        elif c == ';':
            return s[i + 1:]
    return None

def clean_comment(lines):
    out = [x.strip().lstrip(';').strip() for x in lines]
    out = [x for x in out if x and not SEP.match(x)]
    return '\n'.join(out)

def routine_comment(L, i):
    """Label-line comment plus the pure comment lines straight after it; else the comment block
    straight above the label (no blank line in between)."""
    m = LBL.match(L[i])
    c = code_comment(m.group(3)) if m else None
    if c is not None and c.strip():
        lines = [c]
        j = i + 1
        while j < len(L) and re.match(r'^\s*;', L[j]):
            lines.append(L[j]); j += 1
        t = clean_comment(lines)
        if t:
            return t
    lines, j = [], i - 1
    while j >= 0 and re.match(r'^\s*;', L[j]):
        lines.insert(0, L[j]); j -= 1
    return clean_comment(lines)

LOCAL = re.compile(r'^([.@][A-Za-z_\d][\w]*):?(?=\s|$|;)(.*)')

def label_node(depth, name, rest):
    """[depth, 2, name] or [depth, 2, name, same-line comment] for a label inside a routine."""
    c = code_comment(rest)
    c = clean_comment([c]) if c else ''
    return [depth, 2, name, c] if c else [depth, 2, name]

def tree_genesis(src, top):
    """Root file, then its labels and .asm includes interleaved in source order, recursively.
    Same include rule as the files view: .asm only, macros/ and stubinc/ skipped."""
    nodes, seen = [], set()
    def walk(p, depth):
        rp = os.path.relpath(p, src).replace('\\', '/')
        if rp.lower() in seen:
            return
        seen.add(rp.lower())
        nodes.append([depth, 0, rp, ''])
        L = read(p)
        labels = dict(label_starts(L, TREE_NOEMIT))
        inr = False  # inside a routine: local labels (.x / @x) after it become its children
        for i, l in enumerate(L):
            if i in labels:
                nodes.append([depth + 1, 1, labels[i], routine_comment(L, i), rp])
                inr = True
                continue
            lm = LOCAL.match(l)
            if lm and inr:
                nodes.append(label_node(depth + 2, lm.group(1), lm.group(2)))
                continue
            m = INC.match(l)
            if m:
                inr = False  # a label after an include and before the next routine has no routine above it in the tree
                low = m.group(1).lower().replace('\\', '/')
                if low.endswith('.asm') and not low.startswith(('macros/', 'stubinc/')):
                    q = resolve(src, m.group(1))
                    if q:
                        walk(q, depth + 1)
    walk(os.path.join(src, top), 0)
    return nodes

def snes_routine_nodes(src, q, depth):
    """A src/routines .asm as a routine node (stem, comment, home folder) followed by its other global
    labels and local (.x) labels, in source order."""
    rp = os.path.relpath(q, src).replace('\\', '/')
    stem = os.path.splitext(os.path.basename(q))[0]
    L = read(q)
    st = label_starts(L, TREE_NOEMIT)
    hit = [i for i, n in st if n.lower() == stem.lower()] or [i for i, _ in st]
    cm = routine_comment(L, hit[0]) if hit else clean_comment([x for x in L if re.match(r'^\s*;', x)][:3])
    nodes = [[depth, 1, stem, cm, os.path.dirname(rp) + '/']]
    main = hit[0] if hit else -1
    gl = dict(st)
    for i, l in enumerate(L):
        if i in gl and i != main:
            nodes.append(label_node(depth + 1, gl[i], LBL.match(l).group(3)))
        elif i not in gl:
            lm = LOCAL.match(l)
            if lm:
                nodes.append(label_node(depth + 1, lm.group(1), lm.group(2)))
    return nodes

def snes_data_file_nodes(src, q, depth):
    """A src/data/<x>.asm (teamdata, frames) as a file node with its labels as routines (as a Genesis file),
    local labels under each routine. Matches the Genesis teamdata / frames files by the matching-file rule."""
    rp = os.path.relpath(q, src).replace('\\', '/')
    L = read(q)
    labels = dict(label_starts(L, TREE_NOEMIT))
    nodes = [[depth, 0, rp, '']]
    inr = False
    for i, l in enumerate(L):
        if i in labels:
            nodes.append([depth + 1, 1, labels[i], routine_comment(L, i), rp])
            inr = True
            continue
        lm = LOCAL.match(l)
        if lm and inr:
            nodes.append(label_node(depth + 2, lm.group(1), lm.group(2)))
    return nodes

def is_top_data(rp):
    """src/data/<x>.asm directly in data/ (teamdata, frames); the gfx / sound / text / tables files stay leaves."""
    return rp.startswith('data/') and rp.count('/') == 1

def is_root_equ(rp):
    """An equate file the SNES root includes: the RAM file next to the root, or a src/inc/ file (snes_regs.asm,
    the hardware registers). Listed with its equates as rows."""
    return rp.count('/') == 0 or (rp.startswith('inc/') and rp.count('/') == 1)

def tree_snes(src, top):
    """Banks view. Root file -> its incsrc'd .asm files (macros/ skipped) -> for banks/*.asm, each
    incsrc in order: a src/routines .asm is a routine (stem); any other .asm is a leaf data file.
    Root-level equate files (the RAM file, inc/snes_regs.asm) are files with their equates as rows."""
    nodes = []
    nodes.append([0, 0, top, ''])
    for l in read(os.path.join(src, top)):
        m = INCSRC.match(l)
        if not m:
            continue
        low = m.group(1).lower().replace('\\', '/')
        if not low.endswith('.asm') or low.startswith('macros/'):
            continue
        bp = resolve(src, m.group(1))
        if not bp:
            continue
        brp = os.path.relpath(bp, src).replace('\\', '/')
        if is_root_equ(brp):
            nodes += snes_data_file_nodes(src, bp, 1)  # ram93s.asm, inc/snes_regs.asm: equates as rows, as the Genesis RAM files
            continue
        nodes.append([1, 0, brp, '' if low.startswith('banks/') else 'data'])
        if not low.startswith('banks/'):
            continue
        for bl in read(bp):
            mm = INCSRC.match(bl)
            q = resolve(os.path.dirname(bp), mm.group(1)) if mm else None
            if not q:
                continue
            rp = os.path.relpath(q, src).replace('\\', '/')
            if rp.startswith('routines/'):
                nodes += snes_routine_nodes(src, q, 2)
            elif is_top_data(rp):
                nodes += snes_data_file_nodes(src, q, 2)
            else:
                nodes.append([2, 0, rp, 'data'])
    return nodes

def tree_snes_groups(src, top, g):
    """Routine groups view: root file -> each routine group (a src/routines subfolder, nested folders nest;
    one node per folder as in the report's groups view) -> its routines (stem) and their labels.
    Records g['gb'] = [[start, end, module key]] per module block so the page can re-sort modules by the other pane."""
    nodes = [[0, 0, top, '']]
    for l in read(os.path.join(src, top)):  # root-level equate files (inc/snes_regs.asm, ram93s.asm) first, as in the banks tree
        m = INCSRC.match(l)
        bp = resolve(src, m.group(1)) if m else None
        if bp and m.group(1).lower().endswith('.asm') and is_root_equ(os.path.relpath(bp, src).replace('\\', '/')):
            nodes += snes_data_file_nodes(src, bp, 1)
    blocks = []
    for grp in g['groups']:
        if grp['d'] == 0:
            if blocks:
                blocks[-1][1] = len(nodes)
            blocks.append([len(nodes), None, file_key(grp['f'])])
        nodes.append([1 + grp['d'], 0, grp['f'], ''])
        for i in grp['u']:
            nodes += snes_routine_nodes(src, os.path.join(src, g['units'][i]['p']), 2 + grp['d'])
    if blocks:
        blocks[-1][1] = len(nodes)
    g['gb'] = blocks
    # the data files directly in src/data (teamdata, frames), in bank-include order, after the groups
    for l in read(os.path.join(src, top)):
        m = INCSRC.match(l)
        if not m or not m.group(1).replace('\\', '/').startswith('banks/'):
            continue
        bp = resolve(src, m.group(1))
        for bl in read(bp) if bp else []:
            mm = INCSRC.match(bl)
            q = resolve(os.path.dirname(bp), mm.group(1)) if mm else None
            if q and is_top_data(os.path.relpath(q, src).replace('\\', '/')):
                nodes += snes_data_file_nodes(src, q, 1)
    return nodes

def file_key(f):
    """Matching-file key: last path part, no extension, lowercased, cut at the game year (92-96)
    so stats93 / stats94, logic95 / logic96_ass, SNES teamdata93s / frames94s / ram93snes and routines/logic/ all give 'logic' / 'stats' / 'teamdata' / 'frames'.
    An SNES folder below the module (routines/hockey/collisions/) gives the module key ('hockey'), so every area matches the Genesis file of its module."""
    parts = f.rstrip('/').split('/')
    if parts[0] == 'routines' and len(parts) > 1:
        parts = parts[:2]       # SNES routine folders: the folder under routines (the 93G module) is the file; the areas below it only nest
    b = parts[-1]
    if not f.endswith('/') and len(parts) == len(f.rstrip('/').split('/')):
        b = os.path.splitext(b)[0]
    b = b.lower()
    m = re.match(r'^(.+?)9[2-6](?:snes|s)?(?:_.*)?$', b)
    return m.group(1) if m else b

def seq_of(files):
    """Unique matching-file keys in include / first-ROM-appearance order (the order a groups view should follow)."""
    out, seen = [], set()
    for f in files:
        k = file_key(f['f'])
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


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
            if a.startswith('(') or b.startswith('('):
                continue  # placeholder such as '(raw offset)' or '(new equate)': no predecessor name, not a link
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
        g['tree'] = tree_genesis(src, top) if plat == 'genesis' else tree_snes(src, top)
        if plat == 'snes':
            g['treeg'] = tree_snes_groups(src, top, g)
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

    # include tree: per tree (a Genesis game; an SNES game as banks = its id, or as routine groups = id:groups),
    # for every other tree of another game, where each routine lives there (bold / yellow)
    trees = collections.OrderedDict()
    for m in meta:
        trees[m['id']] = (m['id'], data[m['id']]['tree'])
        if 'treeg' in data[m['id']]:
            trees[m['id'] + ':groups'] = (m['id'], data[m['id']]['treeg'])
    tidx, rnames = {}, {}
    for tid, (owner, nodes) in trees.items():
        idx, ridx, k = collections.defaultdict(set), collections.defaultdict(list), 0
        for nd in nodes:
            if nd[1] == 1:
                idx[nd[2].lower()].add(nd[4])
                ridx[nd[2].lower()].append((k, nd[4]))
                k += 1
        tidx[tid] = (idx, ridx)
        rnames[tid] = [nd[2].lower() for nd in nodes if nd[1] == 1]
    def tree_out(gid, tid):
        nodes = trees[tid][1]
        cmp = {}
        for oid, (owner, onodes) in trees.items():
            if owner == gid:
                continue
            (idx, ridx), hits, rr = tidx[oid], [], []
            for nd in nodes:
                if nd[1] == 1:
                    hit, cand = set(), []
                    for x in sorted(al.of(nd[2].lower())):
                        hit |= idx.get(x, set())
                        cand += ridx.get(x, [])
                    hits.append(sorted(hit))
                    # the routine to jump to in the other tree: same name first, then one in a matching file, then the first
                    cand.sort(key=lambda c: (rnames[oid][c[0]] != nd[2].lower(), file_key(c[1]) != file_key(nd[4]), c[0]))
                    rr.append(cand[0][0] if cand else -1)
            names = sorted({h for hs in hits for h in hs})
            pos = {n: i for i, n in enumerate(names)}
            homes = [nd[4] for nd in nodes if nd[1] == 1]
            y = [k for k, hs in enumerate(hits) if hs and file_key(homes[k]) not in {file_key(h) for h in hs}]
            # files: first file in the other tree with the same matching-file key (the roots are not matched). A file
            # with no such match falls back to the routines it holds: an SNES bank file holds routines from several
            # src/routines folders, so a Genesis file (main.asm) matches the bank file holding most of the routines of
            # the folder with its key (routines/main/), and a bank file matches the Genesis file of its busiest folder.
            def spans(ns):
                """Per file node (in order): {home key: routine count} of the routines that are its children."""
                out, stack = [], []
                for nd in ns:
                    if nd[1] == 0:
                        while stack and stack[-1][0] >= nd[0]:
                            stack.pop()
                        cur = {}
                        out.append(cur)
                        stack.append((nd[0], cur))
                    elif nd[1] == 1:
                        while stack and stack[-1][0] >= nd[0]:
                            stack.pop()
                        if stack:
                            k = file_key(nd[4])
                            stack[-1][1][k] = stack[-1][1].get(k, 0) + 1
                return out
            ofk, ofk2, ospans = {}, {}, spans(onodes)
            for j, p in enumerate([nd[2] for nd in onodes if nd[1] == 0]):
                # include the root: SNES routines/hockey/ matches Genesis hockey.asm even when that file is the tree root
                ofk.setdefault(file_key(p), j)
                if j:
                    for k, c in ospans[j].items():
                        if k != file_key(p) and c > ofk2.get(k, (0, 0))[0]:
                            ofk2[k] = (c, j)
            mspans = spans(nodes)
            fr = []
            for j, p in enumerate([nd[2] for nd in nodes if nd[1] == 0]):
                x = -1
                if j:
                    x = ofk.get(file_key(p), -1)
                    if x < 0 and file_key(p) in ofk2:
                        x = ofk2[file_key(p)][1]
                    if x < 0:
                        for k, c in sorted(mspans[j].items(), key=lambda kc: -kc[1]):
                            if k != file_key(p) and k in ofk:
                                x = ofk[k]
                                break
                fr.append(x)
            cmp[oid] = {'files': names, 'o': [[pos[h] for h in hs] for hs in hits], 'y': y, 'r': rr, 'f': fr}
        out = {'nodes': nodes, 'cmp': cmp, 'fk': [file_key(nd[2]) for nd in nodes if nd[1] == 0]}
        if tid.endswith(':groups'):
            out['gb'] = data[gid]['gb']
        return out

    # include-order matching keys per comparison id (92G files, 93S:groups, …). The page re-sorts an SNES
    # groups view to this sequence when that id is the comparison (or the other tree pane).
    all_seq = {}
    for m in meta:
        g = data[m['id']]
        if m['plat'] == 'genesis':
            all_seq[m['id']] = seq_of(g['files'])
        else:
            all_seq[m['id'] + ':groups'] = seq_of(g['groups'])
            all_seq[m['id'] + ':banks'] = seq_of(g['banks'])
            all_seq[m['id']] = all_seq[m['id'] + ':banks']

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
            tg[tid] = {'files': names, 'o': [[pos[o] for o in origins(u['m'], idx)] if u['m'] else None for u in units],
                       'seq': all_seq.get(tid, [])}
        out = {'id': gid, 'units': [{'n': u['n'], 't': u['t'], 'k': u['k'], **({'p': u['p']} if 'p' in u else {})} for u in units],
               'views': views, 'targets': tg, 'tree': tree_out(gid, gid)}
        if gid + ':groups' in trees:
            out['treeg'] = tree_out(gid, gid + ':groups')
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
