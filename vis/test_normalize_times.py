import unittest

from vis.normalize_times import chinese_number, normalize_time


class NormalizeTimesTest(unittest.TestCase):
    def test_chinese_numbers(self):
        self.assertEqual(chinese_number("元"), 1)
        self.assertEqual(chinese_number("十"), 10)
        self.assertEqual(chinese_number("二十七"), 27)
        self.assertEqual(chinese_number("三十二"), 32)

    def test_exact_date(self):
        item = normalize_time("南宋绍兴二年四月二十七日")
        self.assertEqual((item.year_start, item.month, item.day), (1132, 4, 27))
        self.assertEqual(item.time_type, "exact")

    def test_leap_month(self):
        regular = normalize_time("南宋绍兴二年四月二十七日")
        leap = normalize_time("南宋绍兴二年闰四月")
        may = normalize_time("南宋绍兴二年五月")
        self.assertEqual((leap.month, leap.is_leap_month), (4, 1))
        self.assertLess(regular.sort_order, leap.sort_order)
        self.assertLess(leap.sort_order, may.sort_order)

    def test_unnumbered_leap_month_preserves_text(self):
        item = normalize_time("南宋绍兴五年闰月丁卯")
        self.assertEqual(item.year_start, 1135)
        self.assertEqual(item.month_text, "闰月")
        self.assertEqual(item.day_text, "丁卯")

    def test_same_era_range(self):
        item = normalize_time("北宋庆历三年五月至五年十月")
        self.assertEqual((item.year_start, item.year_end), (1043, 1045))
        self.assertEqual((item.month, item.end_month), (5, 10))
        self.assertEqual(item.time_type, "range")

    def test_cross_era_range(self):
        item = normalize_time("北宋乾兴元年至明道二年")
        self.assertEqual((item.year_start, item.year_end), (1022, 1033))
        self.assertEqual(item.time_type, "range")

    def test_undated_and_pre_song(self):
        self.assertEqual(normalize_time("宋代（未载具体年月）").time_type, "undated")
        self.assertEqual(normalize_time("魏文帝黄初三年").time_type, "pre_song")

    def test_known_invalid(self):
        self.assertEqual(normalize_time("南宋宣庆二年").time_type, "unresolved")


if __name__ == "__main__":
    unittest.main()
