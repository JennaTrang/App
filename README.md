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

# Chỉ đường né kẹt xe (Google Maps)

`chi_duong.py` tìm đường **ưu tiên đoạn không kẹt hoặc ít kẹt xe**. Trên Google Maps,
đoạn kẹt xe tô **đỏ**, đoạn đông xe tô **cam**. Công cụ lấy mọi tuyến Google gợi ý,
đo số km đỏ/cam của từng tuyến, rồi chọn tuyến **ít đỏ nhất → ít cam nhất → nhanh nhất**.
Tuyến được chọn không chậm hơn tuyến nhanh nhất quá 15 phút (đổi bằng `--cham-toi-da`).

Kết quả là một link Google Maps có sẵn 3 điểm đi qua nằm trên tuyến ít kẹt đó.
Mở link trên điện thoại thì Google Maps sẽ dẫn đúng tuyến này, thay vì tự chọn tuyến khác.

```bash
export GOOGLE_MAPS_API_KEY="khoá-của-bạn"
python3 chi_duong.py "Chợ Bến Thành" "Sân bay Tân Sơn Nhất"
python3 chi_duong.py "Nhà thờ Đức Bà" "Landmark 81" --xe-may      # tính đường xe máy
python3 chi_duong.py "A" "B" --cham-toi-da 25 --mo                # chịu chậm 25 phút, mở link luôn
```

Ví dụ kết quả:

```
Tìm được 3 tuyến:
   1. Võ Văn Kiệt: 9.8 km, 32 phút (kẹt thêm 12 phút) | đỏ 2.1 km, cam 1.4 km
 → 2. Nguyễn Thị Minh Khai: 10.6 km, 35 phút (kẹt thêm 4 phút) | đỏ 0.0 km, cam 0.6 km
   3. Điện Biên Phủ: 11.2 km, 38 phút (kẹt thêm 9 phút) | đỏ 0.9 km, cam 0.3 km

Đã chọn tuyến 2: ít kẹt xe nhất.
```

**Lấy khoá API:** vào console.cloud.google.com → tạo dự án → bật **Routes API** →
*Credentials* → *Create API key*. Google cho dùng miễn phí một hạn mức hằng tháng
(cần gắn thẻ thanh toán).

Lưu ý:
- Tình trạng kẹt xe là của **lúc chạy lệnh**; nên chạy ngay trước khi đi.
- Các điểm đi qua hiện thành điểm dừng trên Google Maps: cứ chạy qua, Maps tự dẫn tiếp.
- Link mở Google Maps ở chế độ ô tô; với `--xe-may` tuyến được chọn theo xe máy,
  bạn có thể bấm sang biểu tượng xe máy trong Maps (các điểm đi qua vẫn giữ).
