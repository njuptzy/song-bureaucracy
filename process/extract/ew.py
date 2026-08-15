#!/usr/bin/env python3
"""逐条提取的写入辅助（按 prompts/song_bureaucracy_entry_extraction_prompt.md 现行版）。

保证：
  - 四表 + BuildRecords 同事务，一条目一个 EntryWriter；
  - 实体复用必须 title 和 type 都一致；
  - entity()/timepoint()/relationship() 的 quotation 强制必填（辞典原文逐字片段）；
  - 同一实体已有相同 time 的时间点时优先复用（更新属性、追加引用），不重复造节点；
  - 占位节点机制：无时间信息的事实/关系可挂在 time="未知", event="占位" 的首个节点上，
    首个真实时间点复用该节点并清除占位；
  - 修改既有行（prev/succ 链维护、占位复用、属性更新）同样追加 BuildRecords 说明；
  - citation 完全重复（同目标、同出处、同 quotation）时不重复追加。
"""
import sqlite3


class EntryWriter:
    def __init__(self, db_path: str, source_entry: str, source_page: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.source_entry = source_entry
        self.source_page = source_page
        self._done = False

    # ---- 内部 ----

    def _br(self, target_table: str, target_id: int, decision: str) -> None:
        self.conn.execute(
            "INSERT INTO BuildRecords (target_table, target_id, source_entry, source_page, decision)"
            " VALUES (?,?,?,?,?)",
            (target_table, target_id, self.source_entry, self.source_page, decision),
        )

    def _insert(self, sql: str, params: tuple, table: str, decision: str) -> int:
        cur = self.conn.execute(sql, params)
        rid = cur.lastrowid
        self._br(table, rid, decision)
        return rid

    # ---- 实体 ----

    def entity(self, title: str, type_: str, decision: str,
               quotation: str | None = None) -> int:
        """title 和 type 都一致才复用；新建时 quotation 必填。"""
        row = self.conn.execute(
            "SELECT id FROM Entities WHERE title = ? AND type = ?", (title, type_)
        ).fetchone()
        if row:
            return row[0]
        if not quotation:
            raise ValueError(f"新建实体 {title}({type_}) 必须提供 quotation（辞典原文）")
        return self._insert(
            "INSERT INTO Entities (title, type, quotation) VALUES (?,?,?)",
            (title, type_, quotation),
            "Entities",
            decision,
        )

    def find_entity(self, title: str, type_: str | None = None) -> int | None:
        if type_ is None:
            row = self.conn.execute(
                "SELECT id FROM Entities WHERE title = ?", (title,)
            ).fetchone()
        else:
            row = self.conn.execute(
                "SELECT id FROM Entities WHERE title = ? AND type = ?", (title, type_)
            ).fetchone()
        return row[0] if row else None

    # ---- 时间点 ----

    def find_timepoint(self, entity_id: int, time: str) -> int | None:
        row = self.conn.execute(
            "SELECT id FROM Timepoints WHERE entity_id = ? AND time = ?"
            " ORDER BY id LIMIT 1",
            (entity_id, time),
        ).fetchone()
        return row[0] if row else None

    def ensure_placeholder(self, entity_id: int, decision: str) -> int:
        """实体无时间点时建 time="未知", event="占位" 的承载节点；已有则复用
        （优先占位节点，否则链首）。"""
        row = self.conn.execute(
            "SELECT id FROM Timepoints WHERE entity_id = ? AND time = '未知'"
            " AND event = '占位' ORDER BY id LIMIT 1",
            (entity_id,),
        ).fetchone()
        if row:
            return row[0]
        row = self.conn.execute(
            "SELECT id FROM Timepoints WHERE entity_id = ? ORDER BY id LIMIT 1",
            (entity_id,),
        ).fetchone()
        if row:
            return row[0]
        return self._insert(
            "INSERT INTO Timepoints (entity_id, time, event, quotation)"
            " VALUES (?,?,?,?)",
            (entity_id, "未知", "占位", "（无时间信息的承载节点）"),
            "Timepoints",
            decision,
        )

    def timepoint(
        self,
        entity_id: int,
        time: str,
        event: str,
        decision: str,
        quotation: str,
        attr_category: str | None = None,
        attr_officer_type: str | None = None,
        attr_grade: str | None = None,
        chain: str = "tail",
        event_type: str | None = None,
        lifecycle_effect: str | None = None,
    ) -> int:
        """新建时间点。

        - 同实体已有相同 time 的节点：复用（补属性、记 BuildRecords），不重复造；
        - 实体尚只有占位节点：复用该节点写入真实内容（清除占位）；
        - chain="tail"/"head" 维护链尾/链首互反；"none" 由调用方自行 relink。
        quotation 必填（辞典原文逐字片段）。
        """
        if not quotation:
            raise ValueError(f"时间点 {time} {event[:20]} 必须提供 quotation（辞典原文）")

        # 相同 time 复用
        row = self.conn.execute(
            "SELECT id, attr_category, attr_officer_type, attr_grade, event_type, lifecycle_effect"
            " FROM Timepoints"
            " WHERE entity_id = ? AND time = ? ORDER BY id LIMIT 1",
            (entity_id, time),
        ).fetchone()
        if row:
            tp_id = row[0]
            updates, params = [], []
            for col, new, old, overwrite in (
                ("attr_category", attr_category, row[1], False),
                ("attr_officer_type", attr_officer_type, row[2], False),
                ("attr_grade", attr_grade, row[3], False),
                ("event_type", event_type, row[4], True),
                ("lifecycle_effect", lifecycle_effect, row[5], True),
            ):
                if new and (not old or (overwrite and new != old)):
                    updates.append(f"{col} = ?")
                    params.append(new)
            if updates:
                params.append(tp_id)
                self.conn.execute(
                    f"UPDATE Timepoints SET {', '.join(updates)} WHERE id = ?", params
                )
                self._br("Timepoints", tp_id,
                         f"复用相同 time={time} 的既有节点，补充属性 "
                         f"{', '.join(u.split(' ')[0] for u in updates)}：{decision}")
            return tp_id

        # 占位复用：实体只有占位节点时写入真实内容
        ph = self.conn.execute(
            "SELECT id FROM Timepoints WHERE entity_id = ? AND time = '未知'"
            " AND event = '占位' ORDER BY id LIMIT 1",
            (entity_id,),
        ).fetchone()
        only_ph = ph and not self.conn.execute(
            "SELECT 1 FROM Timepoints WHERE entity_id = ? AND NOT (time = '未知'"
            " AND event = '占位') LIMIT 1",
            (entity_id,),
        ).fetchone()
        if only_ph:
            tp_id = ph[0]
            self.conn.execute(
                "UPDATE Timepoints SET time=?, event=?, event_type=?, lifecycle_effect=?, quotation=?,"
                " attr_category=?, attr_officer_type=?, attr_grade=? WHERE id=?",
                (time, event, event_type or "record", lifecycle_effect or "preserve", quotation,
                 attr_category, attr_officer_type, attr_grade, tp_id),
            )
            self._br("Timepoints", tp_id,
                     f"复用占位节点写入首个真实时间点（time='未知',event='占位' -> "
                     f"time='{time}'）：{decision}")
            return tp_id

        prev_id = succ_id = None
        if chain == "tail":
            row2 = self.conn.execute(
                "SELECT id FROM Timepoints WHERE entity_id = ? AND succ_id IS NULL"
                " ORDER BY id DESC LIMIT 1",
                (entity_id,),
            ).fetchone()
            prev_id = row2[0] if row2 else None
        elif chain == "head":
            row2 = self.conn.execute(
                "SELECT id FROM Timepoints WHERE entity_id = ? AND prev_id IS NULL"
                " ORDER BY id LIMIT 1",
                (entity_id,),
            ).fetchone()
            succ_id = row2[0] if row2 else None
        tp_id = self._insert(
            "INSERT INTO Timepoints (entity_id, time, event, event_type, lifecycle_effect, prev_id, succ_id,"
            " attr_category, attr_officer_type, attr_grade, quotation)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (entity_id, time, event, event_type or "record", lifecycle_effect or "preserve", prev_id, succ_id,
             attr_category, attr_officer_type, attr_grade, quotation),
            "Timepoints",
            decision,
        )
        if prev_id is not None:
            self.relink(prev_id, succ_id=tp_id,
                        decision=f"接入新时间点 {tp_id}（{time}），succ 指向它")
        if succ_id is not None:
            self.relink(succ_id, prev_id=tp_id,
                        decision=f"链首前插入新时间点 {tp_id}（{time}），prev 指向它")
        return tp_id

    def relink(self, tp_id: int, decision: str,
               prev_id: int | None = ..., succ_id: int | None = ...) -> None:
        """修改既有节点的链指针并追加 BuildRecords（修改既有行必须留审计）。"""
        row = self.conn.execute(
            "SELECT prev_id, succ_id FROM Timepoints WHERE id = ?", (tp_id,)
        ).fetchone()
        assert row, f"Timepoints {tp_id} 不存在"
        new_prev = row[0] if prev_id is ... else prev_id
        new_succ = row[1] if succ_id is ... else succ_id
        if new_prev == row[0] and new_succ == row[1]:
            return
        self.conn.execute(
            "UPDATE Timepoints SET prev_id = ?, succ_id = ? WHERE id = ?",
            (new_prev, new_succ, tp_id),
        )
        self._br("Timepoints", tp_id,
                 f"链指针修改 prev {row[0]}->{new_prev}, succ {row[1]}->{new_succ}：{decision}")

    # ---- 关系 ----

    def relationship(
        self,
        subject_tp: int,
        object_tp: int,
        relation_type: str,
        decision: str,
        quotation: str,
        staff_quota=None,
        staff_type=None,
    ) -> int:
        """quotation 必填；完全相同（两端+类型）的关系已存在时复用不重复建。"""
        if not quotation:
            raise ValueError(f"关系 {relation_type} 必须提供 quotation（辞典原文）")
        row = self.conn.execute(
            "SELECT id FROM Relationships WHERE subject_id=? AND object_id=?"
            " AND relation_type=?",
            (subject_tp, object_tp, relation_type),
        ).fetchone()
        if row:
            return row[0]
        return self._insert(
            "INSERT INTO Relationships (subject_id, object_id, relation_type,"
            " staff_quota, staff_type, quotation)"
            " VALUES (?,?,?,?,?,?)",
            (subject_tp, object_tp, relation_type, staff_quota, staff_type, quotation),
            "Relationships",
            decision,
        )

    # ---- 引用 ----

    def citation(
        self,
        target_table: str,
        target_id: int,
        citation: str,
        quotation: str,
        decision: str,
        note: str | None = None,
        conflict_flag: int = 0,
    ) -> int:
        """完全相同（目标+出处+quotation）的引用已存在时不重复追加。"""
        row = self.conn.execute(
            "SELECT id FROM Citations WHERE target_table=? AND target_id=?"
            " AND citation=? AND quotation=?",
            (target_table, target_id, citation, quotation),
        ).fetchone()
        if row:
            return row[0]
        return self._insert(
            "INSERT INTO Citations (target_table, target_id, citation, quotation, note, conflict_flag)"
            " VALUES (?,?,?,?,?,?)",
            (target_table, target_id, citation, quotation, note, conflict_flag),
            "Citations",
            decision,
        )

    # ---- 事务 ----

    def commit(self) -> None:
        self.conn.commit()
        self._done = True
        self.conn.close()

    def __del__(self):
        if not self._done:
            try:
                self.conn.rollback()
                self.conn.close()
            except Exception:
                pass
