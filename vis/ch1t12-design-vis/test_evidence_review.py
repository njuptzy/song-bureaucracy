import tempfile
import unittest
from pathlib import Path
import sqlite3

from evidence_review import EvidenceReviewError, load_evidence, validate_model_result


class EvidenceReviewTest(unittest.TestCase):
    def setUp(self):
        handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        handle.close()
        self.path = Path(handle.name)
        conn = sqlite3.connect(self.path)
        conn.executescript("""
        CREATE TABLE Entities(id INTEGER PRIMARY KEY, title TEXT);
        CREATE TABLE Timepoints(id INTEGER PRIMARY KEY, entity_id INTEGER, time TEXT, event TEXT);
        CREATE TABLE Citations(id INTEGER PRIMARY KEY, target_table TEXT, target_id INTEGER, citation TEXT, quotation TEXT);
        INSERT INTO Entities VALUES(1, '秘书省');
        INSERT INTO Timepoints VALUES(2, 1, '南宋建炎元年五月', '于省内复建史馆');
        INSERT INTO Citations VALUES(3, 'Timepoints', 2, '第161页史馆条', '至南宋建炎元年五月，于秘书省复建史馆。');
        INSERT INTO Citations VALUES(4, 'Timepoints', 99, '错误归属', '无关文字');
        """)
        conn.commit()
        conn.close()

    def tearDown(self):
        self.path.unlink(missing_ok=True)

    def test_loads_only_citation_owned_by_timepoint(self):
        evidence = load_evidence(self.path, 2, 3)
        self.assertEqual(evidence.entity, "秘书省")
        with self.assertRaises(EvidenceReviewError):
            load_evidence(self.path, 2, 4)

    def test_accepts_exact_supported_span(self):
        result = validate_model_result({
            "verdict": "supported",
            "concise_quotations": ["南宋建炎元年五月，于秘书省复建史馆"],
            "reason": "时间、地点和行为相符。",
        }, "至南宋建炎元年五月，于秘书省复建史馆。")
        self.assertEqual(result["verdict"], "supported")

    def test_rejects_paraphrase_and_extra_fields(self):
        for value in ({
            "verdict": "supported", "concise_quotations": ["建炎元年在秘书省重建史馆"],
            "reason": "支持。",
        }, {
            "verdict": "not_supported", "concise_quotations": [], "reason": "不支持。", "marker": "red",
        }):
            with self.assertRaises(EvidenceReviewError):
                validate_model_result(value, "至南宋建炎元年五月，于秘书省复建史馆。")

    def test_non_supported_has_no_excerpt(self):
        with self.assertRaises(EvidenceReviewError):
            validate_model_result({
                "verdict": "not_supported", "concise_quotations": ["无关"], "reason": "未记目标事件。",
            }, "无关文字")


if __name__ == "__main__":
    unittest.main()
