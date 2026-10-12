# -*- coding: utf-8 -*-
"""ปรับความกว้างคอลัมน์ทุกตารางอัตโนมัติตามเนื้อหา (3.20) — ช่องข้อความกว้าง ช่องตัวเลขแคบ
Usage: python3 table_balance.py <built.html>   (รันหลัง build_paper.py ก่อน apx_build)
- ลบ <colgroup> เดิม/class fix6 แล้วคำนวณใหม่ทุก <table>; ใส่ class="bal" + <colgroup><col style="width:%">
- ช่องตัวเลข (เฉลี่ย ≤16 ตัวอักษร และส่วนใหญ่เป็นตัวเลข) = แคบ ; ช่องข้อความ = สัดส่วนตามความยาวเฉลี่ย
- ข้ามเซลล์ colspan ตอนวัด ; ตั้ง min-width ของตารางให้เลื่อนข้างได้บนมือถือ (ไม่ทำให้หน้าเลื่อนข้าง)"""
import sys,re,io,html
f=sys.argv[1]; s=io.open(f,encoding='utf-8').read()
tx=lambda x: re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>','',x))).strip()
numre=re.compile(r'^[\s\d.,%+\-−–·×/()xเท่าล้านบาท⚠️฿:~≈<>]*$')
def numeric(t): return len(t)<=26 and bool(re.search(r'\d',t)) and numre.match(t) is not None
def fix(m):
    t=m.group(0)
    t=re.sub(r'<colgroup>.*?</colgroup>\s*','',t,flags=re.S)
    t=re.sub(r'<table[^>]*>','<table>',t,count=1)
    rows=re.findall(r'<tr[^>]*>(.*?)</tr>',t,flags=re.S)
    cols=[]
    for r in rows:
        cells=re.findall(r'<(t[hd])([^>]*)>(.*?)</t[hd]>',r,flags=re.S)
        if any('colspan' in c[1] for c in cells): continue
        for j,(tag,attr,body) in enumerate(cells):
            while len(cols)<=j: cols.append([])
            cols[j].append((tag,tx(body)))
    n=len(cols)
    if n<2: return t
    W=[];MW=[]
    for c in cols:
        body=[x for tg,x in c if tg=='td'] or [x for tg,x in c]
        avg=sum(len(x) for x in body)/max(1,len(body)); mx=max(len(x) for x in body)
        isnum=sum(numeric(x) for x in body)/max(1,len(body))>=0.6 and avg<=16
        hdr=max([len(x) for tg,x in c if tg=='th'] or [0])
        if isnum: W.append(max(16,min(avg*1.3+5,22),min(hdr*1.5+2,18))+(min(mx,60)*0.3 if mx>26 else 0)); MW.append(80)
        else: W.append(max(22,min(avg*1.1,150),min(hdr,18))); MW.append(max(160,min(avg*5.2,340)))
    for j,c in enumerate(cols):
        mxj=max(len(x) for tg,x in c if tg=='td') if any(tg=='td' for tg,x in c) else 0
        if mxj>26 and MW[j]<=80: W[j]=max(W[j],40); MW[j]=140
    for j,c in enumerate(cols):
        L=sorted(len(x) for tg,x in c if tg=='td')
        if L:
            p90=L[int(0.9*(len(L)-1))]; W[j]=max(W[j],min(p90*0.5,40),min(L[-1]*0.35,30),12)
    for j,c in enumerate(cols):
        H=[len(x) for tg,x in c if tg=='th']
        if H: W[j]=max(W[j],min(max(H)*2.2,50))
    # คอลัมน์ 'รหัส/ชื่อสั้น' (ไม่ใช่ตัวเลข มัธยฐานความยาว ≤ 12 และหัว ≤ 12) = ความกว้างพิกเซลคงที่ ไม่ให้ตัดบรรทัดทีละตัวอักษร
    idc=set()
    for j,c in enumerate(cols):
        L=sorted(len(x) for tg,x in c if tg=='td'); H=[len(x) for tg,x in c if tg=='th']
        if L and L[len(L)//2]<=12 and (max(H) if H else 0)<=12 and not (sum(numeric(x) for x in [y for tg,y in c if tg=='td'])/len(L)>=0.6) and n>=4: idc.add(j)
    PX=84; BUDGET=860.0
    idpx={}
    for j in idc:
        mxl=max([len(x) for tg,x in cols[j]] or [0]); idpx[j]=int(min(132,max(PX,mxl*8.4+22)))
    # คอลัมน์เลขลำดับ/อ้างอิงสั้น (#, ดูที่ ฯลฯ: ทุกช่อง ≤3 ตัวอักษร) = แคบตามเนื้อหา ไม่ปล่อยให้กินที่ของช่องข้อความ
    if n>=3:
        for j,c in enumerate(cols):
            tds=[x for tg,x in c if tg=='td']
            if tds and max(len(x) for x in tds)<=3:
                hl=max([len(x) for tg,x in c if tg=='th'] or [0])
                idc.add(j); idpx[j]=int(min(96,max(46,max(len(x) for x in tds)*9.5+28,min(hl,8)*9.5+28)))
    # ตาราง Dashboard (3 คอลัมน์ ท้ายสุด = 'ดูที่') ใช้ความกว้างคอลัมน์ค่าเท่ากันทุกตาราง ให้ตำแหน่งตรงกันทั้งหน้า
    if n==3 and [x for tg,x in cols[2] if tg=='th'][:1]==[u'ดูที่']:
        idc.add(1); idpx[1]=270
    # คอลัมน์ตัวเลข: ให้หัวคอลัมน์ชิดขวาเหมือนตัวเลข (class num ทั้งหัวและช่อง)
    numcols=set()
    for j,c in enumerate(cols):
        body=[x for tg,x in c if tg=='td'] or [x for tg,x in c]
        avg_=sum(len(x) for x in body)/max(1,len(body))
        if (sum(numeric(x) for x in body)/max(1,len(body))>=0.6 and avg_<=16) or (j in idc and body and all(numeric(x) for x in body)) or j==1 and n==3 and [x for tg,x in cols[2] if tg=='th'][:1]==[u'ดูที่']: numcols.add(j)
    # คอลัมน์ที่ผู้เขียนใส่ class num ไว้ ≥50% ของช่อง = ถือเป็นคอลัมน์ตัวเลขด้วย (หัวต้องชิดขวาตาม)
    _mk={}
    for r_ in re.findall(r'<tr[^>]*>.*?</tr>',t,flags=re.S):
        _j=0
        for m_ in re.finditer(r'<td([^>]*)>',r_):
            _cs=re.search(r'colspan="?(\d+)',m_.group(1))
            if _cs: _j+=int(_cs.group(1)); continue
            _a=_mk.setdefault(_j,[0,0]); _a[1]+=1
            if re.search(r'class="[^"]*\bnum\b',m_.group(1)): _a[0]+=1
            _j+=1
    for _j,(_k,_n) in _mk.items():
        if _n and _k/float(_n)>=0.5: numcols.add(_j)
    def _al(tm):
        cnt=[0]
        def cell(m):
            tag,attr,body=m.group(1),m.group(2),m.group(3)
            j=cnt[0]; cs=re.search(r'colspan="?(\d+)',attr); cnt[0]+=int(cs.group(1)) if cs else 1
            if j in numcols and not cs and (len(tx(body))<=40 or tag=='th'):
                if re.search(r'class="[^"]*\bnum\b',attr): return m.group(0)
                if 'class="' in attr: attr=attr.replace('class="','class="num ',1)
                else: attr=attr+' class="num"'
            return '<%s%s>%s</%s>'%(tag,attr,body,tag)
        def row(rm):
            cnt[0]=0
            return re.sub(r'<(t[hd])([^>]*)>(.*?)</(?:th|td)>',cell,rm.group(0),flags=re.S)
        return re.sub(r'<tr[^>]*>.*?</tr>',row,tm,flags=re.S)
    t=_al(t)
    tokre=re.compile(r'[A-Za-z0-9][A-Za-z0-9.,%/+\-–:()฿~≈<>]*')
    # พื้นความกว้าง (px) ต่อคอลัมน์ — กันช่องซ้ายสุด/ช่องข้อความถูกบีบจนข้อความยืดลงเป็นแถวสูง และกันคำอังกฤษ/ตัวเลขถูกตัดกลางคำ
    floor=[]
    first_text=None
    for j,c in enumerate(cols):
        body=[x for tg,x in c if tg=='td'] or [x for tg,x in c]
        avg=sum(len(x) for x in body)/max(1,len(body))
        isnum=sum(numeric(x) for x in body)/max(1,len(body))>=0.6 and avg<=16
        tok=max([len(m) for x in [y for tg,y in c] for m in tokre.findall(x)] or [0])
        if j in idc: floor.append(idpx[j]); continue
        if isnum:
            mxn=max(len(x) for x in body); floor.append(min(max(64,min(mxn,22)*9.3+22,tok*9.3+22),190))
        else:
            base=130 if avg>12 else 100
            if first_text is None:
                first_text=j; base=max(base,min(avg*7+20,190))
            floor.append(min(max(base,tok*9.5+24),210))
    rest=[j for j in range(n) if j not in idc]
    R=BUDGET-sum(idpx.values())
    fs=sum(floor[j] for j in rest)
    if fs>R*0.97:   # พื้นรวมเกินความกว้างจริง = ลดพื้นลงตามสัดส่วน (ไม่ขยาย min-width จนตารางล้นกรอบ)
        k=R*0.97/fs
        for j in rest: floor[j]*=k
    px={j:0.0 for j in rest}; pool=list(rest); fixed={}
    while True:
        sw=sum(W[j] for j in pool) or 1
        Rl=R-sum(fixed.values())
        bad=[j for j in pool if Rl*W[j]/sw<floor[j]]
        if not bad: break
        for j in bad: fixed[j]=floor[j]; pool.remove(j)
        if not pool: break
    Rl=R-sum(fixed.values()); sw=sum(W[j] for j in pool) or 1
    for j in rest: px[j]=fixed[j] if j in fixed else max(0.0,Rl)*W[j]/sw
    totpx=sum(px.values()) or 1
    cg='<colgroup>'
    for j in range(n):
        if j in idc: cg+='<col style="width:%dpx">'%idpx[j]
        elif idc: cg+='<col style="width:calc((100%% - %dpx) * %.4f)">'%(sum(idpx.values()),px[j]/totpx)
        else: cg+='<col style="width:%.1f%%">'%(100.0*px[j]/totpx)
    cg+='</colgroup>'
    MW=[max(m,0) for m in MW]
    minw=int(max(520,min(sum(MW),820)))
    # ตารางกว้าง ≥6 คอลัมน์ที่มีช่องยาว >120 ตัวอักษร = 'dense' (ฟอนต์เล็กลง ระยะบรรทัดชิด) กันแถวสูง >320px โดยไม่ตัดเนื้อหา
    dense=n>=6 and any(len(x)>120 for c in cols for tg,x in c if tg=='td')
    t=t.replace('<table>','<table class="bal%s" style="min-width:%dpx">'%(' dn' if dense else '',minw)+cg,1)
    return t
s2=re.sub(r'<table\b.*?</table>',fix,s,flags=re.S)
css='table.bal{table-layout:fixed;width:100%}\ntable.bal th,table.bal td,table.bal td.num,table.bal th.num{white-space:normal;overflow-wrap:break-word}\ntable.bal td.num,table.bal th.num{white-space:normal}\ntable.bal.dn{font-size:.84rem;line-height:1.5}table.bal.dn th,table.bal.dn td{padding:6px 9px}\n'
if 'table.bal.dn{' not in s2 and 'table.bal{' in s2: s2=s2.replace('</style>','table.bal.dn{font-size:.84rem;line-height:1.5}table.bal.dn th,table.bal.dn td{padding:6px 9px}\n</style>',1)
if 'table.bal{' not in s2: s2=s2.replace('</style>',css+'</style>',1)
io.open(f,'w',encoding='utf-8').write(s2)
print('balanced tables:',s2.count('<table class="bal"'))
