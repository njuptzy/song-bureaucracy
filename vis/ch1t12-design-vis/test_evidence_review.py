import tempfile
import unittest
from pathlib import Path
import sqlite3
from unittest.mock import patch

from evidence_review import (
    DEEPSEEK_DEFAULT_MODEL,
    DEEPSEEK_OFFICIAL_URL,
    EvidenceReviewError,
    EvidenceReviewService,
    load_evidence,
    validate_model_result,
)


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

    def test_deepseek_official_defaults_and_key_file(self):
        env_file = self.path.with_suffix(".env")
        env_file.write_text("OTHER_SECRET=ignored\nDEEPSEEK_API_KEY='test-key'\n", encoding="utf-8")
        service = EvidenceReviewService(self.path)
        with patch.dict("os.environ", {"SONG_EVIDENCE_LLM_ENV_FILE": str(env_file)}, clear=True):
            self.assertEqual(service._config(), (
                "test-key", DEEPSEEK_OFFICIAL_URL, DEEPSEEK_DEFAULT_MODEL,
            ))
        env_file.unlink()

    def test_valid_result_is_reused_from_memory_cache(self):
        service = EvidenceReviewService(self.path)
        model_result = {
            "verdict": "supported",
            "concise_quotations": ["南宋建炎元年五月，于秘书省复建史馆"],
            "reason": "引文明示目标事件。",
        }
        with (
            patch.dict("os.environ", {"DEEPSEEK_API_KEY": "test-key"}, clear=True),
            patch.object(service, "_call_model", return_value=model_result) as call_model,
        ):
            first = service.review(2, 3)
            second = service.review(2, 3)
        self.assertFalse(first["cached"])
        self.assertTrue(second["cached"])
        call_model.assert_called_once()


if __name__ == "__main__":
    unittest.main()
