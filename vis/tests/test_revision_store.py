import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "vis/ch2t7-design-vis/revision_store.py"
SPEC = importlib.util.spec_from_file_location("revision_store", MODULE_PATH)
REVISION = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(REVISION)


def normalize_time(raw_time: str) -> dict:
    digits = "".join(character for character in raw_time if character.isdigit())
    year = int(digits[:4]) if len(digits) >= 4 else None
    return {
        "raw_time": raw_time,
        "year_start": year,
        "year_end": year,
        "month": None,
        "is_leap_month": 0,
        "day": None,
        "end_month": None,
        "end_is_leap_month": 0,
        "end_day": None,
        "month_text": "",
        "day_text": "",
        "end_month_text": "",
        "end_day_text": "",
        "sort_order": year * 10000 if year is not None else None,
        "time_type": "exact" if year is not None else "unresolved",
        "parse_note": "测试标准化",
    }


def make_database(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(
        """
        CREATE TABLE Entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT,
            quotation TEXT
        );
        CREATE TABLE Timepoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id INTEGER NOT NULL,
            time TEXT,
            event TEXT,
            prev_id INTEGER,
            succ_id INTEGER,
            attr_category TEXT,
            attr_officer_type TEXT,
            attr_grade TEXT,
            quotation TEXT,
            FOREIGN KEY(entity_id) REFERENCES Entities(id),
            FOREIGN KEY(prev_id) REFERENCES Timepoints(id),
            FOREIGN KEY(succ_id) REFERENCES Timepoints(id)
        );
        CREATE TABLE Relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            object_id INTEGER NOT NULL,
            relation_type TEXT,
            staff_quota INTEGER,
            staff_type TEXT,
            quotation TEXT,
            FOREIGN KEY(subject_id) REFERENCES Timepoints(id),
            FOREIGN KEY(object_id) REFERENCES Timepoints(id)
        );
        CREATE TABLE Citations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_table TEXT NOT NULL,
            target_id INTEGER NOT NULL,
            citation TEXT,
            quotation TEXT,
            note TEXT,
            conflict_flag INTEGER DEFAULT 0
        );
        CREATE TABLE NormalizedTimes (
            timepoint_id INTEGER PRIMARY KEY,
            raw_time TEXT NOT NULL,
            year_start INTEGER,
            year_end INTEGER,
            month INTEGER,
            is_leap_month INTEGER NOT NULL DEFAULT 0,
            day INTEGER,
            end_month INTEGER,
            end_is_leap_month INTEGER NOT NULL DEFAULT 0,
            end_day INTEGER,
            month_text TEXT,
            day_text TEXT,
            end_month_text TEXT,
            end_day_text TEXT,
            sort_order INTEGER,
            time_type TEXT NOT NULL,
            parse_note TEXT,
            FOREIGN KEY(timepoint_id) REFERENCES Timepoints(id)
        );
        CREATE TABLE BuildRecords (
            id INTEGER PRIMARY KEY,
            target_table TEXT NOT NULL,
            target_id INTEGER NOT NULL,
            source_entry TEXT NOT NULL,
            source_page TEXT,
            decision TEXT NOT NULL
        );
        """
    )
    connection.executemany(
        "INSERT INTO Entities(id,title,type,quotation) VALUES (?,?,?,?)",
        [(1, "甲司", "机构", "甲司"), (2, "乙司", "机构", "乙司"), (3, "甲官", "官职", "甲官")],
    )
    connection.executemany(
        """
        INSERT INTO Timepoints(
            id,entity_id,time,event,prev_id,succ_id,attr_category,
            attr_officer_type,attr_grade,quotation
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        [
            (10, 1, "1000年", "甲司初置", None, None, "机构", "", "", "甲司初置"),
            (11, 1, "1020年", "甲司后续", 10, None, "机构", "", "", "甲司后续"),
            (20, 2, "1010年", "乙司初置", None, None, "机构", "", "", "乙司初置"),
            (30, 3, "1010年", "甲官设置", None, None, "", "文官", "", "甲官设置"),
        ],
    )
    connection.execute("UPDATE Timepoints SET succ_id=11 WHERE id=10")
    connection.executemany(
        "INSERT INTO NormalizedTimes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [tuple([row_id, *normalize_time(raw).values()]) for row_id, raw in [(10, "1000年"), (11, "1020年"), (20, "1010年"), (30, "1010年")]],
    )
    connection.executemany(
        "INSERT INTO Relationships VALUES (?,?,?,?,?,?,?)",
        [
            (100, 10, 20, "前后演变", None, None, "甲司改为乙司"),
            (101, 10, 30, "前后演变", None, None, "历史遗留的跨类型关系"),
        ],
    )
    connection.executemany(
        "INSERT INTO Citations VALUES (?,?,?,?,?,?,?)",
        [
            (1000, "Timepoints", 10, "《测试志》卷一", "甲司初置", "", 0),
            (1001, "Relationships", 100, "《测试志》卷一", "甲司改为乙司", "", 0),
        ],
    )
    connection.execute(
        "INSERT INTO BuildRecords VALUES (1,'Entities',1,'#1 甲司','1','测试构造')"
    )
    connection.commit()
    connection.close()


class RevisionStoreTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.database = self.root / "entries.db"
        make_database(self.database)
        self.store = REVISION.RevisionStore(self.database, normalize_time)

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def existing_evidence(citation_id=1000):
        return [{"mode": "existing", "citation_id": citation_id}]

    def test_draft_preview_undo_redo_and_refresh_do_not_write_formal_database(self):
        self.store.add_group({
            "label": "校正甲司纪年",
            "reason": "原时间录入错误",
            "operations": [{
                "action": "update",
                "target_table": "Timepoints",
                "target_id": 10,
                "after": {"time": "1005年", "event": "甲司设置"},
                "evidence": self.existing_evidence(),
            }],
        })
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute("SELECT time FROM Timepoints WHERE id=10").fetchone()[0], "1000年")

        preview = self.store.preview()
        self.assertTrue(preview["validation"]["valid"])
        changed = preview["patch"]["timepoints"]["upsert"]
        self.assertEqual(changed[0]["time"], "1005年")
        self.assertEqual(changed[0]["year_start"], 1005)
        self.assertLess(len(REVISION.canonical_json(preview)), 100_000)

        self.store.undo()
        self.assertEqual(self.store.preview()["patch"]["timepoints"]["upsert"], [])
        refreshed = REVISION.RevisionStore(self.database, normalize_time)
        self.assertTrue(refreshed.state()["draft"]["can_redo"])
        refreshed.redo()
        self.assertEqual(refreshed.preview()["patch"]["timepoints"]["upsert"][0]["time"], "1005年")

    def test_commit_updates_four_tables_and_sidecar_atomically(self):
        self.store.add_group({
            "reason": "依据新核对的原文校正纪年",
            "operations": [{
                "action": "update",
                "target_table": "Timepoints",
                "target_id": 10,
                "after": {"time": "1005年"},
                "evidence": [{
                    "mode": "new",
                    "citation": "《测试志》卷二",
                    "quotation": "景德二年置甲司",
                    "note": "新证据",
                }],
            }],
        })
        result = self.store.commit("校正甲司设置纪年")
        self.assertEqual(result["commit"]["parent_hash"], self.store.state()["baseline"])
        self.assertGreaterEqual(result["commit"]["operation_count"], 3)
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute("SELECT time FROM Timepoints WHERE id=10").fetchone()[0], "1005年")
            self.assertEqual(connection.execute("SELECT year_start FROM NormalizedTimes WHERE timepoint_id=10").fetchone()[0], 1005)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM Citations WHERE target_table='Timepoints' AND target_id=10").fetchone()[0], 2)
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        self.assertTrue(self.store.rollback_db.exists())
        self.assertTrue(self.store.rollback_revisions_db.exists())

    def test_delete_timepoint_expands_dependencies_and_restore_recreates_exact_state(self):
        baseline = self.store.state()["baseline"]
        self.store.add_group({
            "label": "删除误建时间点",
            "reason": "该事实不见于原文",
            "operations": [{
                "action": "delete",
                "target_table": "Timepoints",
                "target_id": 10,
                "evidence": self.existing_evidence(),
            }],
        })
        preview = self.store.preview()
        self.assertIn(10, preview["patch"]["timepoints"]["delete"])
        self.assertEqual(set(preview["patch"]["relationships"]["delete"]), {100, 101})
        self.store.commit("删除误建甲司时间点")
        with sqlite3.connect(self.database) as connection:
            self.assertIsNone(connection.execute("SELECT id FROM Timepoints WHERE id=10").fetchone())
            self.assertIsNone(connection.execute("SELECT prev_id FROM Timepoints WHERE id=11").fetchone()[0])
        restore_preview = self.store.restore_preview(baseline)
        self.assertGreater(restore_preview["operation_count"], 4)
        self.store.restore(baseline)
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute("SELECT succ_id FROM Timepoints WHERE id=10").fetchone()[0], 11)
            self.assertEqual(connection.execute("SELECT prev_id FROM Timepoints WHERE id=11").fetchone()[0], 10)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM Relationships WHERE id IN (100,101)").fetchone()[0], 2)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM Citations WHERE id IN (1000,1001)").fetchone()[0], 2)
        self.assertEqual(self.store.list_commits()["commits"][0]["reverts_hash"], baseline)

    def test_relation_insert_requires_same_entity_type_and_can_commit(self):
        with self.assertRaisesRegex(REVISION.RevisionError, "类型不一致"):
            self.store.add_group({
                "reason": "测试非法关系",
                "operations": [{
                    "action": "insert",
                    "target_table": "Relationships",
                    "after": {"subject_id": 20, "object_id": 30},
                    "evidence": [{"mode": "new", "citation": "测试", "quotation": "测试引文"}],
                }],
            })
        self.store.add_group({
            "reason": "补录甲司与乙司的另一条演变证据",
            "operations": [{
                "action": "insert",
                "target_table": "Relationships",
                "after": {"subject_id": 11, "object_id": 20},
                "evidence": [{"mode": "new", "citation": "《测试志》卷三", "quotation": "甲司后改乙司"}],
            }],
        })
        result = self.store.commit("补建演变关系")
        relation_operation = next(
            operation for operation in result["commit"]["operations"]
            if operation["target_table"] == "Relationships" and not operation["automatic"]
        )
        self.assertFalse(relation_operation["target_id"].startswith("tmp:"))

    def test_insert_adjacent_timepoint_rewires_chain_and_creates_evidence(self):
        self.store.add_group({
            "reason": "在两条既有记载之间补录明确时间点",
            "operations": [{
                "action": "insert",
                "target_table": "Timepoints",
                "after": {
                    "entity_id": 1, "time": "1010年", "event": "甲司中间状态",
                    "prev_id": 10, "succ_id": 11, "attr_category": "机构",
                },
                "evidence": [{
                    "mode": "new", "citation": "《测试志》卷四", "quotation": "大中祥符三年甲司仍置",
                }],
            }],
        })
        result = self.store.commit("补录甲司中间时间点")
        operation = next(
            item for item in result["commit"]["operations"]
            if item["target_table"] == "Timepoints" and not item["automatic"]
        )
        inserted_id = int(operation["target_id"])
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute("SELECT succ_id FROM Timepoints WHERE id=10").fetchone()[0], inserted_id)
            self.assertEqual(connection.execute("SELECT prev_id FROM Timepoints WHERE id=11").fetchone()[0], inserted_id)
            self.assertEqual(connection.execute("SELECT prev_id,succ_id FROM Timepoints WHERE id=?", (inserted_id,)).fetchone(), (10, 11))
            self.assertEqual(connection.execute("SELECT year_start FROM NormalizedTimes WHERE timepoint_id=?", (inserted_id,)).fetchone()[0], 1010)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM Citations WHERE target_table='Timepoints' AND target_id=?", (inserted_id,)).fetchone()[0], 1)

    def test_relation_endpoint_update_and_direct_delete(self):
        self.store.add_group({
            "reason": "原文方向与录入方向相反",
            "operations": [{
                "action": "update", "target_table": "Relationships", "target_id": 100,
                "after": {"subject_id": 20, "object_id": 10},
                "evidence": [{"mode": "existing", "citation_id": 1001}],
            }],
        })
        updated = self.store.commit("调整甲乙演变方向")["commit"]
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute("SELECT subject_id,object_id FROM Relationships WHERE id=100").fetchone(), (20, 10))
        self.store.add_group({
            "reason": "复核后确认该演变关系不成立",
            "operations": [{
                "action": "delete", "target_table": "Relationships", "target_id": 100,
                "evidence": [{"mode": "existing", "citation_id": 1001}],
            }],
        })
        self.store.commit("删除错误的甲乙演变关系")
        with sqlite3.connect(self.database) as connection:
            self.assertIsNone(connection.execute("SELECT id FROM Relationships WHERE id=100").fetchone())
            self.assertIsNone(connection.execute("SELECT id FROM Citations WHERE id=1001").fetchone())
        self.store.restore(updated["hash"], "恢复关系删除前版本")
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute("SELECT subject_id,object_id FROM Relationships WHERE id=100").fetchone(), (20, 10))

    def test_reason_evidence_and_external_change_are_hard_validation_boundaries(self):
        with self.assertRaisesRegex(REVISION.RevisionError, "理由"):
            self.store.add_group({"operations": [{}]})
        with self.assertRaisesRegex(REVISION.RevisionError, "证据"):
            self.store.add_group({
                "reason": "缺少证据",
                "operations": [{
                    "action": "update", "target_table": "Timepoints",
                    "target_id": 10, "after": {"event": "改动"},
                }],
            })
        self.store.add_group({
            "reason": "准备修改",
            "operations": [{
                "action": "update", "target_table": "Timepoints",
                "target_id": 10, "after": {"event": "改动"},
                "evidence": self.existing_evidence(),
            }],
        })
        with sqlite3.connect(self.database) as connection:
            connection.execute("UPDATE Entities SET quotation='外部脚本改动' WHERE id=1")
            connection.commit()
        with self.assertRaisesRegex(REVISION.RevisionError, "外部脚本"):
            self.store.commit("不应成功")
        self.assertEqual(self.store.state()["draft"]["group_count"], 1)

    def test_database_without_normalized_times_keeps_time_normalization_derived_only(self):
        other_database = self.root / "entries-without-normalized.db"
        make_database(other_database)
        with sqlite3.connect(other_database) as connection:
            connection.execute("DROP TABLE NormalizedTimes")
        store = REVISION.RevisionStore(other_database, normalize_time)
        store.add_group({
            "reason": "兼容无派生表的结果库",
            "operations": [{
                "action": "update", "target_table": "Timepoints", "target_id": 10,
                "after": {"time": "1006年"},
                "evidence": [{"mode": "existing", "citation_id": 1000}],
            }],
        })
        preview = store.preview()
        self.assertEqual(preview["patch"]["normalized_times"]["upsert"], [])
        store.commit("校正无派生表结果库的纪年")
        with sqlite3.connect(other_database) as connection:
            self.assertEqual(connection.execute("SELECT time FROM Timepoints WHERE id=10").fetchone()[0], "1006年")

    def test_failure_after_business_writes_rolls_back_database_and_head_together(self):
        baseline = self.store.state()["head"]
        with sqlite3.connect(self.database) as connection:
            old_event = connection.execute("SELECT event FROM Timepoints WHERE id=10").fetchone()[0]
        self.store.add_group({
            "reason": "验证事务回滚",
            "operations": [{
                "action": "update", "target_table": "Timepoints", "target_id": 10,
                "after": {"event": "不应落库"},
                "evidence": self.existing_evidence(),
            }],
        })
        original_check = self.store._database_checks
        self.store._database_checks = lambda *_: (_ for _ in ()).throw(
            REVISION.RevisionError("注入提交失败", code="INJECTED_FAILURE")
        )
        try:
            with self.assertRaisesRegex(REVISION.RevisionError, "注入提交失败"):
                self.store.commit("不应成功")
        finally:
            self.store._database_checks = original_check
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(connection.execute("SELECT event FROM Timepoints WHERE id=10").fetchone()[0], old_event)
        self.assertEqual(self.store.state()["head"], baseline)
        self.assertEqual(self.store.state()["draft"]["group_count"], 1)


if __name__ == "__main__":
    unittest.main()
