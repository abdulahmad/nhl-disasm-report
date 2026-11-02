"""ram_order.py REF.asm OTHER.asm: matched RAM symbols (same name, any case) of OTHER that are out of REF's order
(the ones outside the longest run in order). Genesis rs lines are the memory layout and cannot move; = / equ
lines can. 2026-11-02: 92G vs 95G and 92G vs 96G are 0, 95G vs 96G is 0; against 93G/94G only their own rs
layout moves (lldisp, DMAlistend, the 94G DispAttribCtr group) remain."""
import re,sys,bisect
def syms(p):
    out=[]
    for i,l in enumerate(open(p,encoding='latin-1')):
        m=re.match(r'^([A-Za-z_][\w.]*)\s*(?::)?\s*(rs(?:\.[bwl])?|=|equ|set)\b',l,re.I)
        if m: out.append((m.group(1),m.group(2).lower(),i+1))
    return out
def lis_out(seq):
    # seq: list of positions in ref; return indices not in LIS
    tails=[];ti=[];prev=[-1]*len(seq)
    for i,x in enumerate(seq):
        k=bisect.bisect_left(tails,x)
        if k==len(tails): tails.append(x); ti.append(i)
        else: tails[k]=x; ti[k]=i
        prev[i]=ti[k-1] if k>0 else -1
    keep=set(); i=ti[-1] if ti else -1
    while i>=0: keep.add(i); i=prev[i]
    return [i for i in range(len(seq)) if i not in keep]
a,b=sys.argv[1],sys.argv[2]
A=syms(a); B=syms(b)
pa={}
for i,(n,k,l) in enumerate(A): pa.setdefault(n.lower(),i)
seen=set(); mb=[]
for n,k,l in B:
    if n.lower() in pa and n.lower() not in seen: seen.add(n.lower()); mb.append((n,k,l,pa[n.lower()]))
out=lis_out([x[3] for x in mb])
print(f'{len(A)} / {len(B)} symbols, {len(mb)} matched, {len(out)} out of order')
for i in out: n,k,l,_=mb[i]; print(f'  {n} ({k}, line {l})')
