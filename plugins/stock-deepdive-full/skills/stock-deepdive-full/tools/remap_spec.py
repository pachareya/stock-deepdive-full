# -*- coding: utf-8 -*-
"""Remap spec.json block ids from OLD build (before-apx html) to NEW build by exact block HTML match.
Usage: python3 remap_spec.py old.html new.html old_spec.json new_spec.json"""
import sys,os,json,io
sys.path.insert(0,os.path.expanduser('~/.claude/skills/stock-deepdive-full/tools'))
from blocks import blocks
O=io.open(sys.argv[1],encoding='utf-8').read(); N=io.open(sys.argv[2],encoding='utf-8').read()
bo=blocks(O); bn=blocks(N)
idx={}
for k,(a,b) in bn.items():
    idx.setdefault(N[a:b],[]).append(k)
sp=json.load(io.open(sys.argv[3],encoding='utf-8'))
used=set(); miss=[]
def m(x):
    a,b=bo[tuple(x)]; h=O[a:b]
    c=[k for k in idx.get(h,[]) if k not in used]
    if not c: miss.append((tuple(x),h[:60])); return None
    used.add(c[0]); return list(c[0])
for g in sp['A']:
    g[3]=[y for y in (m(x) for x in g[3]) if y]
sp['C']=[y for y in (m(x) for x in sp['C']) if y]
json.dump(sp,io.open(sys.argv[4],'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('remapped; missing:',miss)
