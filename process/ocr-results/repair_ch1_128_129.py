#!/usr/bin/env python3
"""修复第一编第128条司赞吞并第129条彤史正文的切分错误。"""

import json
import os
import sqlite3


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_DIR = os.path.join(ROOT, "data", "database")

SIZAN_FIELDS = {
    "职源": "隋炀帝始置，掌礼仪赞相导引（《北史·后妃传》上）。宋朝于真宗朝设置。",
    "职掌": "掌礼仪、班序、设版位、赞拜之事。",
    "编制": "二人。下有僚佐典赞、掌赞、女史、彤史各二人。",
    "品阶": "正七品。在尚仪所属四司中居于末位（《宋会要·后妃》4之2）。",
}
SIZAN_TEXT = "宫人女官六尚所属二十四司之一。"

TONGSHI_FIELDS = {
    "职源": "唐朝内官尚仪局所属司赞，设有彤史，为正六品官（《六典》卷12《内官》）。彤史称谓之起，可溯至《诗经·邺风·静女》：“静女其变，贻我彤管。”据《毛传》云：“古者后、夫人，必有女史彤管之法：事无大小，记以成法；彤管以赤心正人也。”宋朝始见置于仁宗天圣《内命妇品职令》。",
    "职掌": "手书所领职事的文书记录。",
    "编制": "二人。",
    "官品": "正七品，位高于女史（《宋会要·后妃》4之2《内职》）。",
}
TONGSHI_TEXT = "宫人女官名，宋代仅见于内官尚仪所属司赞。"


def repair(db_name, table):
    path = os.path.join(DATABASE_DIR, db_name)
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            f"SELECT id,title FROM {table} WHERE title IN ('司赞','彤史') ORDER BY id"
        ).fetchall()
        assert len(rows) == 2 and [row[1] for row in rows] == ["司赞", "彤史"], rows
        conn.execute(
            f"UPDATE {table} SET fields=?, text=? WHERE title='司赞'",
            (json.dumps(SIZAN_FIELDS, ensure_ascii=False), SIZAN_TEXT),
        )
        conn.execute(
            f"UPDATE {table} SET fields=?, text=? WHERE title='彤史'",
            (json.dumps(TONGSHI_FIELDS, ensure_ascii=False), TONGSHI_TEXT),
        )
        conn.commit()


def main():
    repair("song_bureaucracy_dictionary_ch1.db", "chapter1")
    repair("song_bureaucracy_dictionary_ch1t7.db", "chapter1t7")


if __name__ == "__main__":
    main()
