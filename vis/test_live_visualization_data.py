import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from vis.export_visualization_data import build_payload
from vis.serve_visualization_v2 import LivePayloadCache


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DB = ROOT / "vis/data/song_bureaucracy_visualization.db"


class LiveVisualizationDataTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "live.db"
        shutil.copy2(SOURCE_DB, self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_current_database_builds_complete_payload(self):
        payload = build_payload(self.db_path)
        self.assertEqual(len(payload["entities"]), 981)
        self.assertEqual(len(payload["events"]), 1813)
        self.assertEqual(len(payload["relations"]), 1177)

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
        event = next(item for item in payload["events"] if item["id"] == timepoint_id)
        self.assertEqual(event["yearStart"], 1132)
        self.assertEqual(payload["meta"]["entityCount"], 982)
        self.assertEqual(payload["meta"]["eventCount"], 1814)

    def test_cache_version_changes_after_database_commit(self):
        cache = LivePayloadCache(self.db_path)
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


if __name__ == "__main__":
    unittest.main()
