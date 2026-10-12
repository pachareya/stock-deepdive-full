# -*- coding: utf-8 -*-
"""section_fold2.py <built.html> <summaries.json> <keyx.json>   (3.23 · แทน section_fold.py)
จัดแต่ละหัวข้อเป็น: หัวข้อ → ใจความ 2–3 บรรทัด → รายการหัวข้อย่อย N.M เรียงตามลำดับเดิมเป็น dropdown (ถ้ามีหลักฐานหลักใน keyx = เปิดไว้ และพับส่วนที่เหลือเป็น 'รายละเอียด')
หัวข้อที่ไม่มีหัวข้อย่อย = หลักฐานหลักเห็นเสมอ + dropdown รายละเอียด · ไม่ย้ายลำดับเนื้อหา · keyx = {"s5":[บล็อกเลขตาม blocks.py ของไฟล์เดียวกัน]}"""
import sys,re,io,json,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from blocks import blocks
f,sf,kf=sys.argv[1:4]
H=io.open(f,encoding='utf-8').read(); S=json.load(io.open(sf,encoding='utf-8')); K=json.load(io.open(kf,encoding='utf-8'))
B=blocks(H)
tx=lambda x:re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',x)).strip()
def tag(x): return re.match(r'<(\w+)',x).group(1)
out=[];n=0
for sid in S:
    ks=sorted([k for k in B if k[0]==sid],key=lambda k:k[1])
    if not ks: print('no section',sid); continue
    m=re.search(r'<section id="%s">.*?</section>'%sid,H,flags=re.S)
    if 'class="secsum"' in m.group(0): continue
    blk=[H[B[k][0]:B[k][1]] for k in ks]
    key=set(K.get(sid,[]))
    box='<div class="secsum"><ul>'+''.join('<li>%s</li>'%l for l in S[sid])+'</ul></div>'
    head=blk[0] if tag(blk[0]) in ('h2','h3') else ''
    body=list(enumerate(blk))[1 if head else 0:]
    h3s=[i for i,b in body if tag(b)=='h3' and re.match(r'\d+\.\d+',tx(b))]   # เฉพาะหัวข้อย่อยที่มีเลข N.M
    pieces=[head,box]
    if not h3s:
        kb=[b for i,b in body if i in key]; rb=[b for i,b in body if i not in key]
        if kb: pieces.append('<div class="keyx">\n'+'\n'.join(kb)+'\n</div>')
        if rb: pieces.append('<details class="sec"><summary>อ่านรายละเอียด</summary>\n'+'\n'.join(rb)+'\n</details>')
    else:
        intro=[b for i,b in body if i<h3s[0]]
        if intro: pieces.append('<details class="sub"><summary>บทนำและนิยามของหัวข้อนี้</summary>\n'+'\n'.join(intro)+'\n</details>')
        for j,a in enumerate(h3s):
            z=h3s[j+1] if j+1<len(h3s) else 10**9
            title=tx(blk[a]); content=[(i,b) for i,b in body if a<i<z]
            kb=[b for i,b in content if i in key]; rb=[b for i,b in content if i not in key]
            num=re.match(r'(\d+(?:\.\d+)?)',title); sidn='sub-'+(num.group(1).replace('.','-') if num else str(j))
            inner=''
            if kb: inner+='\n'.join(kb)+'\n'
            if rb: inner+=('<details class="more"><summary>รายละเอียด</summary>\n'+'\n'.join(rb)+'\n</details>') if kb else '\n'.join(rb)
            pieces.append('<details class="sub" id="%s"%s><summary>%s</summary>\n%s\n</details>'%(sidn,' open' if kb else '',title,inner))
    new='<section id="%s">\n'%sid+'\n'.join(p for p in pieces if p)+'\n</section>'
    out.append((m.start(),m.end(),new)); n+=1
for a,z,new in sorted(out,reverse=True): H=H[:a]+new+H[z:]
css=u'''.secsum{background:#14202c;border-left:3px solid #4a90d9;border-radius:8px;padding:.5em 1em;margin:.7em 0 .8em}
.secsum ul{margin:0;padding-left:1.1em}.secsum li{margin:.25em 0;line-height:1.6}
details.sec{margin:.3em 0 1.2em}details.sec>summary,details.more>summary{cursor:pointer;color:#8fb8e6;font-weight:600;padding:.35em 0;list-style:none}
details.sub{margin:.55em 0;border:1px solid #24323f;border-radius:10px;background:#101a24;padding:.15em 1em .5em}
details.sub>summary{cursor:pointer;font-weight:700;padding:.55em 0;list-style:none;color:#dbe6f0}
details.sub>summary::before,details.sec>summary::before,details.more>summary::before{content:"▸ "}
details.sub[open]>summary::before,details.sec[open]>summary::before,details.more[open]>summary::before{content:"▾ "}
details>summary::-webkit-details-marker{display:none}details.more{margin:.4em 0}
button.openall{background:none;color:#9bb7d4;border:1px solid #2c3d50;border-radius:999px;padding:.28em .85em;cursor:pointer;font:inherit;font-size:.9rem;line-height:1.5;margin:.2em 0 .6em}p.foldrow{margin:.2em 0 .6em;display:flex;flex-wrap:wrap;align-items:center;gap:8px}p.foldrow .mut{font-size:.78rem}p.foldrow button.openall{margin:0}
'''
if 'details.sub{' not in H: H=H.replace('</style>',css+'</style>',1)
sel="'details'"
btn=u'<p class="foldrow"><button class="openall" onclick="document.querySelectorAll(%s).forEach(function(d){d.open=true})">เปิดทุกกล่อง</button> <button class="openall" onclick="document.querySelectorAll(%s).forEach(function(d){d.open=false})">พับทุกกล่อง</button> <span class=\"mut\">ปกติเปิดเฉพาะหลักฐานหลัก · กดเปิดทุกกล่อง = เห็นรายละเอียดทั้งหมด</span></p>\n'%(sel,sel)
mm=re.search(r'<nav class="toc[^"]*">',H)
if 'class="openall"' not in H and mm:
    i=H.index('</nav>',mm.start())+6; H=H[:i]+'\n'+btn+H[i:]
io.open(f,'w',encoding='utf-8').write(H); print('folded sections:',n)
