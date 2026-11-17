#!/usr/bin/env python3
"""split_runs.py: derives the real source-file boundaries of a game from another build of the same code.

  python3 tools/split_runs.py REPO [--cart src/nhl94.asm] [--other src/segacd/hockey.asm]

The Sega CD HOCKEY.BIN has the same routines as the cartridge, but its linker put the source files in another
order. Walk the routines in the other build's order and note where the cartridge's order is broken: every break
is a file boundary of the original source (a developer can reorder files, not halves of a file). A break that
falls INSIDE one of our cartridge files means that file is really two (or more) files, and the printed pair of
labels is where to cut it.
"""
import re, os, sys, argparse, collections


def labels(path):
    out = []
    for i, l in enumerate(open(path, encoding='latin-1'), 1):
        m = re.match(r'^([A-Za-z_]\w*)', l)
        if m and not l.startswith((' ', '\t', ';')):
            out.append((m.group(1), i))
    return out


def inc_order(src, listfile):
    return [os.path.normpath(os.path.join(src, m.group(1).replace('\\', '/')))
            for l in open(listfile, encoding='latin-1') for m in [re.match(r'^\s*include\s+(\S+)', l)] if m]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('repo')
    ap.add_argument('--cart', default='src/nhl94.asm')
    ap.add_argument('--other', default='src/segacd/hockey.asm')
    ap.add_argument('--skip', action='append', default=['ram', 'frames', 'sound', 'teamdata'])
    a = ap.parse_args()
    os.chdir(a.repo)
    cart = []
    for p in inc_order('src', a.cart):
        if p.endswith('.asm') and os.path.isfile(p) and not any(s in os.path.basename(p) for s in a.skip):
            cart += [(n.lower(), os.path.basename(p), i) for n, i in labels(p)]
    cpos = {}
    for k, (n, f, i) in enumerate(cart):
        cpos.setdefault(n, (k, f, i))
    disc = []
    for p in inc_order('src', a.other):
        if os.path.isfile(p) and not any(s in os.path.basename(p) for s in a.skip):
            disc += [(n, os.path.basename(p)) for n, i in labels(p) if n.lower() in cpos]
    rank = {k: r for r, k in enumerate(sorted({cpos[n.lower()][0] for n, _ in disc}))}
    runs, prev = [], None
    for n, f in disc:
        r = rank[cpos[n.lower()][0]]
        if prev is not None and r == prev + 1:
            runs[-1].append((n, f))
        else:
            runs.append([(n, f)])
        prev = r
    print(f'{len(disc)} shared routines, {len(runs)} runs in the other build\'s order')
    for i, r in enumerate(runs):
        fa, la = cpos[r[0][0].lower()][1:]
        fb, lb = cpos[r[-1][0].lower()][1:]
        print(f'run {i:2} n={len(r):3}  {fa}:{la} {r[0][0]} .. {fb}:{lb} {r[-1][0]}')
    print('\nBreaks inside one cartridge file (cut the file here):')
    by_cart = sorted(runs, key=lambda r: cpos[r[0][0].lower()][0])
    for r1, r2 in zip(by_cart, by_cart[1:]):
        last, first = cpos[r1[-1][0].lower()], cpos[r2[0][0].lower()]
        if last[1] == first[1]:
            print(f'  {last[1]}: after {r1[-1][0]} (line {last[2]}), before {r2[0][0]} (line {first[2]})')


main()
