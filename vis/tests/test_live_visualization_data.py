import shutil
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from vis.backend.export_visualization_data import build_payload
from vis.backend.serve_visualization_v2 import LivePayloadCache


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DB = ROOT / "vis/data/song_bureaucracy_visualization.db"


class LiveVisualizationDataTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "live.db"
        shutil.copy2(SOURCE_DB, self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _table_counts(self) -> dict[str, int]:
        conn = sqlite3.connect(self.db_path)
        try:
            return {
                table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("Entities", "Timepoints", "Relationships")
            }
        finally:
            conn.close()

    def test_current_database_builds_complete_payload(self):
        counts = self._table_counts()
        payload = build_payload(self.db_path)
        self.assertEqual(len(payload["entities"]), counts["Entities"])
        self.assertEqual(len(payload["events"]), counts["Timepoints"])
        self.assertEqual(len(payload["relations"]), counts["Relationships"])

    def test_changed_raw_time_overrides_stale_normalized_row(self):
        conn = sqlite3.connect(self.db_path)
        try:
            timepoint_id = conn.execute(
                "SELECT timepoint_id FROM NormalizedTimes WHERE time_type = 'exact' LIMIT 1"
            ).fetchone()[0]
            conn.execute(
                "UPDATE Timepoints SET time = ? WHERE id = ?",
                ("南宋绍兴二年四月二十七日", timepoint_id),
            )
            conn.commit()
        finally:
            conn.close()

        event = next(item for item in build_payload(self.db_path)["events"] if item["id"] == timepoint_id)
        self.assertEqual(event["rawTime"], "南宋绍兴二年四月二十七日")
        self.assertEqual((event["yearStart"], event["month"], event["day"]), (1132, 4, 27))

    def test_new_timepoint_without_normalized_row_is_visible(self):
        conn = sqlite3.connect(self.db_path)
        try:
            entity_id = conn.execute(
                "INSERT INTO Entities(title, type) VALUES (?, ?)", ("实时测试官", "官职")
            ).lastrowid
            timepoint_id = conn.execute(
                "INSERT INTO Timepoints(entity_id, time, event) VALUES (?, ?, ?)",
                (entity_id, "南宋绍兴二年", "实时新增记录"),
            ).lastrowid
            conn.commit()
        finally:
            conn.close()

        payload = build_payload(self.db_path)
        counts = self._table_counts()
        event = next(item for item in payload["events"] if item["id"] == timepoint_id)
        self.assertEqual(event["yearStart"], 1132)
        self.assertEqual(payload["meta"]["entityCount"], counts["Entities"])
        self.assertEqual(payload["meta"]["eventCount"], counts["Timepoints"])

    def test_relation_periods_stay_discrete(self):
        conn = sqlite3.connect(self.db_path)
        try:
            rel_id, subject_id, object_id = conn.execute(
                "SELECT id, subject_id, object_id FROM Relationships LIMIT 1"
            ).fetchone()
            # 两端时间点改成相隔很远的年份：不允许合并成 978—1134 的连续跨度
            conn.execute("UPDATE Timepoints SET time = ? WHERE id = ?", ("北宋太平兴国三年", subject_id))
            conn.execute("UPDATE Timepoints SET time = ? WHERE id = ?", ("南宋绍兴四年", object_id))
            conn.commit()
        finally:
            conn.close()

        relation = next(
            item for item in build_payload(self.db_path)["relations"] if item["id"] == rel_id
        )
        self.assertEqual(
            relation["periods"],
            [{"start": 978, "end": 978}, {"start": 1134, "end": 1134}],
        )
        self.assertNotIn("yearStart", relation)

    def test_bounded_endpoint_does_not_become_relation_period(self):
        conn = sqlite3.connect(self.db_path)
        try:
            rel_id, subject_id, object_id = conn.execute(
                "SELECT id, subject_id, object_id FROM Relationships LIMIT 1"
            ).fetchone()
            conn.execute(
                "UPDATE Timepoints SET time = ? WHERE id = ?",
                ("宋代（未载具体年月）", subject_id),
            )
            conn.execute(
                "UPDATE Timepoints SET time = ? WHERE id = ?",
                ("北宋太平兴国三年", object_id),
            )
            conn.commit()
        finally:
            conn.close()

        payload = build_payload(self.db_path)
        relation = next(item for item in payload["relations"] if item["id"] == rel_id)
        bounded_event = next(item for item in payload["events"] if item["id"] == subject_id)
        self.assertEqual(bounded_event["timeType"], "bounded")
        self.assertEqual(relation["periods"], [{"start": 978, "end": 978}])

    def test_cache_version_changes_after_database_commit(self):
        cache = LivePayloadCache(self.db_path, min_stable_seconds=0)
        version_before, _, _ = cache.get()

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("UPDATE Entities SET title = ? WHERE id = 1", ("实时标题变化",))
            conn.commit()
        finally:
            conn.close()

        version_after, payload, _ = cache.get()
        self.assertNotEqual(version_before, version_after)
        entity = next(item for item in payload["entities"] if item["id"] == 1)
        self.assertEqual(entity["title"], "实时标题变化")

    def test_cache_waits_for_writes_to_settle(self):
        cache = LivePayloadCache(self.db_path, min_stable_seconds=0.2)
        version_before, _, _ = cache.get()

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("UPDATE Entities SET title = ? WHERE id = 1", ("写入尚未稳定",))
            conn.commit()
        finally:
            conn.close()

        # 稳定期内仍发旧版本；稳定期过后下一次轮询才重建
        version_pending, payload_pending, _ = cache.get()
        self.assertEqual(version_before, version_pending)
        entity = next(item for item in payload_pending["entities"] if item["id"] == 1)
        self.assertNotEqual(entity["title"], "写入尚未稳定")

        time.sleep(0.3)
        version_settled, payload_settled, _ = cache.get()
        self.assertNotEqual(version_before, version_settled)
        entity = next(item for item in payload_settled["entities"] if item["id"] == 1)
        self.assertEqual(entity["title"], "写入尚未稳定")


if __name__ == "__main__":
    unittest.main()
