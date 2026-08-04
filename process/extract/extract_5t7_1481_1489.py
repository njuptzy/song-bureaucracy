#!/usr/bin/env python3
"""提取 chapter5t7 第1481-1489条：千牛卫将军与环卫官各级统称。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1461_1480 as previous


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch5t7.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t7.db"),
)


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "select title,page,text,fields from chapter5t7 where id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0], "page": row[1], "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(1481, 1490)}
base = previous.base
legacy = previous.previous
base.F = F
base.ENTRY_DB = ENTRY_DB
previous.F = F
legacy.F = F

W = base.W
field = base.field
relation = base.relation
alias_note = base.alias_note
node = previous.node
pair_title = previous.pair_title
member_titles = previous.member_titles

FAMILIES = legacy.FAMILIES


TIME_HINTS = {
    **previous.TIME_HINTS,
    "唐朝": 650,
    "唐神龙元年": 705,
    "北宋初": 960,
    "宋代（具体年月未载）": 1000.2,
    "北宋元祐令": 1090,
    "南宋乾道二年": 1166,
}
previous.TIME_HINTS = TIME_HINTS
legacy.TIME_HINTS = TIME_HINTS


def time_key(time, row_id):
    if time in TIME_HINTS:
        return (TIME_HINTS[time], 0, row_id)
    match = re.search(r"(-?\d{3,4})", time or "")
    if match:
        return (int(match.group(1)), 0, row_id)
    return previous.time_key(time, row_id)


def rechain(w, eid, decision):
    rows = w.conn.execute(
        "select id,time from Timepoints where entity_id=?", (eid,)
    ).fetchall()
    ordered = [row[0] for row in sorted(rows, key=lambda row: time_key(row[1], row[0]))]
    for index, tid in enumerate(ordered):
        w.relink(
            tid, decision,
            prev_id=ordered[index - 1] if index else None,
            succ_id=ordered[index + 1] if index + 1 < len(ordered) else None,
        )


def finish(w, touched, decision):
    for eid in touched:
        rechain(w, eid, decision)
    w.commit()


def rank_group_entry(i, group_title, rank, time, alias_field=None,
                     grade_time=None, grade=None):
    quotation = F[i]["text"]
    w, touched = W(i), set()
    system = node(
        w, touched, i, "环卫官", "官职", time,
        "环卫官五等体系", quotation, "环卫官统称",
        f"复用环卫官{time}体系节点。", officer="环卫官统称",
    )
    group = node(
        w, touched, i, group_title, "官职", time,
        f"八卫左、右{rank}总称", quotation, "环卫官等级统称",
        f"复用{group_title}{time}统称节点。", officer=f"{rank}统称",
    )
    relation(
        w, i, system, group, "统称与实例", quotation,
        f"{group_title}是环卫官等级统称。",
    )
    for family in FAMILIES:
        grouped_title = pair_title(family, rank)
        grouped = node(
            w, touched, i, grouped_title, "官职", time,
            f"{group_title}所含{grouped_title}", quotation, "环卫官左右合称",
            f"复用{grouped_title}{time}节点。", officer=rank,
        )
        relation(
            w, i, group, grouped, "统称与实例", quotation,
            f"{grouped_title}是{group_title}的实例组。",
        )
    if alias_field:
        alias_note(w, i, group, field(i, alias_field), alias_field)
    if grade_time:
        node(
            w, touched, i, group_title, "官职", grade_time,
            f"元祐令定{group_title}{grade}", quotation, "环卫官等级统称",
            f"建立{group_title}{grade_time}官品节点。",
            officer=f"{rank}统称", grade=grade, update_event=True,
        )
    finish(w, touched, f"补足{group_title}正式词头、八个左右实例组及简称证据。")


def entry1481():
    legacy.pair_entry(
        1481, "千牛卫", "将军",
        (("唐神龙元年", "唐神龙元年始置"),), "北宋初", "从四品",
    )


def entry1482():
    legacy.pair_entry(
        1482, "千牛卫", "中郎将",
        (("唐朝", "唐朝始置"),), "南宋乾道二年",
    )


def entry1483():
    legacy.main_only_pair_entry(
        1483, "千牛卫", "郎将", grade="环卫官八十阶最低一阶"
    )


def entry1484():
    rank_group_entry(
        1484, "诸卫上将军", "上将军", "北宋初", "简称",
        grade_time="北宋元祐令", grade="从三品",
    )


def entry1485():
    rank_group_entry(1485, "诸卫大将军", "大将军", "北宋初", "简称")


def entry1486():
    rank_group_entry(1486, "诸卫将军", "将军", "北宋初", "简称与别名")


def entry1487():
    i, quotation = 1487, F[1487]["text"]
    time = "宋代（具体年月未载）"
    w, touched = W(i), set()
    system = node(
        w, touched, i, "环卫官", "官职", time,
        "宋代环卫官总称", quotation, "环卫官统称",
        "建立环卫官宋代无具体年月承载节点。", officer="环卫官统称",
    )
    umbrella = node(
        w, touched, i, "卫将军", "官职", time,
        "环卫官上将军、大将军、将军的泛称", quotation, "环卫官三等泛称",
        "建立卫将军正式泛称节点。", officer="卫将军泛称",
        update_event=True,
    )
    relation(
        w, i, system, umbrella, "统称与实例", quotation,
        "卫将军是环卫官前三等的泛称。",
    )
    for title, rank, grade in (
        ("诸卫上将军", "上将军", "从三品"),
        ("诸卫大将军", "大将军", "正四品"),
        ("诸卫将军", "将军", "从四品"),
    ):
        rank_tid = node(
            w, touched, i, title, "官职", time,
            f"卫将军所含{title}", quotation, "环卫官等级统称",
            f"建立或复用{title}宋代无具体年月节点。",
            officer=f"{rank}统称", grade=grade,
        )
        relation(
            w, i, umbrella, rank_tid, "统称与实例", quotation,
            f"{title}是卫将军所泛称的等级之一。",
        )
    finish(w, touched, "建立卫将军泛称与环卫官前三等的完整层级。")


def entry1488():
    rank_group_entry(
        1488, "环卫中郎将", "中郎将", "南宋乾道二年", "简称"
    )


def entry1489():
    rank_group_entry(1489, "环卫郎将", "郎将", "南宋乾道二年", "简称")


def main():
    expected = [
        "左、右千牛卫将军", "左、右千牛卫中郎将", "左、右千牛卫郎将",
        "诸卫上将军", "诸卫大将军", "诸卫将军", "卫将军",
        "环卫中郎将", "环卫郎将",
    ]
    assert [F[i]["title"] for i in range(1481, 1490)] == expected
    for i in range(1481, 1490):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
