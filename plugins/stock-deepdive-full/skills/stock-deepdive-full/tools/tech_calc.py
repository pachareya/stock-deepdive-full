#!/usr/bin/env python3
"""tech_calc.py — มุมเทคนิค D/W/M จากไฟล์ราคา OHLCV (ทุกตัวเลขสาวกลับ CSV ได้)
ใช้: python3 tech_calc.py <prices.csv> <out.json> [--zz D W M]   (CSV: date,open,high,low,close,volume)
นิยาม (ล็อกไว้ ห้ามเปลี่ยนรายตัว):
 - SMA = ค่าเฉลี่ยราคาปิดธรรมดา · RSI14 = Wilder · ZigZag (บนราคาปิด) = เปลี่ยนทิศเมื่อราคาปิดกลับจากจุดสุดโต่ง >= เกณฑ์ (D 5% · W 8% · M 15%)
 - แนวโน้ม: จุดสวิง 2 จุดล่าสุดของแต่ละฝั่ง สูงกว่า/ต่ำกว่ากัน → ขึ้น (HH+HL) · ลง (LH+LL) · อื่นๆ = แกว่งไม่ชัด
 - แนวรับ/ต้าน = จุดสวิงที่ยืนยันแล้ว + 52w high/low (ไม่ใช่ค่าพยากรณ์)
 - สัปดาห์ = จันทร์-ศุกร์ ปิด = วันทำการสุดท้าย · เดือน = เดือนปฏิทิน (เดือนล่าสุดยังไม่ปิดถ้าไม่ใช่วันสิ้นเดือน → ติดป้าย partial)
"""
import csv, json, sys, datetime as dt

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

def sma(vals, n):
    return sum(vals[-n:]) / n if len(vals) >= n else None

def rsi(closes, n=14):
    if len(closes) <= n: return None
    g = [max(closes[i] - closes[i-1], 0) for i in range(1, len(closes))]
    l = [max(closes[i-1] - closes[i], 0) for i in range(1, len(closes))]
    ag, al = sum(g[:n]) / n, sum(l[:n]) / n
    for i in range(n, len(g)):
        ag = (ag * (n-1) + g[i]) / n; al = (al * (n-1) + l[i]) / n
    return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)

def zigzag(rows, pct):
    """ZigZag บนราคาปิด (กันสวิงซ้ำในแท่งเดียว) · คืนจุดสวิงที่ยืนยันแล้ว + จุดสุดโต่งปัจจุบันที่ยังไม่ยืนยัน"""
    piv = []
    hid, hip = rows[0][0], rows[0][4]
    lod, lop = rows[0][0], rows[0][4]
    direction = 0
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
    pending = (hid, hip, 'H') if direction == 1 else (lod, lop, 'L')
    return piv, pending, direction

def trend(piv):
    H = [p for p in piv if p[2] == 'H'][-2:]; L = [p for p in piv if p[2] == 'L'][-2:]
    if len(H) < 2 or len(L) < 2: return 'ข้อมูลไม่พอ'
    hh, hl = H[1][1] > H[0][1], L[1][1] > L[0][1]
    lh, ll = H[1][1] < H[0][1], L[1][1] < L[0][1]
    return 'ขึ้น (HH+HL)' if hh and hl else 'ลง (LH+LL)' if lh and ll else 'แกว่งไม่ชัด (สวิงสองฝั่งสวนกัน)'

def block(name, rows, ma_n, zz):
    cl = [r[4] for r in rows]
    piv, pend, dire = zigzag(rows, zz)
    last = rows[-1]
    b = {'tf': name, 'last_date': str(last[0]), 'close': cl[-1], 'open': last[1], 'high': last[2], 'low': last[3],
         'rsi14': None if rsi(cl) is None else round(rsi(cl), 1), 'zz_pct': zz,
         'swings': [(str(d), round(p, 2), t) for d, p, t in piv[-6:]], 'pending': (str(pend[0]), round(pend[1], 2), pend[2]),
         'trend': trend(piv), 'sma': {}}
    for n in ma_n:
        m = sma(cl, n)
        b['sma'][n] = None if m is None else {'v': round(m, 3), 'pct': round((cl[-1] / m - 1) * 100, 1)}
    return b

def main():
    p, out = sys.argv[1], sys.argv[2]
    d = load(p)
    if '--from' in sys.argv: d = [r for r in d if r[0] >= dt.date.fromisoformat(sys.argv[sys.argv.index('--from') + 1])]   # เริ่มหลังซีรีส์ไม่ต่อเนื่อง (ควบรวม/พักซื้อขาย)
    D = d
    W = resample(d, lambda x: x.isocalendar()[:2])
    M = resample(d, lambda x: (x.year, x.month))
    res = {'source_csv': p, 'rows': len(d), 'first': str(d[0][0]), 'last': str(d[-1][0])}
    res['D'] = block('วัน', D, (20, 50, 200), 0.05)
    res['W'] = block('สัปดาห์', W, (10, 30, 40), 0.08)
    res['M'] = block('เดือน', M, (6, 12, 24), 0.15)
    lastd = d[-1][0]
    nxt = lastd + dt.timedelta(days=1)
    res['M']['partial'] = (lastd.month == (lastd + dt.timedelta(days=7)).month)
    res['W']['partial'] = lastd.weekday() != 4
    y = [r for r in d if r[0] > lastd - dt.timedelta(days=365)]
    res['52w'] = {'high': max(r[2] for r in y), 'high_date': str(max(y, key=lambda r: r[2])[0]),
                  'low': min(r[3] for r in y), 'low_date': str(min(y, key=lambda r: r[3])[0])}
    cl = [r[4] for r in d]
    def ret(n): return round((cl[-1] / cl[-1-n] - 1) * 100, 1) if len(cl) > n else None
    res['ret'] = {'1M(21d)': ret(21), '3M(63d)': ret(63), '6M(126d)': ret(126), '1Y(252d)': ret(252)}
    vol = [r[5] for r in d]
    res['vol'] = {'last': vol[-1], 'avg20': round(sum(vol[-20:]) / 20), 'ratio_last_vs_avg20': round(vol[-1] / (sum(vol[-20:]) / 20), 2),
                  'avg5_vs_avg20': round((sum(vol[-5:]) / 5) / (sum(vol[-20:]) / 20), 2)}
    json.dump(res, open(out, 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))

main()
