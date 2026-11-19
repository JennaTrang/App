import unittest
from unittest import mock

import chi_duong
from chi_duong import (chon_tuyen, diem_tren_tuyen, giai_ma_polyline,
                       link_google_maps, phan_tich_tuyen)


def ma_hoa(diem):
    """Mã hoá polyline (để tạo dữ liệu thử)."""
    ra, truoc = [], (0, 0)
    for lat, lng in diem:
        cur = (round(lat * 1e5), round(lng * 1e5))
        for v in (cur[0] - truoc[0], cur[1] - truoc[1]):
            v = ~(v << 1) if v < 0 else v << 1
            while v >= 0x20:
                ra.append(chr((0x20 | (v & 0x1F)) + 63))
                v >>= 5
            ra.append(chr(v + 63))
        truoc = cur
    return "".join(ra)


# 5 điểm thẳng hàng, mỗi đoạn ~1.1 km.
DIEM = [(10.70 + 0.01 * i, 106.70) for i in range(5)]


def tuyen(giay, khoang_toc_do):
    return {
        "duration": f"{giay}s",
        "staticDuration": "600s",
        "distanceMeters": 4400,
        "polyline": {"encodedPolyline": ma_hoa(DIEM)},
        "travelAdvisory": {"speedReadingIntervals": [
            # Trường startPolylinePointIndex = 0 bị lược bỏ như API thật.
            {k: v for k, v in (("startPolylinePointIndex", a),
                               ("endPolylinePointIndex", b), ("speed", s)) if v}
            for a, b, s in khoang_toc_do
        ]},
    }


class TestChiDuong(unittest.TestCase):
    def test_giai_ma_polyline_mau_google(self):
        # Ví dụ trong tài liệu của Google.
        self.assertEqual(giai_ma_polyline("_p~iF~ps|U_ulLnnqC_mqNvxq`@"),
                         [(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)])

    def test_dem_met_do_cam(self):
        t = phan_tich_tuyen(tuyen(900, [(0, 2, "TRAFFIC_JAM"), (2, 3, "SLOW"),
                                        (3, 4, "NORMAL")]))
        self.assertAlmostEqual(t["met_do"], 2224, delta=10)
        self.assertAlmostEqual(t["met_cam"], 1112, delta=10)

    def test_chon_tuyen_it_do_nhat(self):
        cac = [phan_tich_tuyen(tuyen(900, [(0, 4, "TRAFFIC_JAM")])),
               phan_tich_tuyen(tuyen(1200, [(0, 4, "SLOW")])),
               phan_tich_tuyen(tuyen(1300, [(0, 4, "NORMAL")]))]
        self.assertEqual(chon_tuyen(cac, 15), 2)   # chậm hơn 6–7 phút, không đỏ
        self.assertEqual(chon_tuyen(cac, 5), 1)    # tuyến 3 vượt giới hạn
        self.assertEqual(chon_tuyen(cac, 0), 0)    # chỉ còn tuyến nhanh nhất

    def test_diem_qua_nam_tren_tuyen(self):
        t = phan_tich_tuyen(tuyen(900, []))
        qua = diem_tren_tuyen(t, 3)
        self.assertEqual(len(qua), 3)
        for d in qua:
            self.assertIn(d, t["diem"])

    def test_link(self):
        link = link_google_maps("A", "B", [(10.7, 106.7)])
        self.assertIn("api=1", link)
        self.assertIn("waypoints=10.70000%2C106.70000", link)

    def test_main(self):
        routes = [tuyen(900, [(0, 4, "TRAFFIC_JAM")]), tuyen(1000, [])]
        with mock.patch.object(chi_duong, "goi_routes_api", return_value=routes), \
                mock.patch("builtins.print") as in_ra:
            chi_duong.main(["A", "B", "--api-key", "x"])
        ra = "\n".join(str(c.args[0]) for c in in_ra.call_args_list)
        self.assertIn("→ 2.", ra)
        self.assertIn("google.com/maps/dir", ra)


if __name__ == "__main__":
    unittest.main()
