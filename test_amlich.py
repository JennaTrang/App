import unittest
from datetime import date

from amlich import solar_to_lunar, ten_nam
from tao_lich import ngay_cung, tao_ics


class TestAmLich(unittest.TestCase):
    def test_tet_nguyen_dan(self):
        # Mùng 1 Tết các năm đã biết (theo lịch Việt Nam).
        for d in [date(2024, 2, 10), date(2025, 1, 29), date(2026, 2, 17),
                  date(2027, 2, 6), date(2028, 1, 26)]:
            self.assertEqual(solar_to_lunar(d)[:2], (1, 1), d)

    def test_khac_lich_trung_quoc(self):
        # Tết 1985 ở Việt Nam là 21/1, ở Trung Quốc là 20/2 (do múi giờ).
        self.assertEqual(solar_to_lunar(date(1985, 1, 21))[:2], (1, 1))

    def test_thang_nhuan(self):
        # Năm 2025 có tháng 6 nhuận, bắt đầu 25/7/2025.
        self.assertEqual(solar_to_lunar(date(2025, 7, 25)), (1, 6, 2025, True))

    def test_can_chi(self):
        self.assertEqual(ten_nam(2026), "Bính Ngọ")
        self.assertEqual(ten_nam(2027), "Đinh Mùi")

    def test_ngay_cung_tet_2027(self):
        ds = {d: ten for d, ten, _ in ngay_cung(date(2027, 1, 1), date(2027, 3, 1))}
        self.assertIn("Giao thừa", ds[date(2027, 2, 5)])
        self.assertIn("Tết Nguyên Đán", ds[date(2027, 2, 6)])
        self.assertIn("Rằm tháng Giêng", ds[date(2027, 2, 20)])

    def test_ics_co_nhac(self):
        ics = tao_ics("x", [(date(2027, 2, 6), "Tết", "a,b")], gio_nhac=9)
        self.assertIn("TRIGGER:-PT15H", ics)
        self.assertIn("DTSTART;VALUE=DATE:20270206", ics)
        ics2 = tao_ics("x", [(date(2027, 2, 6), "Tết", "")], gio_nhac=9, ngay_truoc=2)
        self.assertIn("TRIGGER:-PT39H", ics2)  # 9:00 ngày 4/2/2027
        for line in ics.split("\r\n"):
            self.assertLessEqual(len(line.encode()), 75)


if __name__ == "__main__":
    unittest.main()
