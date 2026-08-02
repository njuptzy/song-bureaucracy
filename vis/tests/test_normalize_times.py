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
        self.assertEqual((song.year_start, song.year_end), (None, None))
        self.assertEqual(song.time_type, "undated")
        self.assertEqual(normalize_time("魏文帝黄初三年").time_type, "pre_song")

    def test_generic_song_period_does_not_anchor_to_960(self):
        for raw in (
            "宋代",
            "两宋",
            "宋代（未载具体年月）",
            "宋代（左右厢店宅务）",
            "宋代千户以上县",
        ):
            with self.subTest(raw=raw):
                item = normalize_time(raw)
                self.assertEqual((item.year_start, item.year_end), (None, None))
                self.assertEqual(item.time_type, "undated")

    def test_known_invalid(self):
        self.assertEqual(normalize_time("南宋宣庆二年").time_type, "unresolved")

    def test_dynasty_periods_anchor_to_start_year(self):
        expected = {
            "北宋": 960,
            "北宋（未载具体年月）": 960,
            "南宋时期": 1127,
        }
        for raw, year in expected.items():
            with self.subTest(raw=raw):
                item = normalize_time(raw)
                self.assertEqual((item.year_start, item.year_end), (year, year))
                self.assertEqual(item.time_type, "bounded")

    def test_reign_and_composite_periods_anchor_to_start_year(self):
        expected = {
            "北宋仁宗朝": 1022,
            "北宋太祖、太宗朝": 960,
            "北宋神宗朝": 1067,
            "北宋徽宗朝": 1100,
            "北宋熙丰间": 1068,
        }
        for raw, year in expected.items():
            with self.subTest(raw=raw):
                item = normalize_time(raw)
                self.assertEqual((item.year_start, item.year_end), (year, year))
                self.assertEqual(item.time_type, "bounded")

    def test_relative_periods_anchor_to_boundary_year(self):
        expected = {
            "北宋景德后": 1007,
            "北宋英宗即位前": 960,
            "北宋英宗即位后": 1063,
            "北宋神宗朝起": 1067,
            "南宋隆兴后": 1164,
        }
        for raw, year in expected.items():
            with self.subTest(raw=raw):
                item = normalize_time(raw)
                self.assertEqual((item.year_start, item.year_end), (year, year))
                self.assertEqual(item.time_type, "bounded")

    def test_invalid_era_year_does_not_fall_back_to_era_range(self):
        item = normalize_time("北宋淳化九年")
        self.assertEqual((item.year_start, item.year_end), (None, None))
        self.assertEqual(item.time_type, "unresolved")
        self.assertIn("年号年次超出有效范围", item.parse_note)

    def test_era_period_is_bounded_not_continuous_range(self):
        item = normalize_time("南宋绍兴年间")
        self.assertEqual((item.year_start, item.year_end), (1131, 1131))
        self.assertEqual(item.time_type, "bounded")

    def test_accession_year_is_exact(self):
        item = normalize_time("北宋英宗即位")
        self.assertEqual((item.year_start, item.year_end), (1063, 1063))
        self.assertEqual(item.time_type, "exact")

    def test_fuzzy_song_periods_receive_numeric_anchors(self):
        expected = {
            "北宋初": 960,
            "北宋前期": 960,
            "北宋英宗即位之初": 1063,
            "北宋元丰改制后": 1082,
            "南宋初": 1127,
        }
        for raw, year in expected.items():
            with self.subTest(raw=raw):
                item = normalize_time(raw)
                self.assertEqual((item.year_start, item.year_end), (year, year))
                self.assertEqual(item.time_type, "bounded")

    def test_parseable_pre_song_dates_keep_numeric_years(self):
        expected = {
            "东汉建武二十七年": 51,
            "南朝梁天监七年": 508,
            "后梁开平元年五月": 907,
            "后周显德初": 954,
            "西周（前593）": -593,
            "唐天宝七载": 748,
            "唐末": 875,
        }
        for raw, year in expected.items():
            with self.subTest(raw=raw):
                item = normalize_time(raw)
                self.assertEqual(item.year_start, year)
                self.assertEqual(item.time_type, "pre_song")

    def test_ambiguous_pre_song_era_uses_dynasty_context(self):
        self.assertEqual(normalize_time("北魏太和十五年").year_start, 491)
        self.assertEqual(normalize_time("唐太和九年").year_start, 835)

    def test_institution_name_does_not_collide_with_pre_song_era(self):
        item = normalize_time("北宋（司天监时期）")
        self.assertEqual((item.year_start, item.time_type), (960, "bounded"))
        self.assertEqual(normalize_time("南朝梁天监七年").year_start, 508)

    def test_only_genuinely_unparseable_values_lack_year(self):
        for raw in ("未知", "修理工程完毕", "北宋淳化九年", "北宋景德五年"):
            with self.subTest(raw=raw):
                item = normalize_time(raw)
                self.assertIsNone(item.year_start)
                self.assertEqual(item.time_type, "unresolved")


if __name__ == "__main__":
    unittest.main()
