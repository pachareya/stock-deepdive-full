# Stock DeepDive Full

deep dive หุ้นครบวงจร ต่อยอดจาก `stock-deepdive-lite`: งบยื่นจริง + คลิป Opportunity Day + เทียบคู่แข่ง + ตรวจเลขอิสระ + Dashboard/ภาคผนวก + เครื่องคิดสถานการณ์

ข้อมูลประกอบการศึกษา ไม่ใช่คำแนะนำการลงทุน

## ติดตั้ง (Claude Desktop แท็บ Code)

1. เปิดแอป Claude → แท็บ **Code** → เริ่ม session แบบ local
2. กดปุ่ม **+** ข้างช่องพิมพ์ → **Plugins** → **Add plugin**
3. **ถ้ายังไม่เคยเพิ่ม** ให้เพิ่มแหล่งนี้ก่อน: `BoonchuTummeng/stock-deepdive` แล้วติดตั้ง **stock-deepdive-lite** (ตัวดึงงบและตรวจเลข ที่ตัวนี้ต้องใช้)
4. เพิ่มแหล่งนี้: `pachareya/stock-deepdive-full` แล้วติดตั้ง **stock-deepdive-full**

## วิธีใช้

สนใจหุ้นตัวไหน เช่น PTT ลองพิมพ์ในช่องแชทว่า `PTT deep dive full` (เปลี่ยน PTT เป็นชื่อหุ้นที่สนใจ)

Claude จะบอกเวลาที่ใช้ (หลายชั่วโมง) และขออนุญาตก่อนดาวน์โหลดไฟล์ทุกครั้ง

ถอดคลิป Opportunity Day ต้องมี CLI เพิ่ม: `python -m pip install "git+https://github.com/BankTheGreat/earnings-call-digest.git"` (Claude จะบอกเมื่อถึงขั้นนั้น)
