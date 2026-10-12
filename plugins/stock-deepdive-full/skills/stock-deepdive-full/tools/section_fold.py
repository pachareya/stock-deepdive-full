# -*- coding: utf-8 -*-
"""พับเนื้อหาแต่ละหัวข้อเป็น dropdown (3.21): หัวข้อ + 'ใจความ' 2–3 บรรทัดเห็นเสมอ · รายละเอียดอยู่ใน <details class="sec">
Usage: python3 section_fold.py <built.html> <summaries.json> [<before-apx.html> <keyx.json>]
keyx.json = {"s5":[block index ...]} บล็อก (เลขตาม blocks.py ของ before-apx) ที่เป็นหลักฐานหลักของข้อสรุป — ต้องเห็นใต้ใจความเสมอ ไม่พับ (3.22)
summaries.json = {"s5": ["บรรทัด 1","บรรทัด 2"], ...}  (ข้อความ/HTML ล้วน ห้ามมีตัวเลขที่ไม่มีในหัวข้อนั้น)
รันหลัง verify_move.py (บล็อกเลขเดิมต้องไม่ถูกแตะ) และก่อน patch_hashnav.py · ไม่ทำซ้ำถ้าหัวข้อถูกพับแล้ว"""
import sys,re,io,json
f,sf=sys.argv[1],sys.argv[2]
s=io.open(f,encoding='utf-8').read(); S=json.load(io.open(sf,encoding='utf-8'))
KEY={}   # sid -> [block html] หลักฐานหลักที่ต้องเห็นเสมอ (วางใต้ใจความ ก่อน dropdown)
if len(sys.argv)>4:
    sys.path.insert(0,__import__('os').path.expanduser('~/.claude/skills/stock-deepdive-full/tools'))
    from blocks import blocks
    B=io.open(sys.argv[3],encoding='utf-8').read(); bl=blocks(B); ki=json.load(io.open(sys.argv[4],encoding='utf-8'))
    TBL={}
    for sid,idx in ki.items():
        KEY[sid]=[]
        for i in idx:
            if isinstance(i,int): KEY[sid].append(B[bl[(sid,i)][0]:bl[(sid,i)][1]])
            else: TBL.setdefault(sid,[]).append(i)   # 'table:N' = ตาราง <div class="tw"> ลำดับที่ N (นับจาก 0; -1 = ตัวสุดท้าย) สำหรับหัวข้อที่ blocks.py มองไม่เห็น (เช่น s7b s8b)
    for sid,specs in TBL.items():
        m=re.search(r'<section id="%s">(.*?)</section>'%sid,B,flags=re.S)
        tws=re.findall(r'<div class="tw">.*?</table></div>',m.group(1),flags=re.S) if m else []
        for sp in specs:
            n=int(sp.split(':')[1])
            if tws: KEY[sid].append(tws[n])
n=0
for sid,lines in S.items():
    m=re.search(r'(<section id="%s">\s*<h[23][^>]*>.*?</h[23]>)(.*?)(</section>)'%sid,s,flags=re.S)
    if not m or 'class="secsum"' in m.group(0): continue
    head,body,tail=m.groups()
    keyhtml=''
    for kb in KEY.get(sid,[]):
        if kb in body: body=body.replace(kb,'',1); keyhtml+=kb+'\n'
        else: print('key block not found in',sid,kb[:50])
    box='<div class="secsum"><ul>'+''.join('<li>%s</li>'%l for l in lines)+'</ul></div>\n<details class="sec"><summary>อ่านรายละเอียด</summary>\n'
    box=box.replace('\n<details class="sec">','\n'+(('<div class="keyx">\n'+keyhtml+'</div>\n') if keyhtml else '')+'<details class="sec">',1)
    s=s[:m.start()]+head+'\n'+box+body+'\n</details>\n'+tail+s[m.end():]; n+=1
css=u'''.secsum{background:#14202c;border-left:3px solid #4a90d9;border-radius:8px;padding:.5em 1em;margin:.7em 0 .8em}
.secsum ul{margin:0;padding-left:1.1em}.secsum li{margin:.25em 0;line-height:1.6}
details.sec{margin:.3em 0 1.2em}details.sec>summary{cursor:pointer;color:#8fb8e6;font-weight:600;padding:.35em 0;list-style:none}
details.sec>summary::before{content:"▸ "}details.sec[open]>summary::before{content:"▾ "}
details.sec>summary::-webkit-details-marker{display:none}
button.openall{background:#14202c;color:#8fb8e6;border:1px solid #2c3d50;border-radius:8px;padding:.35em .9em;cursor:pointer;font:inherit;margin:.2em 0 .6em}
'''
if 'secsum{' not in s: s=s.replace('</style>',css+'</style>',1)
btn=u'<p><button class="openall" onclick="document.querySelectorAll(\'details.sec\').forEach(function(d){d.open=!d.open?true:d.open})">เปิดรายละเอียดทุกหัวข้อ</button> <button class="openall" onclick="document.querySelectorAll(\'details.sec\').forEach(function(d){d.open=false})">พับทั้งหมด</button></p>\n'
import re as _re
_m=_re.search(r'<nav class="toc[^"]*">',s)
if 'class="openall"' not in s and _m:
    i=s.index('</nav>',_m.start())+6; s=s[:i]+'\n'+btn+s[i:]
io.open(f,'w',encoding='utf-8').write(s); print('folded sections:',n)
