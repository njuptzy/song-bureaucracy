import unittest

from vis.backend.normalize_times import chinese_number, normalize_time


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
        song = normalize_time("宋代（未载具体年月）")
        self.assertEqual((song.year_start, song.year_end), (960, 1279))
        self.assertEqual(song.time_type, "bounded")
        self.assertEqual(normalize_time("魏文帝黄初三年").time_type, "pre_song")

    def test_known_invalid(self):
        self.assertEqual(normalize_time("南宋宣庆二年").time_type, "unresolved")

    def test_dynasty_ranges(self):
        expected = {
            "北宋": (960, 1127),
            "北宋（未载具体年月）": (960, 1127),
            "南宋时期": (1127, 1279),
            "宋代（未载具体年月）": (960, 1279),
            "两宋": (960, 1279),
        }
        for raw, years in expected.items():
            with self.subTest(raw=raw):
                item = normalize_time(raw)
                self.assertEqual((item.year_start, item.year_end), years)
                self.assertEqual(item.time_type, "bounded")

    def test_reign_and_composite_ranges(self):
        expected = {
            "北宋仁宗朝": (1022, 1063),
            "北宋太祖、太宗朝": (960, 997),
            "北宋神宗朝": (1067, 1085),
            "北宋徽宗朝": (1100, 1125),
            "北宋熙丰间": (1068, 1085),
        }
        for raw, years in expected.items():
            with self.subTest(raw=raw):
                item = normalize_time(raw)
                self.assertEqual((item.year_start, item.year_end), years)
                self.assertEqual(item.time_type, "bounded")

    def test_relative_ranges_keep_boundary_year(self):
        expected = {
            "北宋景德后": (1007, 1127),
            "北宋英宗即位前": (960, 1063),
            "北宋英宗即位后": (1063, 1127),
            "北宋神宗朝起": (1067, 1127),
            "南宋隆兴后": (1164, 1279),
        }
        for raw, years in expected.items():
            with self.subTest(raw=raw):
                item = normalize_time(raw)
                self.assertEqual((item.year_start, item.year_end), years)
                self.assertEqual(item.time_type, "bounded")

    def test_invalid_era_year_does_not_fall_back_to_era_range(self):
        item = normalize_time("北宋淳化九年")
        self.assertEqual((item.year_start, item.year_end), (None, None))
        self.assertEqual(item.time_type, "unresolved")
        self.assertIn("年号年次超出有效范围", item.parse_note)

    def test_era_period_is_bounded_not_continuous_range(self):
        item = normalize_time("南宋绍兴年间")
        self.assertEqual((item.year_start, item.year_end), (1131, 1162))
        self.assertEqual(item.time_type, "bounded")

    def test_accession_year_is_exact(self):
        item = normalize_time("北宋英宗即位")
        self.assertEqual((item.year_start, item.year_end), (1063, 1063))
        self.assertEqual(item.time_type, "exact")

    def test_fuzzy_periods_remain_undated(self):
        for raw in ("北宋初", "北宋前期", "北宋英宗即位之初", "北宋元丰改制后"):
            with self.subTest(raw=raw):
                self.assertEqual(normalize_time(raw).time_type, "undated")


if __name__ == "__main__":
    unittest.main()
