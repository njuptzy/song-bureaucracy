#!/usr/bin/env python3
"""按原书第21-22页修复司舆/典舆及司灯跨页切分。"""

import json
import os
import sqlite3


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_DIR = os.path.join(ROOT, "data", "database")

SIYU_FIELDS = {
    "职源": "隋炀帝时始置（《北史·后妃传》上）。宋朝于真宗时设置（《宋会要·后妃》4之1）。",
    "职掌": "掌舆辇、伞扇，执持羽仪。",
    "编制": "二人。其僚佐有典舆、掌舆、女史各二人。",
    "品阶": "正七品。位次于司设、高于司苑（《宋会要·后妃》4之3）。",
}
SIYU_TEXT = "宫人女官六尚二十四司之一。"

DIANYU_FIELDS = {
    "职源": "隋炀帝时始置（《北史·后妃传》上）。宋朝于仁宗天圣《内命妇品职令》中始见置。",
    "职掌": "为司舆官之佐贰。",
    "编制": "二人。",
    "品阶": "具体官品失载，盖介于司舆（正七品）与掌舆（正八品）之间无疑（《宋会要·后妃》4之3，并参《六典》卷12《司舆、典舆、掌舆》）。",
}
DIANYU_TEXT = "宫人女官名，二十四典之一。"

SIDENG_FIELDS = {
    "职源": "隋炀帝时始置（《北史·后妃传》上）。宋朝于仁宗时见置（《宋会要·后妃》4之3）。",
    "职掌": "掌灯油、火烛之事。",
    "编制": "二人。其僚佐有典灯、掌灯、女史各二人。",
    "品阶": "正七品。在尚寝所属四司中，居于末位（《宋会要·后妃》4之3）。",
}
SIDENG_TEXT = "宫人女官六尚二十四司之一。"


def repair(db_name, table):
    path = os.path.join(DATABASE_DIR, db_name)
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            f"SELECT id,title FROM {table} WHERE id IN (162,163,168) ORDER BY id"
        ).fetchall()
        assert [row[0] for row in rows] == [162, 163, 168], rows
        conn.execute(
            f"UPDATE {table} SET title='司舆',fields=?,text=? WHERE id=162",
            (json.dumps(SIYU_FIELDS, ensure_ascii=False), SIYU_TEXT),
        )
        conn.execute(
            f"UPDATE {table} SET title='典舆',fields=?,text=? WHERE id=163",
            (json.dumps(DIANYU_FIELDS, ensure_ascii=False), DIANYU_TEXT),
        )
        conn.execute(
            f"UPDATE {table} SET title='司灯',fields=?,text=? WHERE id=168",
            (json.dumps(SIDENG_FIELDS, ensure_ascii=False), SIDENG_TEXT),
        )
        extra = conn.execute(
            f"SELECT title,fields FROM {table} WHERE id=169"
        ).fetchone()
        if extra:
            flags = json.loads(extra[1] or "{}")
            assert extra[0] == "掌灯" and flags.get("_not_in_catalog"), extra
            conn.execute(f"DELETE FROM {table} WHERE id=169")
        conn.commit()


def main():
    repair("song_bureaucracy_dictionary_ch1.db", "chapter1")
    repair("song_bureaucracy_dictionary_ch1t7.db", "chapter1t7")


if __name__ == "__main__":
    main()
