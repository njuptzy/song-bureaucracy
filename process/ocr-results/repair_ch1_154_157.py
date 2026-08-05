#!/usr/bin/env python3
"""按原书第20-21页修复掌药吞并司饎、典饎、掌饎的切分与字形。"""

import json
import os
import sqlite3


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_DIR = os.path.join(ROOT, "data", "database")

ROWS = {
    154: (
        "掌药",
        {
            "职源": "隋炀帝时始置（《北史·后妃传》上）。宋朝于仁宗天圣《内命妇品职令》中始见置。",
            "职掌": "与典药同为司药官之佐贰。",
            "编制": "二人。",
            "品阶": "正八品，位次于司药（《宋会要·后妃》4之3）。",
        },
        "宫人女官名，二十四掌之一。",
    ),
    155: (
        "司饎",
        {
            "职源": "隋炀帝时始置，掌宫人伙食、柴炭（《北史·后妃传》上）。宋朝于真宗时设置（《宋会要·后妃》4之1）。",
            "职掌": "掌宫人膳食及柴火、木炭事。",
            "编制": "二人。其僚佐有典饎、掌饎各二人，女史四人。",
            "品阶": "正七品。在尚食四司中，居于末位（《宋会要·后妃》4之3）。",
        },
        "宫人女官六尚二十四司之一。",
    ),
    156: (
        "典饎",
        {
            "职源": "隋炀帝时始置（《北史·后妃传》上）。宋朝于仁宗天圣《内命妇品职令》中始见置（《宋会要·后妃》4之3）。",
            "职掌": "为司饎官之佐贰。",
            "编制": "二人。",
            "品阶": "具体官品失载，盖介于司饎（正七品）与掌饎（正八品）之间无疑（《宋会要·后妃》4之3，并参《六典》卷12《司饎、典饎、掌饎》）。",
        },
        "宫人女官名，二十四典之一。",
    ),
    157: (
        "掌饎",
        {
            "职源": "隋炀帝时始置（《北史·后妃传》上）。宋朝见于仁宗天圣《内命妇品职令》。",
            "职掌": "与典饎同为司饎官之佐贰。",
            "编制": "二人。",
            "品阶": "正八品，位次于典饎（《宋会要·后妃》4之3）。",
        },
        "宫人女官名，二十四掌之一。",
    ),
}

SIYAO_GRADE = "正七品。在尚食四司中，位次于司酝、高于司饎（《宋会要·后妃》4之3）。"
SHANGSHI_DUTY = "掌进御膳先尝。并管本尚所属四司：司膳、司酝、司药、司饎。"


def repair(db_name, table):
    path = os.path.join(DATABASE_DIR, db_name)
    with sqlite3.connect(path) as conn:
        current = conn.execute(
            f"SELECT id,title FROM {table} WHERE id BETWEEN 154 AND 157 ORDER BY id"
        ).fetchall()
        assert [row[0] for row in current] == [154, 155, 156, 157], current
        shangshi = conn.execute(f"SELECT fields FROM {table} WHERE id=145").fetchone()
        assert shangshi
        shangshi_fields = json.loads(shangshi[0])
        shangshi_fields["职掌"] = SHANGSHI_DUTY
        conn.execute(
            f"UPDATE {table} SET fields=? WHERE id=145",
            (json.dumps(shangshi_fields, ensure_ascii=False),),
        )
        siyao = conn.execute(f"SELECT fields FROM {table} WHERE id=152").fetchone()
        assert siyao
        siyao_fields = json.loads(siyao[0])
        siyao_fields["品阶"] = SIYAO_GRADE
        conn.execute(
            f"UPDATE {table} SET fields=? WHERE id=152",
            (json.dumps(siyao_fields, ensure_ascii=False),),
        )
        for row_id, (title, fields, text) in ROWS.items():
            conn.execute(
                f"UPDATE {table} SET title=?, fields=?, text=? WHERE id=?",
                (title, json.dumps(fields, ensure_ascii=False), text, row_id),
            )
        conn.commit()


def main():
    repair("song_bureaucracy_dictionary_ch1.db", "chapter1")
    repair("song_bureaucracy_dictionary_ch1t7.db", "chapter1t7")


if __name__ == "__main__":
    main()
