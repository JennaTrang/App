#!/usr/bin/env python3
"""Tạo file lịch .ics để nhập vào điện thoại.

Tạo hai file:
  - ngay-cung-le.ics : các ngày cúng (mùng 1, rằm, lễ Tết âm lịch),
                       mỗi ngày có nhắc trước 2 ngày lúc 9:00 sáng.
  - lich-am-hang-ngay.ics : ngày âm lịch của mọi ngày (không nhắc),
                       để xem âm lịch ngay trên lịch điện thoại.

Cách dùng:
  python3 tao_lich.py                      # từ hôm nay đến hết năm sau nữa
  python3 tao_lich.py --tu 2027-01-01 --den 2027-12-31 --gio-nhac 18
"""

import argparse
import os
import zlib
from datetime import date, datetime, timedelta, timezone

from amlich import solar_to_lunar, ten_nam

# Lễ cố định theo ngày âm lịch (chỉ áp dụng cho tháng thường, không nhuận).
LE_AM_LICH = {
    (1, 1): "Tết Nguyên Đán (Mùng 1 Tết)",
    (2, 1): "Mùng 2 Tết",
    (3, 1): "Mùng 3 Tết",
    (10, 1): "Vía Thần Tài",
    (15, 1): "Rằm tháng Giêng (Tết Nguyên Tiêu)",
    (3, 3): "Tết Hàn Thực",
    (10, 3): "Giỗ Tổ Hùng Vương",
    (15, 4): "Lễ Phật Đản",
    (5, 5): "Tết Đoan Ngọ",
    (15, 7): "Rằm tháng Bảy (Vu Lan, Xá tội vong nhân)",
    (15, 8): "Tết Trung Thu",
    (15, 10): "Tết Hạ Nguyên (Rằm tháng Mười)",
    (23, 12): "Ông Công Ông Táo về trời",
}


def nhan_am_lich(ngay, thang, nhuan):
    return f"{ngay}/{thang}{' nhuận' if nhuan else ''} ÂL"


def ngay_cung(tu, den):
    """Danh sách (ngày dương, tên lễ, mô tả) cần cúng trong khoảng [tu, den]."""
    ket_qua = []
    d = tu
    while d <= den:
        ngay, thang, nam, nhuan = solar_to_lunar(d)
        ten = []
        if not nhuan and (ngay, thang) in LE_AM_LICH:
            ten.append(LE_AM_LICH[(ngay, thang)])
        elif ngay == 1:
            ten.append(f"Mùng 1 tháng {thang}{' nhuận' if nhuan else ''}")
        elif ngay == 15:
            ten.append(f"Rằm tháng {thang}{' nhuận' if nhuan else ''}")
        # Giao thừa: ngày cuối tháng Chạp (29 hoặc 30), ngày hôm sau là Mùng 1 Tết.
        ngay_sau = solar_to_lunar(d + timedelta(days=1))
        if ngay_sau[0] == 1 and ngay_sau[1] == 1 and not ngay_sau[3]:
            ten.append("Tất niên & Giao thừa")
        if ten:
            mo_ta = f"Ngày {nhan_am_lich(ngay, thang, nhuan)}, năm {ten_nam(nam)}"
            ket_qua.append((d, " – ".join(ten), mo_ta))
        d += timedelta(days=1)
    return ket_qua


def _escape(text):
    return (text.replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", "\\n"))


def _fold(line):
    """Gấp dòng dài theo RFC 5545 (tối đa 75 byte, không cắt giữa ký tự UTF-8)."""
    out, cur, limit = [], b"", 75
    for ch in line:
        b = ch.encode("utf-8")
        if len(cur) + len(b) > limit:
            out.append(cur.decode("utf-8"))
            cur, limit = b"", 74  # dòng tiếp theo bắt đầu bằng 1 dấu cách
        cur += b
    out.append(cur.decode("utf-8"))
    return "\r\n ".join(out)


def tao_ics(ten_lich, su_kien, gio_nhac=None, ngay_truoc=1):
    """su_kien: list (date, tiêu đề, mô tả).

    gio_nhac: giờ báo nhắc; ngay_truoc: báo trước bao nhiêu ngày.
    """
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dong = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//lich-am-viet//tao_lich.py//VI",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(ten_lich)}",
        "X-WR-TIMEZONE:Asia/Ho_Chi_Minh",
    ]
    for d, tieu_de, mo_ta in su_kien:
        dong += [
            "BEGIN:VEVENT",
            f"UID:{d:%Y%m%d}-{zlib.crc32(ten_lich.encode()):08x}@lich-am-viet",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{d:%Y%m%d}",
            f"DTEND;VALUE=DATE:{d + timedelta(days=1):%Y%m%d}",
            f"SUMMARY:{_escape(tieu_de)}",
            f"DESCRIPTION:{_escape(mo_ta)}",
            "TRANSP:TRANSPARENT",
        ]
        if gio_nhac is not None:
            # Sự kiện cả ngày bắt đầu lúc 00:00; nhắc (24*ngày - giờ) tiếng
            # trước, tức là đúng `gio_nhac` giờ của `ngay_truoc` ngày trước.
            truoc = "Ngày mai" if ngay_truoc == 1 else f"Còn {ngay_truoc} ngày nữa"
            dong += [
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                f"DESCRIPTION:{_escape(truoc + ': ' + tieu_de)}",
                f"TRIGGER:-PT{24 * ngay_truoc - gio_nhac}H",
                "END:VALARM",
            ]
        dong.append("END:VEVENT")
    dong.append("END:VCALENDAR")
    return "\r\n".join(_fold(x) for x in dong) + "\r\n"


def main():
    hom_nay = date.today()
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tu", type=date.fromisoformat, default=hom_nay,
                   help="ngày bắt đầu (YYYY-MM-DD), mặc định hôm nay")
    p.add_argument("--den", type=date.fromisoformat, default=date(hom_nay.year + 2, 12, 31),
                   help="ngày kết thúc (YYYY-MM-DD), mặc định hết năm sau nữa")
    p.add_argument("--gio-nhac", type=int, default=9, choices=range(0, 24), metavar="0-23",
                   help="giờ báo nhắc, mặc định 9 (9:00 sáng)")
    p.add_argument("--ngay-truoc", type=int, default=2, choices=range(1, 8), metavar="1-7",
                   help="báo trước bao nhiêu ngày, mặc định 2")
    p.add_argument("--thu-muc", default="lich", help="thư mục lưu file .ics")
    a = p.parse_args()

    os.makedirs(a.thu_muc, exist_ok=True)

    cung = ngay_cung(a.tu, a.den)
    with open(os.path.join(a.thu_muc, "ngay-cung-le.ics"), "w", encoding="utf-8", newline="") as f:
        f.write(tao_ics("Ngày cúng âm lịch", cung, gio_nhac=a.gio_nhac, ngay_truoc=a.ngay_truoc))

    hang_ngay = []
    d = a.tu
    while d <= a.den:
        ngay, thang, nam, nhuan = solar_to_lunar(d)
        tieu_de = nhan_am_lich(ngay, thang, nhuan)
        hang_ngay.append((d, tieu_de, f"Năm {ten_nam(nam)}"))
        d += timedelta(days=1)
    with open(os.path.join(a.thu_muc, "lich-am-hang-ngay.ics"), "w", encoding="utf-8", newline="") as f:
        f.write(tao_ics("Âm lịch", hang_ngay))

    print(f"Đã tạo {len(cung)} ngày cúng và {len(hang_ngay)} ngày âm lịch "
          f"({a.tu} → {a.den}) trong thư mục '{a.thu_muc}/'.")
    for d, ten, mo_ta in cung[:12]:
        print(f"  {d:%d/%m/%Y}  {ten}  ({mo_ta})")
    if len(cung) > 12:
        print("  ...")


if __name__ == "__main__":
    main()
