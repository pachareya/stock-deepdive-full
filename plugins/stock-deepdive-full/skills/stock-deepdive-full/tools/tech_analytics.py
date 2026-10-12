# -*- coding: utf-8 -*-
"""tech_analytics.py <prices.csv> <out.json> <FROM yyyy-mm-dd> [results.json]
วิเคราะห์เชิงเทคนิคระดับลึกจาก CSV (หลังรอยต่อซีรีส์เท่านั้น) — ทุกตัวเลขสาวกลับ CSV ได้:
 swing log (รายเดือน 15% · รายสัปดาห์ 8% · ราคาปิด) พร้อมระยะเวลา/ขนาด · Fibonacci retracement ของขาขึ้นใหญ่ล่าสุด · Weinstein-style (SMA30 สัปดาห์ + ความชัน) ·
 volume-at-price (ถัง 0.5 บาท) · OBV · ATR/ความผันผวนเทียบประวัติ · drawdown · event study รอบประกาศงบ (results.json = [{"label","date","profit"}])"""
import csv, json, sys, datetime as dt, math, importlib.util, os
spec = importlib.util.spec_from_file_location('tc', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tech_chart.py'))
tc = importlib.util.module_from_spec(spec); spec.loader.exec_module(tc)

def main():
    p, out, frm = sys.argv[1], sys.argv[2], dt.date.fromisoformat(sys.argv[3])
    res_in = json.load(open(sys.argv[4])) if len(sys.argv) > 4 else []
    d = [r for r in tc.load(p) if r[0] >= frm]
    W = tc.resample(d, lambda x: x.isocalendar()[:2]); M = tc.resample(d, lambda x: (x.year, x.month))
    R = {'from': str(frm), 'bars': {'D': len(d), 'W': len(W), 'M': len(M)}}
    # swing log
    def swings(rows, pct):
        piv, pend = tc.zigzag(rows, pct)
        pts = [(str(a), round(b, 2), t) for a, b, t in piv] + [(str(pend[0]), round(pend[1], 2), pend[2] + '*')]
        log = []
        for i in range(1, len(pts)):
            a, b = pts[i - 1], pts[i]
            da = dt.date.fromisoformat(a[0]); db = dt.date.fromisoformat(b[0])
            log.append({'from': a[0], 'to': b[0], 'from_px': a[1], 'to_px': b[1], 'pct': round((b[1] / a[1] - 1) * 100, 1), 'months': round((db - da).days / 30.4, 1)})
        return pts, log
    R['swings_M'], R['swing_log_M'] = swings(M, 0.15)
    R['swings_W'], R['swing_log_W'] = swings(W, 0.08)
    # fibonacci: จากต่ำสุดของขาขึ้นใหญ่ (สวิงต่ำปิดรายเดือนที่เป็นจุดต่ำสุดของซีรีส์ใหม่) ถึงสูงสุดปิดเดือน
    lowrow = min(M, key=lambda r: r[4]); hirow = max(M, key=lambda r: r[4]); last = d[-1][4]
    lo, hi = lowrow[4], hirow[4]
    R['fib'] = {'low': lo, 'low_date': str(lowrow[0]), 'high': hi, 'high_date': str(hirow[0]), 'levels': {k: round(hi - (hi - lo) * k, 2) for k in (0.236, 0.382, 0.5, 0.618)},
                'retrace_now_pct': round((hi - last) / (hi - lo) * 100, 1), 'last': last}
    # Weinstein-style
    C = [r[4] for r in W]; s30 = tc.sma(C, 30)
    R['stage'] = {'sma30_now': round(s30[-1], 2), 'sma30_10w_ago': round(s30[-11], 2), 'slope_10w_pct': round((s30[-1] / s30[-11] - 1) * 100, 1), 'price_vs_sma30_pct': round((C[-1] / s30[-1] - 1) * 100, 1),
                  'weeks_below_sma30': next(i for i in range(len(C)) if C[-1 - i] >= s30[-1 - i]) if C[-1] < s30[-1] else 0}
    # volume at price (ถัง 0.5 บาท ด้วยราคาปิด·ปริมาณ)
    bins = {}
    for r in d: b = math.floor(r[4] / 0.5) * 0.5; bins[b] = bins.get(b, 0) + r[5]
    tot = sum(bins.values()); top = sorted(bins.items(), key=lambda x: -x[1])[:6]
    R['vap'] = {'total_M': round(tot / 1e6), 'top': [(b, round(b + 0.5, 1), round(v / tot * 100, 1)) for b, v in top],
                'share_at_12_13_pct': round(sum(v for b, v in bins.items() if 12 <= b < 13) / tot * 100, 1), 'share_above_now_pct': round(sum(v for b, v in bins.items() if b >= math.floor(last / 0.5) * 0.5 + 0.5) / tot * 100, 1)}
    # OBV
    obv = [0.0]
    for i in range(1, len(d)): obv.append(obv[-1] + (d[i][5] if d[i][4] > d[i - 1][4] else -d[i][5] if d[i][4] < d[i - 1][4] else 0))
    R['obv'] = {'now_M': round(obv[-1] / 1e6), 'chg_60d_M': round((obv[-1] - obv[-61]) / 1e6), 'price_chg_60d_pct': round((d[-1][4] / d[-61][4] - 1) * 100, 1),
                'obv_max_M': round(max(obv) / 1e6), 'obv_max_date': str(d[obv.index(max(obv))][0]), 'from_obv_max_M': round((obv[-1] - max(obv)) / 1e6)}
    # ATR / vol
    tr = [max(d[i][2] - d[i][3], abs(d[i][2] - d[i - 1][4]), abs(d[i][3] - d[i - 1][4])) for i in range(1, len(d))]
    atr = [sum(tr[i - 13:i + 1]) / 14 for i in range(13, len(tr))]
    atrp = [a / d[i + 14][4] * 100 for i, a in enumerate(atr)]
    rng20 = [(max(r[2] for r in d[i - 19:i + 1]) - min(r[3] for r in d[i - 19:i + 1])) / d[i][4] * 100 for i in range(19, len(d))]
    pct_rank = lambda x, arr: round(sum(1 for y in arr if y <= x) / len(arr) * 100)
    ret = [math.log(d[i][4] / d[i - 1][4]) for i in range(1, len(d))]
    rv = lambda n: math.sqrt(sum(x * x for x in ret[-n:]) / n) * math.sqrt(252) * 100
    allrv = [math.sqrt(sum(x * x for x in ret[i - 19:i + 1]) / 20) * math.sqrt(252) * 100 for i in range(19, len(ret))]
    R['vol'] = {'atr14': round(atr[-1], 2), 'atr14_pct': round(atrp[-1], 2), 'atr_pct_rank': pct_rank(atrp[-1], atrp), 'range20_pct': round(rng20[-1], 1), 'range20_rank': pct_rank(rng20[-1], rng20),
                'rv20_ann': round(rv(20), 1), 'rv20_rank': pct_rank(rv(20), allrv)}
    # drawdown
    peak = -1; dd = []
    for r in d:
        peak = max(peak, r[4]); dd.append((r[4] / peak - 1) * 100)
    pk = max(d, key=lambda r: r[4])
    R['dd'] = {'peak_close': pk[4], 'peak_date': str(pk[0]), 'now_pct': round(dd[-1], 1), 'max_pct': round(min(dd), 1), 'max_date': str(d[dd.index(min(dd))][0])}
    # event study
    idx = {r[0]: i for i, r in enumerate(d)}
    ev = []
    for e in res_in:
        t = dt.date.fromisoformat(e['date']); i = None
        for k in range(len(d)):
            if d[k][0] >= t: i = k; break
        if i is None or i + 20 >= len(d) + 0 and i + 1 >= len(d): continue
        base = d[i][4]; g = lambda n: round((d[min(i + n, len(d) - 1)][4] / base - 1) * 100, 1) if i + n < len(d) else None
        ev.append({'label': e['label'], 'date': str(d[i][0]), 'profit': e.get('profit'), 'base_close': base, 'r1': g(1), 'r5': g(5), 'r20': g(20)})
    R['events'] = ev
    json.dump(R, open(out, 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({k: R[k] for k in ('fib', 'stage', 'vap', 'obv', 'vol', 'dd')}, ensure_ascii=False, indent=1)); print(json.dumps(R['swing_log_M'], ensure_ascii=False)); print(json.dumps(R['swing_log_W'][-6:], ensure_ascii=False)); print(json.dumps(R['events'], ensure_ascii=False))

if __name__ == '__main__':
    main()
