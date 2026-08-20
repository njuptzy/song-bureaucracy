import http.client
import importlib.util
import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer


ROOT = Path(__file__).resolve().parents[2]
SERVER_PATH = ROOT / "vis/ch1t12-design-vis/server.py"
SPEC = importlib.util.spec_from_file_location("ch1t12_design_server", SERVER_PATH)
SERVER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SERVER)


def make_connection(*, optional_columns: bool = False) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE Entities (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            type TEXT NOT NULL
        );
        CREATE TABLE Timepoints (
            id INTEGER PRIMARY KEY,
            entity_id INTEGER NOT NULL,
            time TEXT,
            event TEXT
        );
        """
    )
    optional_sql = ""
    if optional_columns:
        optional_sql = """
            , relation_subtype TEXT
            , change_event_id INTEGER
            , relation_group_id TEXT
            , relation_scope TEXT
        """
    connection.execute(
        f"""
        CREATE TABLE Relationships (
            id INTEGER PRIMARY KEY,
            subject_id INTEGER NOT NULL,
            object_id INTEGER NOT NULL,
            relation_type TEXT,
            quotation TEXT
            {optional_sql}
        )
        """
    )
    connection.executemany(
        "INSERT INTO Entities(id, title, type) VALUES (?, ?, ?)",
        [(1, "甲", "机构"), (2, "乙", "机构"), (3, "丙", "机构")],
    )
    connection.executemany(
        "INSERT INTO Timepoints(id, entity_id, time, event) VALUES (?, ?, ?, ?)",
        [
            (10, 1, "北宋太平兴国八年三月七日", "甲发生变化"),
            (11, 1, "北宋淳化四年十月", "甲的后续状态"),
            (20, 2, "北宋淳化五年十二月二十四日", "乙发生变化"),
            (30, 3, "宋代（未载具体年月）", "丙发生变化"),
        ],
    )
    return connection


def normalized_times(connection: sqlite3.Connection) -> dict[int, dict]:
    return {
        row["id"]: SERVER._normalized_time_payload(row["time"])
        for row in connection.execute("SELECT id, time FROM Timepoints")
    }


class Ch1t12DesignServerContractTest(unittest.TestCase):
    def test_composite_events_endpoint_returns_three_bands(self):
        payload = {
            "entities": [
                {"id": 1, "title": "甲机构", "type": "机构"},
                {"id": 2, "title": "乙官职", "type": "官职"},
            ],
            "hierarchyEdges": [],
            "staffEdges": [{
                "id": 20, "org": 1, "official": 2,
                "staff_quota": "二员", "staff_type": "官",
                "periods": [{"start": 1000, "end": 1100}],
            }],
            "changeRelations": [{
                "id": 30, "relation_type": "职掌·移交",
                "display_relation_type": "职掌·移交",
                "source": 1, "target": 1,
                "source_time": {"year_start": 1050, "year_end": 1050, "raw_time": "1050年"},
                "target_time": {"year_start": 1050, "year_end": 1050},
                "evidence_key": "R30", "quotation": "甲机构移交职掌",
            }],
            "timepoints": {"1": [{
                "id": 10, "year_start": 1040, "year_end": 1040,
                "raw_time": "1040年", "event": "始置甲机构",
            }]},
            "citations": {"R30": [{"citation": "出处", "quotation": "甲机构移交职掌"}]},
        }
        previous = SERVER.build_payload
        SERVER.build_payload = lambda include_details=True: payload
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), SERVER.Handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        connection = http.client.HTTPConnection("127.0.0.1", httpd.server_port, timeout=5)
        try:
            connection.request("GET", "/api/composite-events?focus_entity_id=1&year=1050&include_details=1")
            response = connection.getresponse()
            result = json.loads(response.read())
            self.assertEqual(response.status, 200)
            self.assertEqual(set(result["bands"]), {"institution", "staff", "duty"})
            self.assertEqual(result["bands"]["staff"][0]["displaySummary"], "二员，官")
            self.assertEqual(result["bands"]["duty"][0]["evidenceKeys"], ["R30"])
        finally:
            connection.close()
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=5)
            SERVER.build_payload = previous

    def test_entity_detail_dictionary_sections_are_not_truncated(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute(
            "CREATE TABLE dictionary (title, catalog, page, text, fields)"
        )
        long_duty = "职掌原文" * 120
        connection.execute(
            "INSERT INTO dictionary VALUES (?, ?, ?, ?, ?)",
            ("尚书省", "第一编/尚书省", "192", "官署名。", json.dumps({
                "职掌": long_duty,
                "简称与别名": "尚书都省" * 200,
            }, ensure_ascii=False)),
        )
        row = connection.execute("SELECT * FROM dictionary").fetchone()
        try:
            summary = SERVER._dictionary_row_payload(row)
            detail = SERVER._dictionary_row_payload(row, full_sections=True)
        finally:
            connection.close()

        self.assertEqual(len(summary["duty"]), SERVER.SECTION_LEN)
        self.assertEqual(detail["duty"], long_duty)
        self.assertGreater(len(detail["aliases"]), SERVER.SECTION_LEN)

    def test_normalized_time_payload_keeps_calendar_ordering_fields(self):
        payload = SERVER._normalized_time_payload("北宋太平兴国八年三月七日")
        self.assertEqual(payload["raw_time"], "北宋太平兴国八年三月七日")
        self.assertEqual((payload["year_start"], payload["year_end"]), (983, 983))
        self.assertEqual((payload["month"], payload["day"]), (3, 7))
        self.assertEqual(payload["is_leap_month"], 0)
        self.assertEqual(payload["end_month"], 3)
        self.assertEqual(payload["end_day"], 7)
        self.assertEqual(payload["month_text"], "三月")
        self.assertEqual(payload["day_text"], "七日")
        self.assertIsInstance(payload["sort_order"], int)
        self.assertEqual(payload["time_type"], "exact")

    def test_legacy_schema_emits_atomic_unclassified_change_relations(self):
        connection = make_connection()
        try:
            connection.executemany(
                "INSERT INTO Relationships VALUES (?, ?, ?, ?, ?)",
                [
                    (1, 10, 20, "前后演变", "甲改为乙"),
                    (2, 20, 30, "职掌·移交", "乙职掌移交丙"),
                    (3, 10, 30, "演变·改称", "甲改称丙"),
                    (4, 10, 20, "上下级机构", "乙隶甲"),
                    (5, 10, 11, "前后演变", "甲内部状态演变"),
                ],
            )
            relations = SERVER._build_change_relations(connection, normalized_times(connection))
        finally:
            connection.close()

        self.assertEqual([relation["id"] for relation in relations], [1, 2, 3, 5])
        legacy = relations[0]
        self.assertEqual(legacy["relation_type"], "前后演变")
        self.assertIsNone(legacy["relation_subtype"])
        self.assertEqual(legacy["classification_status"], "unclassified")
        self.assertEqual(legacy["display_relation_type"], "前后演变（未分类）")
        self.assertEqual((legacy["source"], legacy["target"]), (1, 2))
        self.assertEqual((legacy["source_timepoint_id"], legacy["target_timepoint_id"]), (10, 20))
        self.assertEqual(legacy["source_time"]["year_start"], 983)
        self.assertEqual(legacy["target_time"]["year_start"], 994)
        self.assertEqual(legacy["evidence_key"], "R1")
        self.assertIsNone(legacy["change_event_id"])
        self.assertIsNone(legacy["relation_group_id"])
        self.assertNotIn("periods", legacy)
        self.assertNotIn("effective_year", legacy)
        self.assertEqual(relations[1]["relation_type"], "职掌·移交")
        self.assertEqual(relations[3]["source"], relations[3]["target"])

    def test_optional_relationship_columns_are_passed_through_without_inference(self):
        connection = make_connection(optional_columns=True)
        try:
            connection.execute(
                """
                INSERT INTO Relationships(
                    id, subject_id, object_id, relation_type, quotation,
                    relation_subtype, change_event_id, relation_group_id, relation_scope
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (7, 10, 20, "前后演变", "原文", "演变·合并", 91, "merge-91", "机构"),
            )
            relation = SERVER._build_change_relations(
                connection, normalized_times(connection)
            )[0]
        finally:
            connection.close()

        self.assertEqual(relation["relation_subtype"], "演变·合并")
        self.assertEqual(relation["classification_status"], "classified")
        self.assertEqual(relation["display_relation_type"], "演变·合并")
        self.assertEqual(relation["change_event_id"], 91)
        self.assertEqual(relation["relation_group_id"], "merge-91")
        self.assertEqual(relation["relation_scope"], "机构")
        self.assertEqual(relation["source_time"]["year_start"], 983)
        self.assertEqual(relation["target_time"]["year_start"], 994)

    def test_revision_routes_persist_small_draft_patch_without_touching_formal_database(self):
        from vis.tests.test_revision_store import make_database

        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "entries.db"
            make_database(database)
            previous_store = SERVER._revision_store
            SERVER._revision_store = SERVER.RevisionStore(database, SERVER._normalized_time_payload)
            httpd = ThreadingHTTPServer(("127.0.0.1", 0), SERVER.Handler)
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            connection = http.client.HTTPConnection("127.0.0.1", httpd.server_port, timeout=5)
            try:
                connection.request("GET", "/api/revisions/state")
                response = connection.getresponse()
                state = json.loads(response.read())
                self.assertEqual(response.status, 200)
                self.assertEqual(state["draft"]["group_count"], 0)

                operation = {
                    "reason": "核对原文后校正",
                    "operations": [{
                        "action": "update",
                        "target_table": "Timepoints",
                        "target_id": 10,
                        "after": {"time": "1005年"},
                        "evidence": [{"mode": "existing", "citation_id": 1000}],
                    }],
                }
                connection.request(
                    "POST",
                    "/api/revisions/draft/operations",
                    body=json.dumps(operation, ensure_ascii=False).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                response = connection.getresponse()
                created = json.loads(response.read())
                self.assertEqual(response.status, 200)
                self.assertTrue(created["preview"]["validation"]["valid"])

                connection.request("GET", "/api/revisions/draft/preview")
                response = connection.getresponse()
                raw_preview = response.read()
                preview = json.loads(raw_preview)
                self.assertEqual(response.status, 200)
                self.assertLess(len(raw_preview), 100_000)
                self.assertEqual(preview["patch"]["timepoints"]["upsert"][0]["time"], "1005年")
                with sqlite3.connect(database) as formal:
                    self.assertEqual(
                        formal.execute("SELECT time FROM Timepoints WHERE id=10").fetchone()[0],
                        "1000年",
                    )
            finally:
                connection.close()
                httpd.shutdown()
                httpd.server_close()
                thread.join(timeout=5)
                SERVER._revision_store = previous_store


if __name__ == "__main__":
    unittest.main()
