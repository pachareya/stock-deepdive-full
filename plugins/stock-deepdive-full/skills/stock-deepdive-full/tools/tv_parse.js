// tv_parse.js — วางใน javascript_tool ของเบราว์เซอร์ในแอป ขณะอยู่หน้า https://www.tradingview.com/symbols/SET-<TICKER>/technicals/
// ขั้นตอน (ทำทีละกรอบ): คลิก "1 day" (ปุ่มเห็นอยู่) · คลิก "More" แล้วเลือก "1 week" / "1 month" ด้วยการคลิกพิกัดจริง (ปุ่มจาก find/ref และพารามิเตอร์ ?interval= ใช้ไม่ได้)
// เรียก window.parseTV() หลังรอ ~3 วินาทีทุกครั้งที่สลับกรอบ แล้วตรวจว่า RSI ต่างจากกรอบก่อนหน้า (กันอ่านซ้ำค่าเก่า)
// ไม่ใช้ตาราง Pivot (ค่ารายสัปดาห์ซ้ำกับรายเดือน และไม่ตรงสูตร Classic) · บันทึกผลเป็น 02_WORKING/paper/<TICKER>-tv-technicals_<วันที่>.json
window.parseTV=function(){const t=document.querySelector('main').innerText;
 const take=(a,b)=>{const i=t.indexOf(a);const j=t.indexOf(b,i+a.length);return t.slice(i,j).split('\n').map(x=>x.trim()).filter(x=>x)};
 const rows=l=>{const r={};l.forEach(x=>{const p=x.split('\t');if(p.length===3&&p[0]!=='Name')r[p[0]]={v:p[1],a:p[2]}});return r};
 const o={osc:rows(take('Oscillators\nName','Moving Averages\nName')),ma:rows(take('Moving Averages\nName','Pivots\nPivot'))};
 const gm=t.match(/Oscillators\s+(\w[\w ]*)\s+Sell\s+(\d+)\s+Neutral\s+(\d+)\s+Buy\s+(\d+)\s+Summary\s+([\w ]+)\s+Sell\s+(\d+)\s+Neutral\s+(\d+)\s+Buy\s+(\d+)\s+Moving Averages\s+([\w ]+)\s+Sell\s+(\d+)\s+Neutral\s+(\d+)\s+Buy\s+(\d+)/);
 if(gm)o.gauge={osc:[gm[1],+gm[2],+gm[3],+gm[4]],summary:[gm[5],+gm[6],+gm[7],+gm[8]],ma:[gm[9],+gm[10],+gm[11],+gm[12]]};
 o.price=(t.match(/\n([\d.]+)\nTHB/)||[])[1];return o};
