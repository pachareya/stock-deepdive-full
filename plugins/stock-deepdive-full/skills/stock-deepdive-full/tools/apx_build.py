# -*- coding: utf-8 -*-
"""Build Dashboard + collapsible appendix (skill 3.14). MOVE-ONLY: blocks are moved verbatim.
Usage: python3 apx_build.py <file.html> <spec.json> <dashboard.html>
spec.json = {"A":[["A1","title","1.1",[["s1",4],["s1",5]],"optional one-line summary of EXISTING facts"],...],
             "B":[["s5",19,"5.3","what was corrected"],...],  "C":[["s10",15],["s10",16]],
             "toc_after":"<li><a href=\\"#s10\\">...</a></li>"}   (exact existing TOC <li> for section 10)
dashboard.html = <section id="s0">...</section> using ONLY numbers already in the article."""
import re,sys,json,os
sys.path.insert(0,os.path.dirname(__file__)); from blocks import blocks
F,SP,DB=sys.argv[1:4]; H=open(F,encoding="utf-8").read(); spec=json.load(open(SP,encoding="utf-8")); dash=open(DB,encoding="utf-8").read()
bl=blocks(H); G=spec["A"]; B=spec.get("B",[]); C=[tuple(x) for x in spec.get("C",[])]
moved={}
for g in G:
    for x in g[3]: moved[tuple(x)]=g[0]
for s,k,*_ in B: moved[(s,k)]="B"
for x in C: moved[x]="C"
for x in moved: assert x in bl, f"no block {x}"
orig={x:H[bl[x][0]:bl[x][1]] for x in moved}; T={g[0]:g for g in G}; seen=set(); edits=[]
for x,(a,b) in sorted(bl.items(),key=lambda kv:kv[1][0]):
    if x not in moved: continue
    gid=moved[x]
    if gid in seen: edits.append((a,b,"")); continue
    seen.add(gid)
    if gid=="B": p='<p class="mut">→ บันทึกการแก้ไขจากฉบับก่อน: <a href="#apxB">ภาคผนวก B</a></p>'
    elif gid=="C": p='<p class="mut">→ ข้อจำกัดของเอกสารชุดนี้ทั้งหมด และคำอธิบายป้ายชั้นข้อมูล: <a href="#apxC">ภาคผนวก C</a></p>'
    else:
        g=T[gid]; sm=(g[4]+" · ") if len(g)>4 and g[4] else ""
        p=f'<p class="mut">{sm}→ หลักฐานเต็ม: <a href="#{gid}">ภาคผนวก {gid} · {g[1]}</a></p>'
    edits.append((a,b,p))
for a,b,n in sorted(edits,reverse=True): H=H[:a]+n+H[b:]
H=re.sub(r'\n{3,}','\n\n',H)
det=lambda i,t,b: f'<details class="apx" id="{i}"><summary>{t}</summary><div class="apxb">\n{b}\n</div></details>\n'
A="\n".join(f'<h3 id="{g[0]}">{g[0]} · {g[1]} <span class="tag">จากหัวข้อ {g[2]}</span></h3>\n'+"\n".join(orig[tuple(x)] for x in g[3]) for g in G)
Bb=('<p>ทุกจุดที่แก้ต่างจากฉบับก่อน แสดงของเดิม เหตุผล และวิธีตรวจยืนยันไว้ครบ — จุดแก้เล็กที่เหลือติดป้าย <span class="tag blue">แก้ …</span> ไว้ในตำแหน่งเดิม</p>\n<div class="tw"><table><thead><tr><th>หัวข้อ</th><th>เรื่องที่แก้</th></tr></thead><tbody>'
    +"".join(f'<tr><td>{x[2]}</td><td>{x[3]}</td></tr>' for x in B)+'</tbody></table></div>\n'+"\n".join(f'<h4>จากหัวข้อ {x[2]}</h4>\n'+orig[(x[0],x[1])] for x in B))
leg=('<h4>ป้ายชั้นข้อมูลที่ใช้ในบทความนี้</h4>\n<div class="tw"><table><thead><tr><th>ป้าย</th><th>ความหมาย</th></tr></thead><tbody>'
 '<tr><td>📄</td><td>งบการเงิน/หมายเหตุ/56-1 ที่ยื่นต่อหน่วยงานกำกับ — น่าเชื่อถือสูงสุด ใช้คำนวณได้</td></tr><tr><td>🧮</td><td>คำนวณเองจากตัวเลขในบทความ พร้อมวิธีคำนวณ</td></tr>'
 '<tr><td>📊</td><td>สไลด์ Opportunity Day — เอกสารบริษัทเผยแพร่เอง ไม่ผ่านการยื่นกำกับ</td></tr><tr><td>🎙️</td><td>คำพูดผู้บริหารถอดจากคลิป (ซับอัตโนมัติ อาจฟังผิด)</td></tr>'
 '<tr><td>📰</td><td>ข่าวสื่อที่ระบุวันที่ — ไม่ใช่เอกสารบริษัท</td></tr><tr><td>&#x1F7E1;</td><td>ข้อสังเกต/การตีความของผู้เขียน — ข้อสังเกต → เหตุผล → Implication → ป้ายแหล่งข้อมูล/ความน่าเชื่อถือ/หมายเหตุ</td></tr></tbody></table></div>\n')
apx=('<section id="apx">\n<h2>ภาคผนวก</h2>\n<p class="mut">หลักฐาน ตาราง และวิธีคำนวณที่ย้ายออกจากเนื้อหาหลักเพื่อให้อ่าน thesis ได้เร็วขึ้น — ไม่มีการแก้ตัวเลขหรือข้อความ แตะหัวข้อเพื่อกางออก (ฉบับ PDF กางครบทุกส่วน)</p>\n'
 +det("apxA",f"ภาคผนวก A · หลักฐานและการคำนวณ (A1–A{len(G)})",A)+(det("apxB","ภาคผนวก B · บันทึกการแก้ไข",Bb) if B else "")+det("apxC","ภาคผนวก C · ข้อจำกัดและแหล่งข้อมูล",leg+"\n".join(orig[x] for x in C))+'</section>\n\n')
i=H.index('<div class="foot">'); H=H[:i]+apx+H[i:]
i=H.index('<nav class="toc">'); H=H[:i]+dash.strip()+"\n\n"+H[i:]
H=H.replace('<li><a href="#s1">','<li><a href="#s0">Dashboard</a></li>\n<li><a href="#s1">',1)
if spec.get("toc_after"): H=H.replace(spec["toc_after"],spec["toc_after"]+'\n<li><a href="#apx">ภาคผนวก A–C</a></li>',1)
H=H.replace('.foot{','details.apx{border:1px solid var(--line);border-radius:12px;margin:1.2em 0;background:var(--card)}\ndetails.apx>summary{cursor:pointer;padding:12px 18px;font-weight:700;color:#e8f1fa}\n.apxb{padding:0 18px 14px}\n.foot{',1)
H=H.replace('</body>','<script>window.addEventListener("beforeprint",function(){document.querySelectorAll("details").forEach(function(d){d.open=true})});</script>\n</body>',1)
open(F,"w",encoding="utf-8").write(H)
print("moved",len(orig),"blocks · missing/dup:",[x for x,s in orig.items() if H.count(s)!=1])
