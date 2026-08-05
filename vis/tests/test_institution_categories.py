import unittest

from vis.backend.institution_categories import classify_institution


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


if __name__ == "__main__":
    unittest.main()
