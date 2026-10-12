# -*- coding: utf-8 -*-
"""ด่านความยาว (3.20): เตือนอย่างเดียว ไม่ทำให้ build ล้ม
Usage: python3 length_gate.py <built.html> [cell_max=120] [box_max=330]
 - ช่องตาราง (td) ในเนื้อหาหลัก (นอก <details> ภาคผนวก) เกิน cell_max ตัวอักษร -> เตือน (ย้ายรายละเอียดไปภาคผนวก/ตัดทอน)
 - กล่อง 🟡: เนื้อหา (ไม่นับ h4 และ <p class="mut"> ที่เป็น caveat) เกิน box_max ตัวอักษร -> เตือน
exit 0 เสมอ; พิมพ์สรุปจำนวน"""
import sys,re,html,io
s=io.open(sys.argv[1],encoding='utf-8').read()
cm=int(sys.argv[2]) if len(sys.argv)>2 else 120
bm=int(sys.argv[3]) if len(sys.argv)>3 else 330
tx=lambda x: re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>','',x))).strip()
main=re.sub(r'<details.*?</details>','',s,flags=re.S)
cells=[(len(tx(m)),tx(m)[:50]) for m in re.findall(r'<td[^>]*>(.*?)</td>',main,flags=re.S)]
bad=[c for c in cells if c[0]>cm]
print('ช่องตารางเนื้อหาหลักเกิน %d: %d จาก %d'%(cm,len(bad),len(cells)))
for n,t in sorted(bad,reverse=True)[:8]: print('  ',n,t)
boxes=0;over=[]
for m in re.finditer(r'<div class="box[^"]*"><h4>(🟡[^<]*)</h4>(.*?)</div>',s,flags=re.S):
    body=re.sub(r'<p class="mut">.*?</p>','',m.group(2),flags=re.S); n=len(tx(body)); boxes+=1
    if n>bm: over.append((n,m.group(1)[:50]))
print('กล่อง 🟡 เกิน %d ตัวอักษร: %d จาก %d'%(bm,len(over),boxes))
for n,t in sorted(over,reverse=True)[:10]: print('  ',n,t)
