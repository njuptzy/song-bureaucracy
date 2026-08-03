#!/usr/bin/env python3
"""删除歧义的“尚书吏部”过渡实体，补齐尚书省吏部的明示隶属关系。"""

import json
import os
import sqlite3


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t7.db"),
)


def dictionary_entry(conn, entry_id):
    row = conn.execute(
        "select title,page,text,fields from chapter2t4 where id=?", (entry_id,)
    ).fetchone()
    assert row, entry_id
    return row[0], str(row[1]), row[2] or "", json.loads(row[3] or "{}")


def add_build(conn, table, target_id, source_entry, page, decision):
    conn.execute(
        "insert into BuildRecords"
        " (target_table,target_id,source_entry,source_page,decision)"
        " values (?,?,?,?,?)",
        (table, target_id, source_entry, page, decision),
    )


def ensure_build(conn, table, target_id, source_entry, page, decision):
    row = conn.execute(
        "select 1 from BuildRecords where target_table=? and target_id=?"
        " and source_entry=? and source_page=? and decision=?",
        (table, target_id, source_entry, page, decision),
    ).fetchone()
    if not row:
        add_build(conn, table, target_id, source_entry, page, decision)


def add_citation(conn, table, target_id, citation, quotation, source_entry,
                 page, decision, note=None):
    row = conn.execute(
        "select id from Citations where target_table=? and target_id=?"
        " and citation=? and quotation=?",
        (table, target_id, citation, quotation),
    ).fetchone()
    if row:
        return row[0]
    cid = conn.execute(
        "insert into Citations"
        " (target_table,target_id,citation,quotation,note,conflict_flag)"
        " values (?,?,?,?,?,0)",
        (table, target_id, citation, quotation, note),
    ).lastrowid
    add_build(conn, "Citations", cid, source_entry, page, decision)
    return cid


def ensure_relationship(conn, subject_id, object_id, relation_type, quotation,
                        source_entry, page, decision, citation, note=None):
    row = conn.execute(
        "select id from Relationships where subject_id=? and object_id=?"
        " and relation_type=?",
        (subject_id, object_id, relation_type),
    ).fetchone()
    if row:
        rid = row[0]
    else:
        rid = conn.execute(
            "insert into Relationships"
            " (subject_id,object_id,relation_type,quotation) values (?,?,?,?)",
            (subject_id, object_id, relation_type, quotation),
        ).lastrowid
        add_build(conn, "Relationships", rid, source_entry, page, decision)
    add_citation(
        conn, "Relationships", rid, citation, quotation, source_entry, page,
        f"为关系保存逐字辞典证据：{decision}", note,
    )
    return rid


def delete_ambiguous_entity(conn):
    row = conn.execute(
        "select id from Entities where title='尚书吏部' and type='机构'"
    ).fetchone()
    if not row:
        return False
    eid = row[0]
    tids = [
        r[0] for r in conn.execute(
            "select id from Timepoints where entity_id=?", (eid,)
        )
    ]
    placeholders = ",".join("?" for _ in tids)
    rel_ids = []
    if tids:
        rel_ids = [
            r[0] for r in conn.execute(
                f"select id from Relationships where subject_id in ({placeholders})"
                f" or object_id in ({placeholders})",
                tids + tids,
            )
        ]

    citation_ids = []
    for table, ids in (("Timepoints", tids), ("Relationships", rel_ids)):
        if not ids:
            continue
        ph = ",".join("?" for _ in ids)
        citation_ids.extend(
            r[0] for r in conn.execute(
                f"select id from Citations where target_table=?"
                f" and target_id in ({ph})",
                (table, *ids),
            )
        )

    if citation_ids:
        ph = ",".join("?" for _ in citation_ids)
        conn.execute(
            f"delete from BuildRecords where target_table='Citations'"
            f" and target_id in ({ph})", citation_ids,
        )
        conn.execute(f"delete from Citations where id in ({ph})", citation_ids)
    if rel_ids:
        ph = ",".join("?" for _ in rel_ids)
        conn.execute(
            f"delete from BuildRecords where target_table='Relationships'"
            f" and target_id in ({ph})", rel_ids,
        )
        conn.execute(f"delete from Relationships where id in ({ph})", rel_ids)
    if tids:
        ph = ",".join("?" for _ in tids)
        conn.execute(
            f"delete from BuildRecords where target_table='Timepoints'"
            f" and target_id in ({ph})", tids,
        )
        conn.execute(f"delete from NormalizedTimes where timepoint_id in ({ph})", tids)
        conn.execute(f"delete from Timepoints where id in ({ph})", tids)
    conn.execute(
        "delete from BuildRecords where target_table='Entities' and target_id=?",
        (eid,),
    )
    conn.execute("delete from Entities where id=?", (eid,))
    return True


def main():
    dictionary = sqlite3.connect(DICT_DB)
    _, page102, _, fields102 = dictionary_entry(dictionary, 102)
    title974, page974, _, fields974 = dictionary_entry(dictionary, 974)
    evolution_quote = fields102["职源与沿革"]
    hierarchy_quote = fields974["职掌"]
    assert "元丰三年八月十四日，改名为尚书吏部" in evolution_quote
    assert "五年五月，元丰新制改为吏部侍郎左选" in evolution_quote
    for needle in ("流内铨虽名义上归隶吏部", "兼领南曹、格式司、甲库"):
        assert needle in hierarchy_quote

    conn = sqlite3.connect(ENTRY_DB)
    conn.execute("pragma foreign_keys=on")
    try:
        conn.execute("begin immediate")
        removed = delete_ambiguous_entity(conn)

        source_tp = conn.execute(
            "select t.id from Timepoints t join Entities e on e.id=t.entity_id"
            " where e.title='吏部流内铨' and e.type='机构'"
            " and t.time='北宋元丰三年八月十四日'"
        ).fetchone()
        target_tp = conn.execute(
            "select t.id from Timepoints t join Entities e on e.id=t.entity_id"
            " where e.title='吏部侍郎左选' and e.type='机构'"
            " and t.time='北宋元丰五年五月'"
        ).fetchone()
        assert source_tp and target_tp
        ensure_relationship(
            conn, source_tp[0], target_tp[0], "前后演变", evolution_quote,
            "吏部流内铨", page102,
            "删除歧义过渡实体后，依据完整沿革将吏部流内铨直接连接至吏部侍郎左选；"
            "元丰三年改称信息保留在来源时间点事件中。",
            f"《宋代官制辞典》第{page102}页“吏部流内铨”条（职源与沿革字段）",
            note="尚书吏部为1080至1082年的过渡称名，不另立同名实体",
        )

        parent = conn.execute(
            "select t.id from Timepoints t join Entities e on e.id=t.entity_id"
            " where e.title='尚书省吏部' and e.type='机构' and t.time='宋前期'"
        ).fetchone()
        assert parent
        children = (
            ("吏部流内铨", "北宋建隆三年", "名义归隶尚书省吏部"),
            ("吏部南曹", "北宋", "宋前期由尚书省吏部兼领"),
            ("吏部格式司", "宋代", "宋前期由尚书省吏部兼领"),
            ("吏部甲库", "宋代", "宋前期由尚书省吏部兼领"),
        )
        citation = f"《宋代官制辞典》第{page974}页“{title974}”条（职掌字段）"
        for child_title, child_time, fact in children:
            child = conn.execute(
                "select t.id from Timepoints t join Entities e on e.id=t.entity_id"
                " where e.title=? and e.type='机构' and t.time=?",
                (child_title, child_time),
            ).fetchone()
            assert child, (child_title, child_time)
            ensure_relationship(
                conn, parent[0], child[0], "上下级机构", hierarchy_quote,
                title974, page974, fact, citation,
            )

        ensure_build(
            conn, "Timepoints", source_tp[0], "吏部流内铨", page102,
            "删除独立‘尚书吏部’实体后，保留本节点‘改名尚书吏部’事件，"
            "承载元丰三年过渡称名证据。",
        )
        conn.commit()
        print("removed_ambiguous_entity", int(removed))
        print("direct_evolution", source_tp[0], target_tp[0])
        print("added_hierarchy", len(children))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
        dictionary.close()


if __name__ == "__main__":
    main()
