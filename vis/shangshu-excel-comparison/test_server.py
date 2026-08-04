import unittest

import server


class ExcelPayloadTest(unittest.TestCase):
    def test_chinese_number_and_composition_parser(self):
        self.assertEqual(server.chinese_number("一百五十"), 150)
        self.assertEqual(server.quota_from_text("元丰新制定为一人"), 1)
        text = "宋前期，判尚书都省事一人，吏额七人：令史三人，驱使官三人，散官一人。"
        self.assertEqual(
            server.composition_items(text),
            [
                ("判尚书都省事", 1, "官"),
                ("令史", 3, "吏"),
                ("驱使官", 3, "吏"),
                ("散官", 1, "吏"),
            ],
        )

    def test_1080_shangshu_staff_comes_from_excel_composition(self):
        payload = server.build_payload()
        entities = {entity["id"]: entity for entity in payload["entities"]}
        shangshu_id = next(
            entity_id for entity_id, entity in entities.items()
            if entity["title"] == "尚书省"
        )
        staff = {
            entities[edge["official"]]["title"]: edge["staff_quota"]
            for edge in payload["staffEdges"]
            if edge["org"] == shangshu_id
            and edge["periods"][0]["start"] <= 1080
        }
        self.assertEqual(
            set(staff),
            {"权判尚书都省事", "令史", "驱使官", "散官"},
        )
        self.assertEqual(staff["权判尚书都省事"], 1)
        self.assertEqual(staff["令史"], 3)
        self.assertEqual(staff["驱使官"], 3)
        self.assertEqual(staff["散官"], 1)


if __name__ == "__main__":
    unittest.main()
