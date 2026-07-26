#!/usr/bin/env python3
"""修复 79–98 批次人工复核问题：链序与重复关系（幂等）。"""
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t4.db")


def audit(conn, table, rid, source, page, decision):
    conn.execute(
        "INSERT INTO BuildRecords(target_table,target_id,source_entry,source_page,decision)"
        " VALUES(?,?,?,?,?)",
        (table, rid, source, page, decision),
    )


def entity_id(conn, title):
    row = conn.execute("SELECT id FROM Entities WHERE title=?", (title,)).fetchone()
    assert row, f"缺实体 {title}"
    return row[0]


def tp_id(conn, title, time):
    row = conn.execute(
        "SELECT t.id FROM Timepoints t JOIN Entities e ON e.id=t.entity_id"
        " WHERE e.title=? AND t.time=?",
        (title, time),
    ).fetchone()
    assert row, f"{title} 缺 time={time}"
    return row[0]


def rechain(conn, title, times, source, page, reason):
    ids = [tp_id(conn, title, time) for time in times]
    for i, tid in enumerate(ids):
        old = conn.execute(
            "SELECT prev_id,succ_id FROM Timepoints WHERE id=?", (tid,)
        ).fetchone()
        new = (ids[i - 1] if i else None, ids[i + 1] if i + 1 < len(ids) else None)
        if old == new:
            continue
        conn.execute(
            "UPDATE Timepoints SET prev_id=?,succ_id=? WHERE id=?", (*new, tid)
        )
        audit(
            conn, "Timepoints", tid, source, page,
            f"人工复核重排 {title} 时间链：prev {old[0]}->{new[0]}, "
            f"succ {old[1]}->{new[1]}；{reason}",
        )


def citation_source(conn, citation_id):
    row = conn.execute(
        "SELECT source_entry,source_page FROM BuildRecords"
        " WHERE target_table='Citations' AND target_id=? ORDER BY id LIMIT 1",
        (citation_id,),
    ).fetchone()
    return row or ("人工复核", "")


def move_citations(conn, target_table, old_id, new_id, reason):
    rows = conn.execute(
        "SELECT id,citation,quotation FROM Citations"
        " WHERE target_table=? AND target_id=? ORDER BY id",
        (target_table, old_id),
    ).fetchall()
    for cid, citation, quotation in rows:
        duplicate = conn.execute(
            "SELECT id FROM Citations WHERE target_table=? AND target_id=?"
            " AND citation=? AND quotation=?",
            (target_table, new_id, citation, quotation),
        ).fetchone()
        if duplicate:
            conn.execute(
                "DELETE FROM BuildRecords WHERE target_table='Citations' AND target_id=?",
                (cid,),
            )
            conn.execute("DELETE FROM Citations WHERE id=?", (cid,))
            continue
        conn.execute("UPDATE Citations SET target_id=? WHERE id=?", (new_id, cid))
        source, page = citation_source(conn, cid)
        audit(conn, "Citations", cid, source, page, reason)


def merge_relationship(conn, old_id, new_id, source, page, reason):
    if old_id == new_id:
        return
    move_citations(conn, "Relationships", old_id, new_id, reason)
    conn.execute(
        "DELETE FROM BuildRecords WHERE target_table='Relationships' AND target_id=?",
        (old_id,),
    )
    conn.execute("DELETE FROM Relationships WHERE id=?", (old_id,))
    audit(conn, "Relationships", new_id, source, page, reason)


def merge_timepoint(conn, old_id, new_id, source, page, reason):
    if old_id == new_id:
        return
    refs = conn.execute(
        "SELECT COUNT(*) FROM Relationships WHERE subject_id=? OR object_id=?",
        (old_id, old_id),
    ).fetchone()[0]
    assert refs == 0, f"待删时间点 {old_id} 仍被 {refs} 条关系引用"
    old_prev, old_succ = conn.execute(
        "SELECT prev_id,succ_id FROM Timepoints WHERE id=?", (old_id,)
    ).fetchone()
    prev_refs = [r[0] for r in conn.execute(
        "SELECT id FROM Timepoints WHERE prev_id=?", (old_id,)
    )]
    succ_refs = [r[0] for r in conn.execute(
        "SELECT id FROM Timepoints WHERE succ_id=?", (old_id,)
    )]
    for tid in prev_refs:
        replacement = None if old_succ == tid else old_prev
        conn.execute("UPDATE Timepoints SET prev_id=? WHERE id=?", (replacement, tid))
        audit(conn, "Timepoints", tid, source, page, f"合并节点 {old_id}->{new_id} 时迁移 prev 指针；{reason}")
    for tid in succ_refs:
        replacement = None if old_prev == tid else old_succ
        conn.execute("UPDATE Timepoints SET succ_id=? WHERE id=?", (replacement, tid))
        audit(conn, "Timepoints", tid, source, page, f"合并节点 {old_id}->{new_id} 时迁移 succ 指针；{reason}")
    move_citations(conn, "Timepoints", old_id, new_id, reason)
    conn.execute(
        "DELETE FROM BuildRecords WHERE target_table='Timepoints' AND target_id=?",
        (old_id,),
    )
    conn.execute("DELETE FROM Timepoints WHERE id=?", (old_id,))
    audit(conn, "Timepoints", new_id, source, page, reason)


def relation_rows(conn, subject_title, object_title, kind):
    return conn.execute(
        "SELECT r.id,st.time,ot.time FROM Relationships r"
        " JOIN Timepoints st ON st.id=r.subject_id"
        " JOIN Entities se ON se.id=st.entity_id"
        " JOIN Timepoints ot ON ot.id=r.object_id"
        " JOIN Entities oe ON oe.id=ot.entity_id"
        " WHERE se.title=? AND oe.title=? AND r.relation_type=? ORDER BY r.id",
        (subject_title, object_title, kind),
    ).fetchall()


def main():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        conn.execute("BEGIN")
        rechain(
            conn, "审官院",
            ["北宋淳化四年二月二十八日", "北宋淳化四年五月二十日", "北宋熙宁三年五月二十八日"],
            "审官院", "101", "二月由磨勘京朝官院改名，五月接收差遣院",
        )
        rechain(
            conn, "吏部尚书铨",
            ["隋朝", "唐朝", "唐、五代", "宋立国之初", "北宋初", "北宋太平兴国六年九月十二日"],
            "吏部三铨", "100", "唐五代与宋立国之初节点不得接在太平兴国终结节点之后",
        )

        # 统称关系只保留唐、五代节点的一条边；宋初原文作为第二条 citation 保留。
        for title in ("吏部尚书铨", "吏部西铨", "吏部东铨"):
            rows = relation_rows(conn, "吏部三铨", title, "统称与实例")
            if len(rows) > 1:
                keep = next(row for row in rows if row[1] == "唐、五代")
                for row in rows:
                    if row[0] != keep[0]:
                        merge_relationship(
                            conn, row[0], keep[0], "吏部三铨", "100",
                            f"合并重复统称关系；{title}只保留一条实例边，宋初证据转挂保留边",
                        )
            assert len(relation_rows(conn, "吏部三铨", title, "统称与实例")) == 1

        # 审官院→知审官院事只保留五月二十日的精确编制关系。
        rows = relation_rows(conn, "审官院", "知审官院事", "编制隶属")
        if len(rows) > 1:
            keep = next(row for row in rows if row[2] == "北宋淳化四年五月二十日")
            for row in rows:
                if row[0] != keep[0]:
                    merge_relationship(
                        conn, row[0], keep[0], "知审官院事", "101",
                        "合并重复编制关系；保留知审官院事始置于五月二十日的精确关系",
                    )
        assert len(relation_rows(conn, "审官院", "知审官院事", "编制隶属")) == 1

        vague = conn.execute(
            "SELECT t.id FROM Timepoints t JOIN Entities e ON e.id=t.entity_id"
            " WHERE e.title='知审官院事' AND t.time='北宋淳化四年二月'"
        ).fetchone()
        if vague:
            exact = tp_id(conn, "知审官院事", "北宋淳化四年五月二十日")
            merge_timepoint(
                conn, vague[0], exact, "知审官院事", "101",
                "合并知院官二月泛化节点到五月二十日精确始置节点",
            )
        rechain(
            conn, "知审官院事", ["北宋淳化四年五月二十日"],
            "知审官院事", "101", "移除重复泛化节点后重建单节点链",
        )

        # 核实正确方向已经存在：磨勘京朝官院（来源）→审官院（后继）。
        correct = relation_rows(conn, "磨勘京朝官院", "审官院", "前后演变")
        reverse = relation_rows(conn, "审官院", "磨勘京朝官院", "前后演变")
        assert len(correct) == 1 and not reverse, "磨勘京朝官院→审官院方向或数量异常"

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
