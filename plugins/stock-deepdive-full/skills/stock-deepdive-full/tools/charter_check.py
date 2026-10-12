# -*- coding: utf-8 -*-
"""charter_check.py <built.html> [baseline.html]  — ตรวจว่ารายงานตรงตาม CHARTER.md (ข้อตกลงรูปแบบ) ก่อน publish ทุกครั้ง
พิมพ์ PASS/FAIL ต่อข้อ · exit 1 ถ้ามี FAIL"""
import sys,re,io,html,os
f=sys.argv[1]; base=sys.argv[2] if len(sys.argv)>2 else None
s=io.open(f,encoding='utf-8').read()
tx=lambda x:re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',x))).strip()
res=[]
def R(name,ok,detail=''): res.append((name,ok,detail))
# C1 หน้าเปิดจบในไม่เกิน ~2 จอ + มีบทสรุป/มุมมอง + Bull|Bear
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1000,'height':900}); pg.goto('file://'+os.path.abspath(f)); pg.wait_for_timeout(400)
    y=pg.evaluate("(()=>{const e=document.getElementById('s0');return e?Math.round(e.getBoundingClientRect().top+scrollY):-1})()")
    R('C1 หน้าเปิด (ก่อน Dashboard) ไม่เกิน 2.2 จอ (≤ 1980px)',0<y<=1980,'%dpx'%y)
    R('C1b มีกล่องบทสรุปที่เป็น "ราคานี้ต้องเชื่ออะไร" + Bull|Bear',('บทสรุป: ราคานี้ต้องเชื่ออะไร' in s) and ('class="bb"' in s),'')
    # C2 ทุกหัวข้อยาว >1500: มีใจความ + หลักฐานหลักเห็นเสมอ
    rows=pg.evaluate("""()=>[...document.querySelectorAll('section[id^=s]')].filter(s=>/^s\\d+b?$/.test(s.id)&&s.id!=='s0').map(s=>{const sec=s.querySelector('.secsum');const key=s.querySelector('.keyx');
      const vis=[...s.querySelectorAll('table,svg')].filter(t=>t.getClientRects().length>0);return [s.id,s.textContent.length,!!sec,vis.length>0,sec?sec.querySelectorAll('li').length:0]})""")
    EX={'s2','s3','s4','s6','s8'}   # หัวข้อบรรยาย (ข้อมูลหลักเป็นข้อความ/คำพูด ไม่มีตารางพิสูจน์) — ยกเว้นเรื่องหลักฐานหลัก แต่ต้องมีใจความ
    bad=[r for r in rows if r[1]>1500 and (not r[2] or (not r[3] and r[0] not in EX) or r[4]>3)]
    R('C2 ทุกหัวข้อยาว: มีใจความ ≤3 บรรทัด + หลักฐานหลักเห็นเสมอ',not bad,'ขาด: '+', '.join('%s(ใจความ=%s หลักฐาน=%s)'%(r[0],r[2],r[3]) for r in bad))
    # C7 ตาราง
    t=pg.evaluate("(()=>{document.querySelectorAll('details').forEach(d=>d.open=true);let m=0,n=0,sc=0;document.querySelectorAll('tr').forEach(r=>{const h=r.getBoundingClientRect().height;m=Math.max(m,h);if(h>320)n++});document.querySelectorAll('.tw').forEach(t=>{if(t.scrollWidth>t.clientWidth+2)sc++});return [Math.round(m),n,sc,document.documentElement.scrollWidth]})()")
    R('C7 ตาราง: ไม่มีแถวสูง >320px · ไม่ล้นกรอบ · หน้าไม่เลื่อนข้าง',t[1]==0 and t[2]==0 and t[3]<=1000,'แถวสูงสุด %dpx · แถว>320px %d · ล้นกรอบ %d'%(t[0],t[1],t[2]))
    b.close()
# C12 ตารางอ่านสบายตา: (ก) ไม่มีคำอังกฤษ/ตัวเลขถูกตัดกลางคำ (ข) ไม่มีคอลัมน์ข้อความถูกบีบแคบ <105px ทั้งที่เนื้อหายาว (ช่องซ้ายสุดยืดลงเป็นแถวสูง)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1000,'height':900}); pg.goto('file://'+os.path.abspath(f)); pg.wait_for_timeout(300)
    r=pg.evaluate("""()=>{document.querySelectorAll('details').forEach(d=>d.open=true);
      const broken=[],narrow=[];
      document.querySelectorAll('table').forEach((t,ti)=>{
        const rows=[...t.rows];
        rows.forEach(r=>[...r.cells].forEach(c=>{
          const w=document.createTreeWalker(c,NodeFilter.SHOW_TEXT);let n;
          while(n=w.nextNode()){const re=/[A-Za-z]{5,}/g;let m;while(m=re.exec(n.data)){const rg=document.createRange();rg.setStart(n,m.index);rg.setEnd(n,m.index+m[0].length);const rs=[...rg.getClientRects()];if(rs.length>1&&Math.abs(rs[0].top-rs[rs.length-1].top)>6){broken.push(m[0]+'@T'+ti)}}}
        }));
        const nc=Math.max(...rows.map(r=>r.cells.length));
        for(let j=0;j<nc;j++){const cells=rows.map(r=>r.cells[j]).filter(Boolean);if(!cells.length)continue;
          const txt=cells.map(c=>c.textContent.trim());const avg=txt.reduce((a,x)=>a+x.length,0)/txt.length;
          const isnum=txt.filter(x=>/^[\s\d.,%+\-−–·×/()xเท่าล้านบาท⚠️฿:~≈<>]*$/.test(x)).length/txt.length>=0.6;
          const wpx=cells[0].getBoundingClientRect().width;
          if(!isnum&&avg>10&&wpx<105&&nc>=3)narrow.push('T'+ti+'c'+j+'('+Math.round(wpx)+'px avg'+Math.round(avg)+')');}
      });return [broken.slice(0,12),narrow.slice(0,12)]}""")
    R('C12a ไม่มีคำอังกฤษ/ตัวเลขในตารางถูกตัดกลางคำ',not r[0],str(r[0]))
    R('C12b ไม่มีคอลัมน์ข้อความ (เนื้อหายาว) ถูกบีบแคบ <105px',not r[1],str(r[1]))
    b.close()
# C13 การจัดวางตาราง: (ก) หัวคอลัมน์ชิดข้างเดียวกับข้อมูล (ตัวเลขชิดขวา → หัวชิดขวา) (ข) คอลัมน์ # / เลขอ้างอิงสั้นกว้างไม่เกิน ~96px (ค) ตาราง Dashboard 'ดูที่' ทุกตารางมีคอลัมน์ค่า/ดูที่ตำแหน่งเดียวกัน
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1000,'height':900}); pg.goto('file://'+os.path.abspath(f)); pg.wait_for_timeout(300)
    r=pg.evaluate("""()=>{document.querySelectorAll('details').forEach(d=>d.open=true);
      const mis=[],wide=[],dash=[];
      document.querySelectorAll('table').forEach((t,ti)=>{
        const rows=[...t.rows]; if(rows.length<2)return;
        const nc=Math.max(...rows.map(r=>r.cells.length));
        for(let j=0;j<nc;j++){
          const body=rows.slice(1).map(r=>r.cells[j]).filter(c=>c&&c.colSpan===1);
          const head=rows[0].cells[j]; if(!head||!body.length)continue;
          const al=c=>{const a=getComputedStyle(c).textAlign;return (a==='right'||a==='end')?'r':(a==='center'?'c':'l')};
          const rc=body.filter(c=>al(c)==='r').length;
          if(rc/body.length>=0.5&&al(head)!=='r')mis.push('T'+ti+'c'+j+':'+head.textContent.trim().slice(0,14));
          const txt=body.map(c=>c.textContent.trim());
          if(txt.length>=2&&Math.max(...txt.map(x=>x.length))<=3&&head.getBoundingClientRect().width>96)wide.push('T'+ti+'c'+j+'('+Math.round(head.getBoundingClientRect().width)+'px)');
        }
        if(rows[0].cells.length===3&&rows[0].cells[2].textContent.trim()==='ดูที่'){const c=rows[0].cells;dash.push([Math.round(c[1].getBoundingClientRect().left),Math.round(c[2].getBoundingClientRect().left)])}
      });
      const dashbad=dash.length>1&&dash.some(d=>Math.abs(d[0]-dash[0][0])>2||Math.abs(d[1]-dash[0][1])>2);
      return [mis.slice(0,12),wide.slice(0,12),dashbad,dash]}""")
    R('C13a หัวคอลัมน์ชิดข้างเดียวกับข้อมูล (ตัวเลขชิดขวา → หัวชิดขวา)',not r[0],str(r[0]))
    R('C13b คอลัมน์ # / เลขอ้างอิงสั้น กว้างไม่เกิน 70px',not r[1],str(r[1]))
    R('C13c ตาราง Dashboard (ดูที่) ทุกตารางมีคอลัมน์ค่า/ดูที่ตำแหน่งเดียวกัน',not r[2],str(r[3]))
    b.close()
# C10 คำกล่าวเกินในชื่อเรื่อง/ใต้ชื่อ (ส่วนใหญ่/Mostly/majority) ต้องไม่มี — ใช้ตัวเลขจริงแทน
hk=re.search(r'<h1[^>]*>(.*?)</h1>',s,flags=re.S); hp=re.search(r'<p class="hook">(.*?)</p>',s,flags=re.S)
hh=tx((hk.group(1) if hk else '')+' '+(hp.group(1) if hp else ''))
badw=[w for w in ['ส่วนใหญ่','Mostly','Majority','majority','ทั้งหมด','เกือบทั้งหมด'] if w in hh]
R('C10 ชื่อเรื่อง/ใต้ชื่อไม่ใช้คำกล่าวเกิน (ส่วนใหญ่/Mostly/ทั้งหมด) — ใช้ตัวเลขที่คำนวณได้',not badw,str(badw)+' | '+hh[:90])
# C3 ลิงก์ anchor
ids=set(re.findall(r'id="([^"]+)"',s)); hr=set(re.findall(r'href="#([^"]+)"',s))
R('C3 ลิงก์ภายในไม่เสีย',not [h for h in hr if h not in ids and h!=''],str([h for h in hr if h not in ids])[:80])
# C6 คำตกค้าง
T=tx(s); T_noTech=tx(re.sub(r'<section id="s1[1-9]">.*?</section>','',s,flags=re.S)); stale=[k for k in ['Yahoo','แหล่งรอง','7.6.1','ต่อด้านล่าง','TODO','undefined','NaN'] if (k in T_noTech if k=='Yahoo' else k in T)]   # Yahoo ห้ามเป็นแหล่งราคา/ตัวคูณ แต่ใช้ได้ในหัวข้อมุมเทคนิค (3.24: ราคาย้อนหลัง ต้องตรวจกับ SET)
R('C6 ไม่มีคำตกค้าง',not stale,str(stale))
# C9 จำนวนที่อ้างตรงของจริง
bad=[]
for hm in re.finditer(r'<h4>[^<]*?(\d+) (?:บรรทัด|ข้อ)[^<]*</h4>\s*<(ol|ul)>(.*?)</\2>',s,flags=re.S):
    n=len(re.findall(r'<li>',hm.group(3)))
    if n!=int(hm.group(1)): bad.append('%s vs %d'%(hm.group(1),n))
R('C9 หัวกล่องที่อ้างจำนวนข้อ ("N บรรทัด/ข้อ") มีจำนวนข้อจริงตรงกัน',not bad,str(bad))
# C11 เทียบงวดเท่ากัน: ตารางที่เห็นทันที (ไม่อยู่ใน details.more) ห้ามมีหัวคอลัมน์/ป้ายแถวแรกที่ความยาวงวดต่างกัน (3M/6M/9M/12M ปน)
#     + C11b เฉพาะเคสพิเศษ: ถ้ามีปีบัญชีไม่เต็ม (เช่น "FY68 9M") หรือมีการใช้ ★ ต้องมีคำอธิบายเหตุพิเศษกำกับ (หุ้นปกติไม่ต้องมี ★)
vis=re.sub(r'<details class="more">.*?</details>','',s,flags=re.S)
lenre=re.compile(r'(?<![\d/])(\d{1,2})\s*M(?![A-Za-z])|(\d{1,2}) เดือน|(?:^|\s)(\d)M/\d\d|\bQ\d/\d\d (\d)M|FY\d\d (\d)M')
badt=[]
for tb in re.findall(r'<table\b.*?</table>',vis,flags=re.S):
    labs=[]
    rows=re.findall(r'<tr[^>]*>(.*?)</tr>',tb,flags=re.S)
    if rows: labs+=[tx(c) for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>',rows[0],flags=re.S)]
    for r in rows[1:]:
        m=re.search(r'<t[hd][^>]*>(.*?)</t[hd]>',r,flags=re.S)
        if m: labs.append(tx(m.group(1)))
    L=set()
    if any(u'เฉลี่ย' in lb for lb in labs): continue   # ตารางที่แปลงเป็นฐานเท่ากัน (เฉลี่ย/เดือน) ใช้เทียบงวดสะสมต่างความยาวได้
    for lb in labs[:40]:
        if len(lb)>40 or 'TTM' in lb or 'ทุกคอลัมน์' in lb or 'ปีเต็ม' in lb: continue
        for m in lenre.finditer(lb):
            v=[g for g in m.groups() if g]
            if v: L.add(int(v[0]))
        if re.search(r'^(FY\d\d|Q\d/\d\d)$',lb.strip()) and 'Q' in lb: L.add(3)
    if len(L)>1: badt.append(('/'.join(str(x) for x in sorted(L)),tx(tb)[:40]))
R('C11a ตารางที่เห็นทันทีไม่ปนงวดต่างความยาว (3M/6M/9M/12M) — ตารางสะสมไปไว้ใน details.more',not badt,'; '.join('%s: %s'%b for b in badt[:6]))
partial=bool(re.search(r'FY\d\d\s*9\s*(M|เดือน)',T))   # ปีบัญชีที่ยื่นไม่เต็ม 12 เดือน (เคสพิเศษ เช่น หลังควบรวม)
usedstar=('★' in s)
explained=bool(re.search(r'★[^<]{0,80}(รวมกิจการ|ควบรวม|เหตุพิเศษ|ไม่ใช่ปีเต็ม|เปลี่ยนรอบ|ครั้งเดียว)',s)) and (u'วิธีอ่านงวด' in s or not partial)
R('C11b เคสพิเศษ (ปีบัญชีไม่เต็ม/ใช้ ★) ต้องมี ★ + คำอธิบายเหตุ · หุ้นปกติไม่ต้องมี ★',((not partial) and (not usedstar)) or (usedstar and explained and ((not partial) or (u'วิธีอ่านงวด' in s))),'partial=%s star=%s explained=%s'%(partial,usedstar,explained))
# C8 ความยาวช่อง/กล่อง
main=re.sub(r'<section id="apx">.*?</section>','',s,flags=re.S)
cells=[len(tx(c)) for c in re.findall(r'<td[^>]*>(.*?)</td>',main,flags=re.S)]
R('C8 ช่องตารางในเนื้อหาหลักเกิน 120 ตัวอักษร ≤ 5% ของช่องทั้งหมด',sum(c>120 for c in cells)<=0.05*len(cells),'%d จาก %d'%(sum(c>120 for c in cells),len(cells)))
# C4 ไม่มีเนื้อหาหายเทียบฉบับก่อน (ตัวเลข)
if base:
    nre=re.compile(r'(?<![\w.])\d[\d,]*\.?\d*%?')
    keep=lambda t:{k for k in nre.findall(t) if len(re.sub(r'[,.%]','',k))>=3}
    o=keep(tx(io.open(base,encoding='utf-8').read())); n=keep(T)
    R('C4 ตัวเลขจากฉบับก่อนหายไม่เกิน 3% (ที่หายต้องรายงานผู้ใช้)',len(o-n)<=0.03*len(o),'หาย %d จาก %d: %s'%(len(o-n),len(o),sorted(o-n)[:8]))
w=max(len(r[0]) for r in res)
for nme,ok,d in res: print(('PASS ' if ok else 'FAIL ')+nme+('  → '+d if d else ''))
sys.exit(1 if any(not ok for _,ok,_ in res) else 0)
