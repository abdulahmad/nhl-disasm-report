#!/usr/bin/env python3
"""split_audit.py: finds source files that are cut into pieces and says which cuts are real.

  python3 tools/split_audit.py REPO [REPO ...]            report only
  python3 tools/split_audit.py REPO --apply [--fold N]    merge what is safe, then run the repo's check yourself

An "include list" is any .asm file with three or more `include` lines (nhl94.asm, segacd/hockey.asm,
engine95.asm ...). Inside one list the tool groups files by stem:

  * numbered pieces   cards94.asm + cards94_2.asm       (the Sega CD fragments: one cartridge file that
                                                        shows up in several places of the disc)
  * job pieces        logic96.asm + logic96_puck.asm    (96G cuts by job; reported as folder candidates)

For numbered pieces it classifies every neighbouring pair:
  ADJACENT     nothing is included between the two pieces. Merging cannot change a byte.
  TINY-FIRST   the first piece is at most N lines and the file before it is disc-only (cdhockey). Appending
               the piece to that file keeps every byte at the same address, so the piece is not a real
               cartridge cut. The numbered piece then becomes the base file.
  INTERLEAVED  other files sit between the pieces: a real reordering in the binary. Left alone and listed with
               what sits between them (line counts), so the split is documented, not guessed.

--apply does the first two (merge = concatenate, delete the extra file, fix the include list). The order of
includes never changes, so the build must still MATCH; run it (tools/verify_all.sh -q) before committing.
"""
import re, sys, os, argparse

INC = re.compile(r'^\s*include\s+(\S+)', re.I)
DISC_ONLY = ('cdhockey',)  # stems that have no cartridge twin; extend with --disc-only


def norm(p):
    return p.replace('\\', '/').split(';')[0].strip()


def lists(root):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in ('.git', 'node_modules', 'output', 'Extracted', 'stubinc')]
        for f in fn:
            if not f.endswith('.asm'):
                continue
            p = os.path.join(dp, f)
            try:
                L = open(p, encoding='latin-1').read().split('\n')
            except OSError:
                continue
            inc = [(i, norm(m.group(1))) for i, l in enumerate(L) for m in [INC.match(l)] if m]
            if len(inc) >= 3:
                yield p, L, inc


def resolve(root, listpath, inc):
    """Find the file an include line names: relative to src/ (SNASM) or to the list's folder."""
    for base in (os.path.join(root, 'src'), os.path.dirname(listpath), root):
        c = os.path.normpath(os.path.join(base, inc))
        if os.path.isfile(c):
            return c
    return None


def nlines(p):
    return sum(1 for _ in open(p, encoding='latin-1')) if p else 0


def stem(path):
    return os.path.basename(path)[:-4] if path.endswith('.asm') else None


def audit(root, apply, fold, disc_only):
    root = os.path.abspath(root)
    changed = 0
    print(f'== {os.path.basename(root)}')
    for lp, L, inc in lists(root):
        files = [(i, n, resolve(root, lp, n)) for i, n in inc]
        stems = {}
        for pos, (i, n, p) in enumerate(files):
            s = stem(n.split('/')[-1]) if n.endswith('.asm') else None
            if s:
                stems.setdefault(s, pos)
        groups = {}
        for s, pos in stems.items():
            m = re.match(r'^(.*?)_(\d+)$', s)
            if m:
                groups.setdefault(m.group(1), []).append((int(m.group(2)), s, pos))
        jobs = {}
        for s, pos in stems.items():
            m = re.match(r'^([a-z]+\d\d)_([a-z]\w*)$', s)
            if m:
                jobs.setdefault(m.group(1), []).append(s)
        rel = os.path.relpath(lp, root)
        if groups or jobs:
            print(f'-- include list {rel} ({len(files)} includes)')
        edits = []  # (kind, ...)
        for base, parts in sorted(groups.items()):
            seq = sorted(parts)
            chain = []
            if base in stems:
                chain.append((1, base, stems[base]))
            chain += seq
            for a, b in zip(chain, chain[1:]):
                pa, pb = a[2], b[2]
                between = [(files[k][1].split('/')[-1], nlines(files[k][2])) for k in range(pa + 1, pb)]
                la = nlines(files[pa][2])
                if not between:
                    kind = 'ADJACENT'
                elif la <= fold and stem(files[pa - 1][1].split('/')[-1]) in disc_only and a[1] == base:
                    kind = 'TINY-FIRST'
                else:
                    kind = 'INTERLEAVED'
                bt = ', '.join(f'{n} ({c})' for n, c in between) or '-'
                print(f'   {kind:11} {a[1]} ({la} lines) .. {b[1]} ({nlines(files[pb][2])} lines): between: {bt}')
                edits.append((kind, a, b, files))
        for base, js in sorted(jobs.items()):
            if base in stems:
                print(f'   JOB-PIECES  {base}.asm + {len(js)} pieces ({", ".join(sorted(js)[:6])}{"..." if len(js) > 6 else ""})'
                      f' -> one folder candidate')
        if apply and edits:
            changed += do_apply(root, lp, L, edits)
    return changed


def do_apply(root, lp, L, edits):
    n = 0
    drop = set()
    for kind, a, b, files in edits:
        pa, pb = a[2], b[2]
        if kind == 'ADJACENT':
            fa, fb = files[pa][2], files[pb][2]
            if not fa or not fb or files[pa][0] in drop:
                continue
            txt = open(fa, encoding='latin-1').read().rstrip('\n') + '\n' + open(fb, encoding='latin-1').read()
            open(fa, 'w', encoding='latin-1').write(txt)
            os.remove(fb)
            drop.add(files[pb][0])
            n += 1
            print(f'   merged {os.path.basename(fb)} into {os.path.basename(fa)}')
        elif kind == 'TINY-FIRST':
            prev, fa, fb = files[pa - 1][2], files[pa][2], files[pb][2]
            if not prev or not fa or not fb:
                continue
            txt = open(prev, encoding='latin-1').read().rstrip('\n') + '\n' + open(fa, encoding='latin-1').read()
            open(prev, 'w', encoding='latin-1').write(txt)
            os.remove(fa)
            drop.add(files[pa][0])
            newb = fa  # the numbered piece becomes the base file name
            os.rename(fb, newb)
            L[files[pb][0]] = re.sub(r'(\S*?)' + re.escape(os.path.basename(fb)), lambda m: m.group(1) + os.path.basename(newb), L[files[pb][0]])
            n += 1
            print(f'   folded {os.path.basename(fa)} into {os.path.basename(prev)}; {os.path.basename(fb)} is now {os.path.basename(newb)}')
    if n:
        open(lp, 'w', encoding='latin-1').write('\n'.join(l for i, l in enumerate(L) if i not in drop))
    return n


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('repos', nargs='+')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--fold', type=int, default=100)
    ap.add_argument('--disc-only', action='append', default=list(DISC_ONLY))
    a = ap.parse_args()
    total = sum(audit(r, a.apply, a.fold, set(a.disc_only)) for r in a.repos)
    if a.apply:
        print(f'{total} merges applied: run the repo check (tools/verify_all.sh -q) before committing')
