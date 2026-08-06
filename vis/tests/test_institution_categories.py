import unittest

from vis.backend.institution_categories import (
    classify_central_group,
    classify_institution,
    classify_institution_group,
    resolve_source_catalogs,
)


class InstitutionCategoriesTest(unittest.TestCase):
    def test_dictionary_chapters_map_to_the_five_design_categories(self):
        cases = {
            "宋代官制辞典/第一编 皇帝制度类/九、宦官门": "内廷机构",
            "宋代官制辞典/第五编 元丰正名后中枢机构类之二/二、太常寺门": "中央机构",
            "宋代官制辞典/第八编 军事统率机构与地方治安机构类": "军队机构",
            "宋代官制辞典/第九编 地方官类之一——路官": "路级机构",
            "宋代官制辞典/第十编 地方官类之二——府州县官": "州县机构",
        }
        for catalog, expected in cases.items():
            with self.subTest(catalog=catalog):
                self.assertEqual(classify_institution([], [catalog])[0], expected)

    def test_chapter_seven_splits_military_and_inner_court_sections(self):
        root = "宋代官制辞典/第七编 皇宫京城禁卫侍奉机构类/"
        self.assertEqual(
            classify_institution([], [root + "一、禁军三衙门"])[0], "军队机构"
        )
        self.assertEqual(
            classify_institution([], [root + "二、皇城司与横行五司门"])[0], "内廷机构"
        )

    def test_specific_non_central_catalog_wins_over_central_catalog(self):
        catalogs = [
            "宋代官制辞典/第三编 北宋前期中枢机构类",
            "宋代官制辞典/第十编 地方官类之二——府州县官",
        ]
        category, basis = classify_institution([], catalogs)
        self.assertEqual(category, "州县机构")
        self.assertIn("非中央", basis)

    def test_explicit_attribute_disambiguates_cross_chapter_entity(self):
        catalogs = [
            "宋代官制辞典/第五编 元丰正名后中枢机构类之二",
            "宋代官制辞典/第七编 皇宫京城禁卫侍奉机构类/一、禁军三衙门",
        ]
        category, _ = classify_institution(["禁军番号统称"], catalogs)
        self.assertEqual(category, "军队机构")

    def test_missing_evidence_stays_unresolved(self):
        self.assertEqual(classify_institution(["官署名"], [])[0], None)

    def test_palace_and_temple_attributes_map_to_court_categories(self):
        self.assertEqual(classify_institution(["宫观"], [])[0], "中央机构")
        self.assertEqual(classify_institution(["宫殿"], [])[0], "内廷机构")

    def test_title_fallback_covers_generic_attributes(self):
        cases = (
            ("淮东宣抚使司", "军队机构"),
            ("真定府", "州县机构"),
            ("建康府", "州县机构"),
            ("八作司", "中央机构"),
            ("香药榷易院", "中央机构"),
        )
        for title, expected in cases:
            with self.subTest(title=title):
                category, basis = classify_institution(["官署名"], [], title)
                self.assertEqual(category, expected)
                self.assertIn("兜底", basis)

    def test_title_fallback_respects_palace_exclusions(self):
        self.assertEqual(classify_institution(["官署名"], [], "都督府")[0], None)
        self.assertEqual(classify_institution(["官署名"], [], "王府")[0], None)

    def test_road_in_a_common_noun_does_not_mean_circuit_level(self):
        category, _ = classify_institution(
            ["京师道路机构"],
            ["宋代官制辞典/第四编 元丰正名后中枢机构类之一"],
        )
        self.assertEqual(category, "中央机构")

    def test_precise_page_ignores_ambiguous_title_only_fallback(self):
        military = "宋代官制辞典/第八编 军事统率机构与地方治安机构类"
        circuit = "宋代官制辞典/第九编 地方官类之一——路官"
        catalogs = resolve_source_catalogs(
            "经制司（军事机构）",
            [("经制司", "510"), ("经制司", "")],
            {("经制司", "510"): {military}},
            {"510": {military}},
            {"经制司": {military, circuit}},
        )
        self.assertEqual(catalogs, {military})

    def test_formal_headword_beats_incidental_mentions(self):
        central = "宋代官制辞典/第三编 北宋前期中枢机构类"
        county = "宋代官制辞典/第十编 地方官类之二——府州县官"
        catalogs = resolve_source_catalogs(
            "粮料院",
            [("粮料院", "139"), ("监当官", "614")],
            {("粮料院", "139"): {central}, ("监当官", "614"): {county}},
            {"139": {central}, "614": {county}},
            {"粮料院": {central}, "监当官": {county}},
        )
        self.assertEqual(catalogs, {central})

    def test_central_groups_follow_dictionary_institutional_systems(self):
        cases = (
            (
                "中书门下",
                ["官署名"],
                ["宋代官制辞典/第三编 北宋前期中枢机构类/一、中书门下门"],
                "宰辅与决策中枢",
            ),
            (
                "尚书省",
                ["中央政务机构"],
                ["宋代官制辞典/第四编 元丰正名后中枢机构类之一/一、三省门"],
                "三省六部与馆阁",
            ),
            (
                "提举太医局所",
                ["中央医学教育机构"],
                ["宋代官制辞典/第五编 元丰正名后中枢机构类之二/二、太常寺门"],
                "礼仪宗室与宫廷事务",
            ),
            (
                "元丰库",
                ["中央封桩库"],
                ["宋代官制辞典/第五编 元丰正名后中枢机构类之二/九、太府寺门"],
                "财赋农政与马政",
            ),
            (
                "国子监",
                ["中央教育管理机构"],
                ["宋代官制辞典/第五编 元丰正名后中枢机构类之二/一、总九寺五监门"],
                "五监与工程教育",
            ),
            (
                "御史台",
                ["中央监察机构"],
                ["宋代官制辞典/第六编 司法、监察机构类/一、御史台门"],
                "司法监察",
            ),
        )
        for title, attrs, catalogs, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(classify_central_group(title, attrs, catalogs)[0], expected)

    def test_central_collective_stays_in_a_non_historical_summary_group(self):
        group, basis = classify_central_group(
            "九寺五监",
            ["机构统称"],
            ["宋代官制辞典/第五编 元丰正名后中枢机构类之二/一、总九寺五监门"],
        )
        self.assertEqual(group, "寺监制度统称")
        self.assertIn("统称", basis)

    def test_horse_service_bureau_is_not_absorbed_by_the_privy_council_catalog(self):
        catalog = "宋代官制辞典/第三编 北宋前期中枢机构类/三、枢密院门"
        for title in ("皮剥所", "行在皮剥所", "枢密院皮剥所", "剥马务"):
            with self.subTest(title=title):
                group, basis = classify_central_group(title, ["监当局"], [catalog])
                self.assertEqual(group, "财赋农政与马政")
                self.assertIn("马政", basis)

    def test_third_chapter_sections_do_not_all_fall_into_the_policy_group(self):
        cases = (
            ("三司", "四、三司门", "财赋农政与马政"),
            ("群牧司", "六、群牧司门", "财赋农政与马政"),
            ("宣徽院", "五、宣徽院门", "礼仪宗室与宫廷事务"),
            ("崇文院", "[附]殿阁学士与三馆秘阁门", "三省六部与馆阁"),
        )
        for title, section, expected in cases:
            with self.subTest(title=title):
                catalog = f"宋代官制辞典/第三编 北宋前期中枢机构类/{section}"
                self.assertEqual(classify_central_group(title, ["官署名"], [catalog])[0], expected)

    def test_all_five_categories_have_stable_visual_groups(self):
        cases = (
            ("内廷机构", "皇城司", [], ["第七编/二、皇城司与横行五司门"], "宦官内侍与皇城侍奉"),
            ("路级机构", "转运司", [], ["第九编/二、发运使、转运使门"], "转运发运"),
            ("州县机构", "州学", [], ["第十编/四、州府学与书院门"], "州学与书院"),
            ("军队机构", "御前诸军都统制司", [], ["第八编/五、御前诸军都统制司门"], "宣抚总领与御前诸军"),
        )
        for category, title, attrs, catalogs, expected in cases:
            with self.subTest(category=category, title=title):
                self.assertEqual(
                    classify_institution_group(category, title, attrs, catalogs)[0],
                    expected,
                )

    def test_group_classifier_does_not_invent_a_group_without_evidence(self):
        group, basis = classify_institution_group("路级机构", "未详机构", ["路级机构"], [])
        self.assertIsNone(group)
        self.assertIn("缺少", basis)

    def test_cross_chapter_entities_use_explicit_attributes_for_visual_grouping(self):
        cases = (
            ("内廷机构", "奉宸库", ["御前内庭宝库"], "御前供奉与宫廷库务"),
            ("路级机构", "提举秦凤等路买马监牧司", ["路级机构", "马政机构"], "买马监牧"),
            ("军队机构", "御营使司前军", ["军事编制机构"], "宣抚总领与御前诸军"),
            ("军队机构", "堡", ["地方/军事设施"], "城关堡寨与地方防务"),
        )
        for category, title, attrs, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(
                    classify_institution_group(category, title, attrs, ["其他编目录"])[0],
                    expected,
                )


if __name__ == "__main__":
    unittest.main()
