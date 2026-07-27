#!/usr/bin/env python3
"""修复 #9“三相”首相实例误接到二相制复合官衔的问题。"""
import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t4.db"),
)

SOURCE_ENTRY = "三相"
SOURCE_PAGE = "86"
CITATION = "《宋代官制辞典》第86页“三相”条"
QUOTATION = (
    "《朝野杂记》甲集卷10《丞相》：“国初，循唐制，以三公至列曹侍郎、"
    "同平章事为宰相，首相带昭文馆大学士，亚相带监修国史，"
    "末相带集贤殿大学士。”"
)


def one(conn, sql, params=()):
    row = conn.execute(sql, params).fetchone()
    assert row, (sql, params)
    return row[0]


def main():
    with sqlite3.connect(DICT_DB) as dictionary:
        title, text, fields = dictionary.execute(
            "SELECT title,text,fields FROM chapter2t4 WHERE id=9"
        ).fetchone()
    source = "\n".join(
        [text or ""]
        + [
            str(value)
            for key, value in json.loads(fields or "{}").items()
            if not key.startswith("_")
        ]
    )
    assert title == SOURCE_ENTRY and QUOTATION in source

    conn = sqlite3.connect(ENTRY_DB)
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        conn.execute("BEGIN")
        group_tp = one(
            conn,
            "SELECT t.id FROM Timepoints t JOIN Entities e ON e.id=t.entity_id "
            "WHERE e.title='三相' AND e.type='官职' AND t.time='宋初'",
        )
        wrong_tp = one(
            conn,
            "SELECT t.id FROM Timepoints t JOIN Entities e ON e.id=t.entity_id "
            "WHERE e.title='同中书门下平章事、昭文馆大学士、监修国史' "
            "AND e.type='官职' AND t.time='宋前期'",
        )
        correct_tp = one(
            conn,
            "SELECT t.id FROM Timepoints t JOIN Entities e ON e.id=t.entity_id "
            "WHERE e.title='同中书门下平章事、昭文馆大学士' "
            "AND e.type='官职' AND t.time='宋前期'",
        )

        correct_rel = conn.execute(
            "SELECT id FROM Relationships WHERE subject_id=? AND object_id=? "
            "AND relation_type='统称与实例'",
            (group_tp, correct_tp),
        ).fetchone()
        wrong_rel = conn.execute(
            "SELECT id FROM Relationships WHERE subject_id=? AND object_id=? "
            "AND relation_type='统称与实例'",
            (group_tp, wrong_tp),
        ).fetchone()

        if correct_rel:
            rel_id = correct_rel[0]
            assert not wrong_rel, "正确、错误两条首相关系同时存在，需人工合并"
        elif wrong_rel:
            rel_id = wrong_rel[0]
            conn.execute(
                "UPDATE Relationships SET object_id=?, quotation=? WHERE id=?",
                (correct_tp, QUOTATION, rel_id),
            )
            conn.execute(
                "INSERT INTO BuildRecords "
                "(target_table,target_id,source_entry,source_page,decision) "
                "VALUES ('Relationships',?,?,?,?)",
                (
                    rel_id,
                    SOURCE_ENTRY,
                    SOURCE_PAGE,
                    f"修复三相首相实例：object_id {wrong_tp}->{correct_tp}；"
                    "三相制首相只带昭文馆大学士，监修国史属于亚相，"
                    "原关系误复用了二相制首相兼监修国史的复合官衔。",
                ),
            )
        else:
            cur = conn.execute(
                "INSERT INTO Relationships "
                "(subject_id,object_id,relation_type,quotation) VALUES (?,?,?,?)",
                (group_tp, correct_tp, "统称与实例", QUOTATION),
            )
            rel_id = cur.lastrowid
            conn.execute(
                "INSERT INTO BuildRecords "
                "(target_table,target_id,source_entry,source_page,decision) "
                "VALUES ('Relationships',?,?,?,?)",
                (
                    rel_id,
                    SOURCE_ENTRY,
                    SOURCE_PAGE,
                    "补建三相至首相实例；原文明载首相带昭文馆大学士。",
                ),
            )

        citation = conn.execute(
            "SELECT id FROM Citations WHERE target_table='Relationships' "
            "AND target_id=? AND citation=? AND quotation=?",
            (rel_id, CITATION, QUOTATION),
        ).fetchone()
        if not citation:
            cur = conn.execute(
                "INSERT INTO Citations "
                "(target_table,target_id,citation,quotation,note,conflict_flag) "
                "VALUES ('Relationships',?,?,?,?,0)",
                (rel_id, CITATION, QUOTATION, "三相制首相带昭文馆大学士"),
            )
            conn.execute(
                "INSERT INTO BuildRecords "
                "(target_table,target_id,source_entry,source_page,decision) "
                "VALUES ('Citations',?,?,?,?)",
                (
                    cur.lastrowid,
                    SOURCE_ENTRY,
                    SOURCE_PAGE,
                    "为修复后的首相实例关系补入三相条直接引文。",
                ),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
