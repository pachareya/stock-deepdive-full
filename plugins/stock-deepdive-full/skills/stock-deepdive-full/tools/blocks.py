# -*- coding: utf-8 -*-
"""List top-level blocks inside each <section id="sN"> of a deep-dive HTML.
Usage: python3 blocks.py <file.html>   -> prints: section index tag class chars head"""
import re,sys
tagre=re.compile(r'<(/?)([a-zA-Z0-9]+)([^>]*?)(/?)>')
SELF={'col','br','hr','img','meta','link','input','circle','line','rect','polyline','path'}
def children(s):
    out=[];depth=0;start=None
    for m in tagre.finditer(s):
        close,tag,selfc=m.group(1),m.group(2).lower(),m.group(4)
        if selfc or tag in SELF:
            if depth==0: out.append((m.start(),m.end()))
            continue
        if not close:
            if depth==0: start=m.start()
            depth+=1
        else:
            depth-=1
            if depth==0: out.append((start,m.end()))
    return out
def blocks(H):
    d={}
    for sm in re.finditer(r'<section id="(s\d+[a-z]?)">(.*?)</section>',H,re.S):
        off=sm.start(2)
        for k,(a,b) in enumerate(children(sm.group(2))): d[(sm.group(1),k)]=(off+a,off+b)
    return d
if __name__=="__main__":
    H=open(sys.argv[1],encoding="utf-8").read()
    for (s,k),(a,b) in sorted(blocks(H).items(),key=lambda kv:kv[1][0]):
        blk=H[a:b]; t=re.sub(r'<svg.*?</svg>','[SVG]',blk,flags=re.S); t=re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',t)).strip()
        m=re.match(r'<(\w+)([^>]*)>',blk); c=re.search(r'class="([^"]+)"',m.group(2))
        print(f"{s:4}{k:3} {m.group(1):4} {(c.group(1) if c else '')[:10]:10} {len(t):5} {t[:80]}")
