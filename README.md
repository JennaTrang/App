# Lịch âm & nhắc ngày cúng

Tạo file lịch `.ics` để nhập vào điện thoại (iPhone, Android/Google Calendar):

| File | Nội dung |
|---|---|
| `lich/ngay-cung-le.ics` | Mùng 1, Rằm hằng tháng (cả tháng nhuận) và các lễ Tết âm lịch. **Mỗi ngày nhắc trước 2 ngày lúc 9:00 sáng.** |
| `lich/lich-am-hang-ngay.ics` | Ngày âm lịch của mọi ngày (ví dụ `15/7 ÂL`), không nhắc. |

Âm lịch tính theo giờ Việt Nam (UTC+7), nên chính xác hơn lịch âm Trung Quốc có sẵn trên điện thoại.

Lễ có trong lịch: Tết Nguyên Đán (mùng 1–3), Vía Thần Tài (10/1), Rằm tháng Giêng,
Tết Hàn Thực (3/3), Giỗ Tổ Hùng Vương (10/3), Phật Đản (15/4), Tết Đoan Ngọ (5/5),
Rằm tháng Bảy – Vu Lan (15/7), Trung Thu (15/8), Tết Hạ Nguyên (15/10),
Ông Công Ông Táo (23/12), Tất niên & Giao thừa.

## Tạo lại lịch

Chỉ cần Python 3.8+ (không cần cài thêm thư viện):

```bash
python3 tao_lich.py                                    # từ hôm nay đến hết năm sau nữa
python3 tao_lich.py --tu 2027-01-01 --den 2030-12-31   # khoảng tuỳ chọn
python3 tao_lich.py --ngay-truoc 1 --gio-nhac 18       # nhắc 18:00 hôm trước
python3 -m unittest -v                                 # chạy kiểm tra
```

## Đưa vào điện thoại

**iPhone:** gửi file `.ics` cho chính mình (Mail/AirDrop/Files) → mở file → *Thêm tất cả*
→ chọn *Lịch mới*. Lời nhắc trong file được giữ nguyên.

**Android / Google Calendar:** vào calendar.google.com trên máy tính → *Cài đặt* →
*Nhập và xuất* → tạo lịch mới tên "Ngày cúng" trước, rồi nhập file vào lịch đó.
Google **bỏ qua lời nhắc trong file**, nên vào cài đặt của lịch "Ngày cúng" →
*Thông báo về sự kiện cả ngày* → đặt **2 ngày trước lúc 9:00**.
