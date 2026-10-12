# -*- coding: utf-8 -*-
"""fold_boxes.py <built.html>  (3.24 · กัน "เขียนย้วย" ในกล่อง 🟡)
กล่อง 🟡 ข้อสังเกต: เห็นทันที = หัวกล่อง + "Implication:" (ข้อสรุป) + caveat (แหล่ง/ความน่าเชื่อถือ/หมายเหตุการใช้งาน)
ส่วนหลักฐาน (ย่อหน้าก่อน Implication ทั้งหมด รวม "เหตุผล:") พับเป็น <details class="full"> ไม่ลบข้อความ · idempotent"""
import io,re,sys
import json,html
f=sys.argv[1]; H=io.open(f,encoding='utf-8').read(); n=0
SH=json.load(io.open(sys.argv[2],encoding='utf-8')) if len(sys.argv)>2 else {}   # {คำขึ้นต้นหัวกล่องเดิม: หัวสั้นใหม่ ≤ ~100 ตัวอักษร} · หัวเดิมเก็บไว้ในส่วนพับ
def fix(m):
    global n
    box=m.group(0)
    if 'class="full"' in box: return box
    h4=re.match(r'<div class="box note"><h4>.*?</h4>\n?',box,flags=re.S).group(0)
    body=box[len(h4):-len('</div>')]
    ps=re.findall(r'<p[^>]*>.*?</p>',body,flags=re.S)
    if ''.join(ps).replace('\n','').strip()!=body.replace('\n','').strip(): return box
    imp=[p for p in ps if re.match(r'<p>\s*Implication',p)]
    mut=[p for p in ps if p.startswith('<p class="mut"')]
    ev=[p for p in ps if p not in imp and p not in mut]
    if len(imp)!=1 or not ev: return box
    n+=1
    oh=html.unescape(re.sub(r'<[^>]+>','',h4)); pre=''
    for k,v in SH.items():
        if k in oh:
            tagp=re.match(r'(🟡 ข้อสังเกต \([^)]*\): )',oh); full=oh
            h4='<div class="box note"><h4>%s%s</h4>\n'%(tagp.group(1) if tagp else '',v.replace('<','&lt;')); pre='<p><b>หัวกล่องเดิม:</b> %s</p>'%html.escape(full[len(tagp.group(1)):] if tagp else full); break
    return h4+imp[0]+'\n<details class="full"><summary>หลักฐานและเหตุผลเต็ม</summary>'+pre+''.join(ev)+'</details>\n'+''.join(mut)+'</div>'
H=re.sub(r'<div class="box note"><h4>🟡.*?</div>',fix,H,flags=re.S)
io.open(f,'w',encoding='utf-8').write(H); print('folded boxes:',n)
