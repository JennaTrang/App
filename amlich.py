"""Chuyển đổi dương lịch <-> âm lịch Việt Nam.

Dựa trên thuật toán thiên văn của Hồ Ngọc Đức, tính theo múi giờ UTC+7
(giờ Việt Nam). Âm lịch Việt Nam đôi khi lệch một ngày so với âm lịch
Trung Quốc (UTC+8), nên không nên dùng lịch âm Trung Quốc có sẵn trên
điện thoại để xác định ngày cúng.

Chỉ dùng thư viện chuẩn của Python.
"""

import math
from datetime import date

TZ_VIETNAM = 7.0
_DR = math.pi / 180


def jd_from_date(dd, mm, yy):
    """Số ngày Julius của một ngày dương lịch."""
    a = (14 - mm) // 12
    y = yy + 4800 - a
    m = mm + 12 * a - 3
    jd = dd + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    if jd < 2299161:
        jd = dd + (153 * m + 2) // 5 + 365 * y + y // 4 - 32083
    return jd


def jd_to_date(jd):
    """Ngày dương lịch (ngày, tháng, năm) từ số ngày Julius."""
    if jd > 2299160:
        a = jd + 32044
        b = (4 * a + 3) // 146097
        c = a - (b * 146097) // 4
    else:
        b = 0
        c = jd + 32082
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = b * 100 + d - 4800 + m // 10
    return day, month, year


def _new_moon(k):
    """Thời điểm sóc (trăng mới) thứ k tính từ 1/1/1900, theo ngày Julius."""
    T = k / 1236.85
    T2 = T * T
    T3 = T2 * T
    jd1 = 2415020.75933 + 29.53058868 * k + 0.0001178 * T2 - 0.000000155 * T3
    jd1 += 0.00033 * math.sin((166.56 + 132.87 * T - 0.009173 * T2) * _DR)
    M = 359.2242 + 29.10535608 * k - 0.0000333 * T2 - 0.00000347 * T3
    Mpr = 306.0253 + 385.81691806 * k + 0.0107306 * T2 + 0.00001236 * T3
    F = 21.2964 + 390.67050646 * k - 0.0016528 * T2 - 0.00000239 * T3
    c1 = (0.1734 - 0.000393 * T) * math.sin(M * _DR) + 0.0021 * math.sin(2 * _DR * M)
    c1 -= 0.4068 * math.sin(Mpr * _DR) - 0.0161 * math.sin(_DR * 2 * Mpr)
    c1 -= 0.0004 * math.sin(_DR * 3 * Mpr)
    c1 += 0.0104 * math.sin(_DR * 2 * F) - 0.0051 * math.sin(_DR * (M + Mpr))
    c1 -= 0.0074 * math.sin(_DR * (M - Mpr)) - 0.0004 * math.sin(_DR * (2 * F + M))
    c1 -= 0.0004 * math.sin(_DR * (2 * F - M)) + 0.0006 * math.sin(_DR * (2 * F + Mpr))
    c1 += 0.0010 * math.sin(_DR * (2 * F - Mpr)) + 0.0005 * math.sin(_DR * (2 * Mpr + M))
    if T < -11:
        deltat = 0.001 + 0.000839 * T + 0.0002261 * T2 - 0.00000845 * T3 - 0.000000081 * T * T3
    else:
        deltat = -0.000278 + 0.000265 * T + 0.000262 * T2
    return jd1 + c1 - deltat


def _new_moon_day(k, tz):
    return int(math.floor(_new_moon(k) + 0.5 + tz / 24))


def _sun_longitude(jdn):
    T = (jdn - 2451545.0) / 36525
    T2 = T * T
    M = 357.52910 + 35999.05030 * T - 0.0001559 * T2 - 0.00000048 * T * T2
    L0 = 280.46645 + 36000.76983 * T + 0.0003032 * T2
    DL = (1.914600 - 0.004817 * T - 0.000014 * T2) * math.sin(_DR * M)
    DL += (0.019993 - 0.000101 * T) * math.sin(_DR * 2 * M) + 0.000290 * math.sin(_DR * 3 * M)
    L = (L0 + DL) * _DR
    return L - math.pi * 2 * math.floor(L / (math.pi * 2))


def _sun_longitude_sector(day_number, tz):
    """Cung hoàng đạo (0..11) của mặt trời vào đầu ngày day_number."""
    return int(math.floor(_sun_longitude(day_number - 0.5 - tz / 24) / math.pi * 6))


def _lunar_month11(yy, tz):
    """Ngày bắt đầu tháng 11 âm lịch (tháng chứa Đông chí) của năm yy."""
    off = jd_from_date(31, 12, yy) - 2415021
    k = int(math.floor(off / 29.530588853))
    nm = _new_moon_day(k, tz)
    if _sun_longitude_sector(nm, tz) >= 9:
        nm = _new_moon_day(k - 1, tz)
    return nm


def _leap_month_offset(a11, tz):
    k = int(math.floor((a11 - 2415021.076998695) / 29.530588853 + 0.5))
    i = 1
    arc = _sun_longitude_sector(_new_moon_day(k + i, tz), tz)
    while True:
        last = arc
        i += 1
        arc = _sun_longitude_sector(_new_moon_day(k + i, tz), tz)
        if arc == last or i >= 14:
            break
    return i - 1


def solar_to_lunar(d, tz=TZ_VIETNAM):
    """Đổi ngày dương lịch (datetime.date) sang âm lịch.

    Trả về (ngày, tháng, năm, nhuận) với nhuận là True nếu là tháng nhuận.
    """
    day_number = jd_from_date(d.day, d.month, d.year)
    k = int(math.floor((day_number - 2415021.076998695) / 29.530588853))
    month_start = _new_moon_day(k + 1, tz)
    if month_start > day_number:
        month_start = _new_moon_day(k, tz)
    a11 = _lunar_month11(d.year, tz)
    b11 = a11
    if a11 >= month_start:
        lunar_year = d.year
        a11 = _lunar_month11(d.year - 1, tz)
    else:
        lunar_year = d.year + 1
        b11 = _lunar_month11(d.year + 1, tz)
    lunar_day = day_number - month_start + 1
    diff = int(math.floor((month_start - a11) / 29))
    leap = False
    lunar_month = diff + 11
    if b11 - a11 > 365:
        leap_diff = _leap_month_offset(a11, tz)
        if diff >= leap_diff:
            lunar_month = diff + 10
            if diff == leap_diff:
                leap = True
    if lunar_month > 12:
        lunar_month -= 12
    if lunar_month >= 11 and diff < 4:
        lunar_year -= 1
    return lunar_day, lunar_month, lunar_year, leap


CAN = ["Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý"]
CHI = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]


def ten_nam(lunar_year):
    """Tên can chi của năm âm lịch, ví dụ 2026 -> 'Bính Ngọ'."""
    return f"{CAN[(lunar_year + 6) % 10]} {CHI[(lunar_year + 8) % 12]}"


def date_from_jd(jd):
    d, m, y = jd_to_date(jd)
    return date(y, m, d)
