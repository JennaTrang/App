#!/usr/bin/env python3
"""Chỉ đường Google Maps, ưu tiên đường KHÔNG kẹt xe hoặc ít kẹt xe.

Google Maps tô đường kẹt xe màu đỏ (TRAFFIC_JAM), đường đông màu cam (SLOW),
đường thông thoáng màu xanh (NORMAL). Công cụ này:

  1. Hỏi Google Routes API các tuyến đường có thể đi (kèm tình trạng giao thông
     trên từng đoạn).
  2. Tính số km bị tô đỏ / cam trên mỗi tuyến.
  3. Chọn tuyến ít đoạn đỏ nhất (rồi tới ít đoạn cam nhất, rồi nhanh nhất),
     miễn là không chậm hơn tuyến nhanh nhất quá --cham-toi-da phút.
  4. In ra một đường link Google Maps có điểm đi qua nằm trên tuyến đã chọn,
     để mở trên điện thoại là Google Maps đi đúng đường ít kẹt xe đó.

Cần khoá API Google Maps (bật "Routes API"), đặt trong biến môi trường
GOOGLE_MAPS_API_KEY hoặc truyền bằng --api-key.

Cách dùng:
  python3 chi_duong.py "Chợ Bến Thành" "Sân bay Tân Sơn Nhất"
  python3 chi_duong.py "Nhà thờ Đức Bà" "Landmark 81" --xe-may --mo
  python3 chi_duong.py "A" "B" --cham-toi-da 20 --diem-qua 3
"""

import argparse
import json
import math
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
FIELD_MASK = ",".join([
    "routes.duration",
    "routes.staticDuration",
    "routes.distanceMeters",
    "routes.description",
    "routes.polyline.encodedPolyline",
    "routes.travelAdvisory.speedReadingIntervals",
])

DO = "TRAFFIC_JAM"   # màu đỏ trên bản đồ
CAM = "SLOW"         # màu cam


def giai_ma_polyline(chuoi):
    """Giải mã encoded polyline của Google thành danh sách (vĩ độ, kinh độ)."""
    diem, i, lat, lng = [], 0, 0, 0
    while i < len(chuoi):
        gia_tri = []
        for _ in range(2):
            ket_qua, dich = 0, 0
            while True:
                b = ord(chuoi[i]) - 63
                i += 1
                ket_qua |= (b & 0x1F) << dich
                dich += 5
                if b < 0x20:
                    break
            gia_tri.append(~(ket_qua >> 1) if ket_qua & 1 else ket_qua >> 1)
        lat += gia_tri[0]
        lng += gia_tri[1]
        diem.append((lat / 1e5, lng / 1e5))
    return diem


def khoang_cach_m(a, b):
    """Khoảng cách (mét) giữa hai điểm (vĩ độ, kinh độ)."""
    r = 6371000
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def giay(chuoi):
    """'1234s' -> 1234."""
    return int(float(str(chuoi or "0s").rstrip("s")))


def phan_tich_tuyen(route):
    """Tóm tắt một tuyến: thời gian, quãng đường, số mét đỏ/cam, các điểm."""
    diem = giai_ma_polyline(route.get("polyline", {}).get("encodedPolyline", ""))
    doan = [khoang_cach_m(diem[i], diem[i + 1]) for i in range(len(diem) - 1)]
    met = {DO: 0.0, CAM: 0.0}
    for kq in route.get("travelAdvisory", {}).get("speedReadingIntervals", []):
        toc_do = kq.get("speed")
        if toc_do in met:
            # Trường bằng 0 có thể bị API lược bỏ.
            dau = kq.get("startPolylinePointIndex", 0)
            cuoi = kq.get("endPolylinePointIndex", 0)
            met[toc_do] += sum(doan[dau:cuoi])
    return {
        "mo_ta": route.get("description", ""),
        "thoi_gian": giay(route.get("duration")),
        "thoi_gian_khong_ket": giay(route.get("staticDuration")),
        "quang_duong": route.get("distanceMeters", sum(doan)),
        "met_do": met[DO],
        "met_cam": met[CAM],
        "diem": diem,
        "doan": doan,
    }


def chon_tuyen(cac_tuyen, cham_toi_da_phut):
    """Chọn tuyến ít kẹt xe nhất trong số tuyến không chậm hơn tuyến nhanh
    nhất quá `cham_toi_da_phut` phút. Trả về chỉ số tuyến được chọn."""
    nhanh_nhat = min(t["thoi_gian"] for t in cac_tuyen)
    hop_le = [i for i, t in enumerate(cac_tuyen)
              if t["thoi_gian"] <= nhanh_nhat + cham_toi_da_phut * 60]
    return min(hop_le, key=lambda i: (round(cac_tuyen[i]["met_do"] / 50),
                                      round(cac_tuyen[i]["met_cam"] / 50),
                                      cac_tuyen[i]["thoi_gian"]))


def diem_tren_tuyen(tuyen, so_diem):
    """Lấy `so_diem` điểm cách đều nhau dọc theo tuyến (không tính đầu, cuối)."""
    tong = sum(tuyen["doan"])
    if so_diem <= 0 or tong == 0:
        return []
    moc = [tong * (k + 1) / (so_diem + 1) for k in range(so_diem)]
    ket_qua, da_di, j = [], 0.0, 0
    for i, d in enumerate(tuyen["doan"]):
        da_di += d
        while j < len(moc) and da_di >= moc[j]:
            ket_qua.append(tuyen["diem"][i + 1])
            j += 1
    return ket_qua


def link_google_maps(diem_di, diem_den, diem_qua):
    tham_so = {
        "api": "1",
        "origin": diem_di,
        "destination": diem_den,
        "travelmode": "driving",
    }
    if diem_qua:
        tham_so["waypoints"] = "|".join(f"{a:.5f},{b:.5f}" for a, b in diem_qua)
    return "https://www.google.com/maps/dir/?" + urllib.parse.urlencode(tham_so)


def goi_routes_api(diem_di, diem_den, api_key, xe_may):
    than = {
        "origin": {"address": diem_di},
        "destination": {"address": diem_den},
        "travelMode": "TWO_WHEELER" if xe_may else "DRIVE",
        "routingPreference": "TRAFFIC_AWARE",
        "computeAlternativeRoutes": True,
        "extraComputations": ["TRAFFIC_ON_POLYLINE"],
        "languageCode": "vi",
        "regionCode": "VN",
    }
    yeu_cau = urllib.request.Request(
        ROUTES_URL,
        data=json.dumps(than).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": FIELD_MASK,
        },
    )
    try:
        with urllib.request.urlopen(yeu_cau, timeout=30) as phan_hoi:
            return json.load(phan_hoi).get("routes", [])
    except urllib.error.HTTPError as e:
        sys.exit(f"Google trả lỗi {e.code}: {e.read().decode(errors='replace')}")


def phut(s):
    return f"{round(s / 60)} phút"


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Chỉ đường Google Maps, ưu tiên đường không/ít kẹt xe (ít đoạn đỏ).")
    p.add_argument("diem_di", help="nơi xuất phát (địa chỉ hoặc 'vĩ độ,kinh độ')")
    p.add_argument("diem_den", help="nơi đến")
    p.add_argument("--xe-may", action="store_true", help="tính đường cho xe máy")
    p.add_argument("--cham-toi-da", type=int, default=15, metavar="PHÚT",
                   help="chấp nhận chậm hơn tuyến nhanh nhất tối đa bao nhiêu phút "
                        "để né kẹt xe (mặc định 15)")
    p.add_argument("--diem-qua", type=int, default=3, metavar="SỐ",
                   help="số điểm đi qua gắn vào link để giữ đúng tuyến (mặc định 3; "
                        "Google Maps trên điện thoại nhận tối đa 3)")
    p.add_argument("--api-key", default=os.environ.get("GOOGLE_MAPS_API_KEY"),
                   help="khoá API (mặc định lấy từ biến GOOGLE_MAPS_API_KEY)")
    p.add_argument("--mo", action="store_true", help="mở link bằng trình duyệt")
    a = p.parse_args(argv)

    if not a.api_key:
        p.error("thiếu khoá API: đặt GOOGLE_MAPS_API_KEY hoặc dùng --api-key")

    routes = goi_routes_api(a.diem_di, a.diem_den, a.api_key, a.xe_may)
    if not routes:
        sys.exit("Google không tìm được đường đi giữa hai điểm này.")
    cac_tuyen = [phan_tich_tuyen(r) for r in routes]
    chon = chon_tuyen(cac_tuyen, a.cham_toi_da)

    print(f"Tìm được {len(cac_tuyen)} tuyến:")
    for i, t in enumerate(cac_tuyen):
        dau = "→" if i == chon else " "
        ket_them = max(0, t["thoi_gian"] - t["thoi_gian_khong_ket"])
        print(f" {dau} {i + 1}. {t['mo_ta'] or 'Tuyến ' + str(i + 1)}: "
              f"{t['quang_duong'] / 1000:.1f} km, {phut(t['thoi_gian'])} "
              f"(kẹt thêm {phut(ket_them)}) | "
              f"đỏ {t['met_do'] / 1000:.1f} km, cam {t['met_cam'] / 1000:.1f} km")

    t = cac_tuyen[chon]
    if t["met_do"] == 0 and t["met_cam"] == 0:
        print("\nĐã chọn tuyến không kẹt xe.")
    elif chon == 0:
        print("\nKhông có tuyến nào ít kẹt hơn tuyến Google đề xuất; giữ tuyến này.")
    else:
        print(f"\nĐã chọn tuyến {chon + 1}: ít kẹt xe nhất.")

    link = link_google_maps(a.diem_di, a.diem_den, diem_tren_tuyen(t, a.diem_qua))
    print("\nMở link này trên điện thoại để Google Maps đi đúng tuyến:\n" + link)
    if a.mo:
        webbrowser.open(link)


if __name__ == "__main__":
    main()
