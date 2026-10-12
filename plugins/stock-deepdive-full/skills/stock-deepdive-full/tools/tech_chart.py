# -*- coding: utf-8 -*-
"""tech_chart.py <prices.csv> <outdir> [TICKER]  (3.24 · กราฟมุมเทคนิค 3 กรอบเวลา เป็น SVG ในหน้า ไม่ใช้บริการภายนอก)
สร้าง chart_M.svg chart_W.svg chart_D.svg + metrics.json ใน outdir
แผง: ราคาแท่งเทียน + EMA + ZigZag(ปิด) + แนวรับ/ต้านจากสวิง · ปริมาณ · Slow Stochastic 14,3,3 · RSI 14 · MACD 12,26,9
ตัวชี้วัดคำนวณเองจาก CSV (EMA เริ่มจาก SMA ช่วงแรก · RSI แบบ Wilder · Stoch %K = SMA3 ของ raw %K) แล้วเทียบกับ TradingView ใน metrics.json (ถ้ามี tv json)
⚠️ ตรวจก่อนใช้: ซีรีส์ราคาไม่ต่อเนื่องไหม (ปริมาณ 0 หลายวัน/ราคาค้าง = ซื้อขายถูกพัก · แท่งกระโดดผิดปกติ = ควบรวม/แตกพาร์) ถ้าใช่ให้ตัดข้อมูลด้วยอาร์กิวเมนต์ที่ 4 = วันเริ่ม (TRUE: 2023-03-03)
กรอบ: D = 130 แท่งล่าสุด · W = 104 แท่ง · M = ทุกแท่งในไฟล์ (EMA เดือนเฉพาะที่ข้อมูลพอ)"""
import csv, json, sys, os, datetime as dt, html

def load(p):
    r = []
    for x in csv.DictReader(open(p)):
        r.append((dt.date.fromisoformat(x['date']), float(x['open']), float(x['high']), float(x['low']), float(x['close']), float(x['volume'])))
    return r

def resample(rows, keyf):
    out, cur, k = [], None, None
    for d, o, h, l, c, v in rows:
        kk = keyf(d)
        if kk != k:
            if cur: out.append(cur)
            cur, k = [d, o, h, l, c, v], kk
        else:
            cur[2] = max(cur[2], h); cur[3] = min(cur[3], l); cur[4] = c; cur[5] += v; cur[0] = d
    if cur: out.append(cur)
    return [tuple(x) for x in out]

def sma(v, n):
    return [None if i + 1 < n else sum(v[i + 1 - n:i + 1]) / n for i in range(len(v))]

def ema(v, n):
    out = [None] * len(v)
    if len(v) < n: return out
    e = sum(v[:n]) / n; out[n - 1] = e; a = 2.0 / (n + 1)
    for i in range(n, len(v)):
        e = v[i] * a + e * (1 - a); out[i] = e
    return out

def rsi(c, n=14):
    out = [None] * len(c)
    if len(c) <= n: return out
    g = [max(c[i] - c[i - 1], 0) for i in range(1, len(c))]; l = [max(c[i - 1] - c[i], 0) for i in range(1, len(c))]
    ag, al = sum(g[:n]) / n, sum(l[:n]) / n
    out[n] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    for i in range(n, len(g)):
        ag = (ag * (n - 1) + g[i]) / n; al = (al * (n - 1) + l[i]) / n
        out[i + 1] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out

def stoch(h, l, c, n=14, k=3, d=3):
    raw = [None] * len(c)
    for i in range(n - 1, len(c)):
        hh, ll = max(h[i - n + 1:i + 1]), min(l[i - n + 1:i + 1])
        raw[i] = 50.0 if hh == ll else (c[i] - ll) / (hh - ll) * 100
    def sm(x, m):
        o = [None] * len(x)
        for i in range(len(x)):
            w = x[max(0, i - m + 1):i + 1]
            if i - m + 1 >= 0 and all(t is not None for t in w): o[i] = sum(w) / m
        return o
    K = sm(raw, k); D = sm(K, d)
    return K, D

def macd(c, f=12, s=26, g=9):
    ef, es = ema(c, f), ema(c, s)
    m = [None if a is None or b is None else a - b for a, b in zip(ef, es)]
    first = next((i for i, x in enumerate(m) if x is not None), None)
    if first is None: return [None] * len(c), [None] * len(c), [None] * len(c)
    sig = [None] * len(c); seq = m[first:]; e = ema(seq, g)
    for i, x in enumerate(e): sig[first + i] = x
    hist = [None if a is None or b is None else a - b for a, b in zip(m, sig)]
    return m, sig, hist

def zigzag(rows, pct):
    piv = []; hid, hip = rows[0][0], rows[0][4]; lod, lop = rows[0][0], rows[0][4]; direction = 0
    for d, o, h, l, c, v in rows[1:]:
        if direction >= 0 and c > hip: hid, hip = d, c
        if direction <= 0 and c < lop: lod, lop = d, c
        if direction == 0:
            if c >= lop * (1 + pct): piv.append((lod, lop, 'L')); direction = 1; hid, hip = d, c
            elif c <= hip * (1 - pct): piv.append((hid, hip, 'H')); direction = -1; lod, lop = d, c
        elif direction == 1:
            if c <= hip * (1 - pct): piv.append((hid, hip, 'H')); direction = -1; lod, lop = d, c
        else:
            if c >= lop * (1 + pct): piv.append((lod, lop, 'L')); direction = 1; hid, hip = d, c
    pend = (hid, hip, 'H') if direction == 1 else (lod, lop, 'L')
    return piv, pend

UP, DN = '#22c55e', '#ef4444'
GRID, TXT, TX2 = '#243444', '#dbe6f0', '#9fb0c2'
def fnum(x, d=2): return ('%.' + str(d) + 'f') % x

def seg_apply(fn, rows, k):
    """คำนวณตัวชี้วัดแยกก่อน/หลังรอยต่อซีรีส์ (k = index แถวแรกของช่วงหลัง) แล้วต่อกัน (ไม่ข้ามรอยต่อ)"""
    if not k: return fn(rows)
    a, b = fn(rows[:k]), fn(rows[k:])
    return a + b

MON = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
def fdate(x): return '%d %s %d' % (x.day, MON[x.month], x.year)

def chart(name, rows, nshow, emas, zzpct, ticker, tf_label, tickf, brk=None, brk_label=''):
    """rows = แท่งทั้งหมด · brk = วันแรกของซีรีส์ใหม่ (แท่งก่อนหน้าแสดงจางและไม่ต่อตัวชี้วัดข้ามรอยต่อ) · ข้อความในกราฟเป็นอังกฤษทั้งหมด"""
    C = [r[4] for r in rows]; H = [r[2] for r in rows]; L = [r[3] for r in rows]; V = [r[5] for r in rows]
    kbrk = next((i for i, r in enumerate(rows) if brk and r[0] >= brk), 0) if brk else 0
    def per(fn): return seg_apply(fn, rows, kbrk)
    E = {n: per(lambda rr, n=n: ema([r[4] for r in rr], n)) for n in emas}
    K = per(lambda rr: stoch([r[2] for r in rr], [r[3] for r in rr], [r[4] for r in rr])[0])
    Dd = per(lambda rr: stoch([r[2] for r in rr], [r[3] for r in rr], [r[4] for r in rr])[1])
    R = per(lambda rr: rsi([r[4] for r in rr]))
    M_ = per(lambda rr: macd([r[4] for r in rr])[0]); S_ = per(lambda rr: macd([r[4] for r in rr])[1]); HI = per(lambda rr: macd([r[4] for r in rr])[2])
    segs = [(0, kbrk), (kbrk, len(rows))] if kbrk else [(0, len(rows))]
    pivs = []
    for a, b in segs:
        if b - a > 5:
            pv, pe = zigzag(rows[a:b], zzpct); pivs.append((pv, pe))
    piv, pend = pivs[-1]
    n0 = max(0, len(rows) - nshow); idx = list(range(n0, len(rows))); N = len(idx)
    W, padL, padR = 720, 8, 62; pw = W - padL - padR
    hp, hv, hs, hr, hm, gap = 300, 64, 80, 80, 92, 26
    y0 = 34
    ytop = {'p': y0, 'v': y0 + hp + 10, 's': y0 + hp + 10 + hv + gap, 'r': y0 + hp + 10 + hv + gap + hs + gap, 'm': y0 + hp + 10 + hv + gap + hs + gap + hr + gap}
    Ht = ytop['m'] + hm + 30
    xs = lambda k: padL + (k + 0.5) * pw / N
    bw = max(1.5, pw / N * 0.62)
    lo = min(min(L[i] for i in idx), min([E[n][i] for n in emas for i in idx if E[n][i] is not None] or [1e9])); hi = max(H[i] for i in idx)
    pad = (hi - lo) * 0.06; lo -= pad; hi += pad
    py = lambda v: ytop['p'] + hp - (v - lo) / (hi - lo) * hp
    old = lambda i: bool(kbrk) and i < kbrk
    o = ['<svg viewBox="0 0 %d %d" width="100%%" role="img" aria-label="%s %s chart" font-size="11" fill="%s" font-family="system-ui,-apple-system,Segoe UI,sans-serif" style="min-width:560px;display:block">' % (W, Ht, html.escape(ticker), html.escape(tf_label), TXT)]
    last = rows[-1]
    o.append('<text x="%d" y="14" font-size="13" font-weight="700">%s · %s</text>' % (padL, html.escape(ticker), html.escape(tf_label)))
    o.append('<text x="%d" y="28" fill="%s">O %s  H %s  L %s  C %s  · %s</text>' % (padL, TX2, fnum(last[1]), fnum(last[2]), fnum(last[3]), fnum(last[4]), fdate(last[0])))
    step = 1
    for cand in (0.1, 0.2, 0.25, 0.5, 1, 2, 2.5, 5, 10):
        if (hi - lo) / cand <= 8: step = cand; break
    g = (int(lo / step) + 1) * step
    while g < hi:
        y = py(g); o.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="%s" stroke-width=".6"/><text x="%d" y="%.1f" fill="%s">%s</text>' % (padL, padL + pw, y, y, GRID, padL + pw + 4, y + 3, TX2, fnum(g, 2 if step < 1 else 1)))
        g += step
    lastlab = None; lastx = -999
    for k, i in enumerate(idx):
        lab = tickf(rows[i][0])
        if lab != lastlab and lab and xs(k) - lastx >= 52:
            lastlab = lab; lastx = xs(k)
            o.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" stroke="%s" stroke-width=".5"/><text x="%.1f" y="%d" fill="%s" text-anchor="middle">%s</text>' % (xs(k), xs(k), ytop['p'], ytop['m'] + hm, GRID, xs(k), ytop['m'] + hm + 14, TX2, html.escape(lab)))
    # รอยต่อซีรีส์
    if kbrk and kbrk in idx:
        kx = xs(idx.index(kbrk)) - pw / N / 2
        o.append('<rect x="%d" y="%d" width="%.1f" height="%d" fill="#ffffff" opacity=".035"/>' % (padL, ytop['p'], kx - padL, ytop['m'] + hm - ytop['p']))
        o.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" stroke="#c9974f" stroke-width="1" stroke-dasharray="2 3"/>' % (kx, kx, ytop['p'], ytop['m'] + hm))
        o.append('<text x="%.1f" y="%d" fill="#c9974f" font-size="10" text-anchor="end">%s</text>' % (kx - 4, ytop['p'] + 38, html.escape(brk_label.split('|')[0])))
        o.append('<text x="%.1f" y="%d" fill="#c9974f" font-size="10">%s</text>' % (kx + 4, ytop['p'] + 38, html.escape(brk_label.split('|')[1] if '|' in brk_label else '')))
    for k, i in enumerate(idx):
        _, op, h_, l_, c_, _v = rows[i]; col = UP if c_ >= op else DN; x = xs(k); opa = ' opacity=".42"' if old(i) else ''
        o.append('<line x1="%.1f" x2="%.1f" y1="%.1f" y2="%.1f" stroke="%s" stroke-width="1"%s/>' % (x, x, py(h_), py(l_), col, opa))
        yb, yt = py(max(op, c_)), py(min(op, c_)); o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"%s/>' % (x - bw / 2, yb, bw, max(1, yt - yb), col, opa))
    dates = [rows[i][0] for i in idx]
    for (pv, pe) in pivs:
        pts = []
        for d, p in [(d, p) for d, p, t in pv] + [(pe[0], pe[1])]:
            if d in dates: pts.append((xs(dates.index(d)), py(p)))
        if len(pts) > 1:
            o.append('<polyline points="%s" fill="none" stroke="#c9974f" stroke-width="1.1" stroke-dasharray="4 3" opacity=".9"/>' % ' '.join('%.1f,%.1f' % p for p in pts))
    ecol = {10: '#f59e0b', 20: '#3b82f6', 50: '#a78bfa', 100: '#2dd4bf', 200: '#e6edf3'}
    leg = []
    for n in emas:
        for (a, b) in segs:
            seg = [(xs(k), py(E[n][i])) for k, i in enumerate(idx) if a <= i < b and E[n][i] is not None]
            if len(seg) > 1: o.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="1.4"%s/>' % (' '.join('%.1f,%.1f' % p for p in seg), ecol.get(n, '#888'), ' opacity=".5"' if (kbrk and b == kbrk) else ''))
        leg.append((n, ecol.get(n, '#888'), E[n][-1]))
    lx = padL + 4; ly = ytop['p'] + 12
    for n, col, lv in leg:
        o.append('<rect x="%d" y="%d" width="10" height="3" fill="%s"/><text x="%d" y="%d" fill="%s">EMA %d  %s</text>' % (lx, ly - 6, col, lx + 14, ly, TX2, n, '—' if lv is None else fnum(lv)))
        lx += 92
    o.append('<line x1="%d" x2="%d" y1="%d" y2="%d" stroke="#c9974f" stroke-width="1.1" stroke-dasharray="4 3"/><text x="%d" y="%d" fill="%s">ZigZag (close, %d%%)</text>' % (lx, lx + 12, ly - 4, ly - 4, lx + 16, ly, TX2, round(zzpct * 100)))
    o.append('<rect x="%d" y="%.1f" width="%d" height="14" rx="2" fill="%s"/><text x="%d" y="%.1f" fill="#fff" font-weight="700">%s</text>' % (padL + pw + 1, py(last[4]) - 7, padR - 4, UP if last[4] >= last[1] else DN, padL + pw + 4, py(last[4]) + 4, fnum(last[4])))
    vmax = max(V[i] for i in idx)
    o.append('<text x="%d" y="%d" fill="%s">Volume (million shares)</text>' % (padL, ytop['v'] + 10, TX2))
    for k, i in enumerate(idx):
        h_ = V[i] / vmax * (hv - 14); col = UP if rows[i][4] >= rows[i][1] else DN
        o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" opacity="%s"/>' % (xs(k) - bw / 2, ytop['v'] + hv - h_, bw, h_, col, '.25' if old(i) else '.55'))
    o.append('<text x="%d" y="%d" fill="%s">%s</text>' % (padL + pw + 4, ytop['v'] + 12, TX2, fnum(vmax / 1e6, 0)))
    def panel(key, title, h, vmin, vmax_, lines, hlines=(), hist=None, valtxt=''):
        yt = ytop[key]; o.append('<text x="%d" y="%d" fill="%s">%s</text>' % (padL, yt - 6, TX2, html.escape(title)))
        o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="%s" stroke-width=".7"/>' % (padL, yt, pw, h, GRID))
        yy = lambda v: yt + h - (v - vmin) / (vmax_ - vmin) * h
        for hv_ in hlines:
            o.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="%s" stroke-width=".6" stroke-dasharray="3 3"/><text x="%d" y="%.1f" fill="%s">%s</text>' % (padL, padL + pw, yy(hv_), yy(hv_), TX2, padL + pw + 4, yy(hv_) + 3, TX2, fnum(hv_, 0)))
        if hist is not None:
            z = yy(0)
            for k, i in enumerate(idx):
                x = hist[i]
                if x is None: continue
                col = UP if x >= 0 else DN
                o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" opacity="%s"/>' % (xs(k) - bw / 2, min(z, yy(x)), bw, max(.6, abs(yy(x) - z)), col, '.35' if old(i) else '.7'))
            o.append('<line x1="%d" x2="%d" y1="%.1f" y2="%.1f" stroke="%s" stroke-width=".6"/>' % (padL, padL + pw, z, z, TX2))
        for series, col in lines:
            for (a, b) in segs:
                seg = [(xs(k), yy(series[i])) for k, i in enumerate(idx) if a <= i < b and series[i] is not None]
                if len(seg) > 1: o.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="1.3"%s/>' % (' '.join('%.1f,%.1f' % p for p in seg), col, ' opacity=".5"' if (kbrk and b == kbrk) else ''))
        o.append('<text x="%d" y="%d" fill="%s" text-anchor="end">%s</text>' % (padL + pw - 4, yt + 11, TXT, valtxt))
    kv = lambda x: '—' if x is None else fnum(x, 1)
    panel('s', 'Slow Stochastic 14,3,3 (blue = %K, orange = %D)', hs, 0, 100, [(K, '#3b82f6'), (Dd, '#f59e0b')], hlines=(20, 80), valtxt='K %s · D %s' % (kv(K[-1]), kv(Dd[-1])))
    panel('r', 'RSI 14', hr, 0, 100, [(R, '#a78bfa')], hlines=(30, 50, 70), valtxt='RSI %s' % kv(R[-1]))
    mm = [x for x in M_[n0:] + S_[n0:] + HI[n0:] if x is not None]; mv = max(abs(min(mm)), abs(max(mm))) * 1.15
    panel('m', 'MACD 12,26,9 (blue = MACD, orange = signal, bars = histogram)', hm, -mv, mv, [(M_, '#3b82f6'), (S_, '#f59e0b')], hist=HI, valtxt='MACD %s · signal %s · hist %s' % (fnum(M_[-1], 2), fnum(S_[-1], 2), fnum(HI[-1], 2)))
    o.append('</svg>')
    met = {'tf': tf_label, 'last_date': str(last[0]), 'close': last[4], 'bars_shown': N, 'bars_total': len(rows), 'break_index': kbrk,
           'ema': {str(n): E[n][-1] for n in emas}, 'stoch_k': K[-1], 'stoch_d': Dd[-1], 'rsi': R[-1], 'macd': M_[-1], 'macd_signal': S_[-1], 'macd_hist': HI[-1],
           'swings': [(str(d), round(p, 2), t) for d, p, t in piv[-6:]], 'pending': (str(pend[0]), round(pend[1], 2), pend[2]),
           'vol_last': V[-1], 'vol_avg20': sum(V[-20:]) / min(20, len(V))}
    return '\n'.join(o), met

def main():
    """tech_chart.py <csv> <outdir> <TICKER> [BREAK_YYYY-MM-DD]  — BREAK = วันแรกของซีรีส์ใหม่ (ควบรวม/แตกพาร์): ก่อนหน้าแสดงจาง ตัวชี้วัดแยกช่วง"""
    p, out = sys.argv[1], sys.argv[2]; ticker = sys.argv[3] if len(sys.argv) > 3 else 'TICKER'
    brk = dt.date.fromisoformat(sys.argv[4]) if len(sys.argv) > 4 else None
    os.makedirs(out, exist_ok=True)
    d = load(p)
    dpost = [r for r in d if (not brk or r[0] >= brk)]
    W = resample(d, lambda x: x.isocalendar()[:2]); M = resample(d, lambda x: (x.year, x.month))
    mt = lambda x: ("%s '%s" % (MON[x.month], str(x.year)[2:])) if x.month in (1, 7) else ''
    wt = lambda x: ("%s '%s" % (MON[x.month], str(x.year)[2:])) if (x.month in (1, 7) and x.day <= 7) else ''
    dtk = lambda x: MON[x.month] if x.day <= 3 else ''
    label = 'Merger | 1 Mar 2023: new share base'
    res = {}
    # 3.25: หน้าต่างเวลา — มีข้อมูลหุ้นชุดเดียวกัน (หลัง BREAK) ≥10 ปี ใช้ 10 ปี (เดือน 120 · สัปดาห์ 520) ไม่งั้นใช้เท่าที่มี (สูงสุด 5 ปีแบบ TRUE) · เส้นยาวเพิ่มเมื่อข้อมูลพอ: สัปดาห์ EMA200 เมื่อ ≥260 สัปดาห์ · เดือน EMA50 เมื่อ ≥72 เดือน
    Mp = [r for r in M if (not brk or r[0] >= brk)]; Wp = [r for r in W if (not brk or r[0] >= brk)]
    emaM = (10, 20, 50) if len(Mp) >= 72 else (10, 20); emaW = (20, 50, 100, 200) if len(Wp) >= 260 else (20, 50, 100)
    nM = min(len(M), 120); nW = min(len(W), 520)
    for key, rows, n, emas, zz, lab, f, b in (('M', M, nM, emaM, 0.15, 'Monthly', mt, brk), ('W', W, nW, emaW, 0.08, 'Weekly', wt, brk), ('D', dpost, 150, (20, 50, 100, 200), 0.05, 'Daily', dtk, None)):
        svg, met = chart(key, rows, n, emas, zz, ticker, lab, f, brk=b, brk_label=label)
        open(os.path.join(out, 'chart_%s.svg' % key), 'w').write(svg); res[key] = met
    json.dump(res, open(os.path.join(out, 'metrics.json'), 'w'), ensure_ascii=False, indent=1)
    print('ok', {k: v['bars_shown'] for k, v in res.items()})

if __name__ == '__main__':
    main()
