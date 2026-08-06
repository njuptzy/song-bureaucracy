#!/usr/bin/env python3
"""提取 chapter11t12 第462-481条：医官二十二阶第四至二十一阶。"""

import importlib.util
import json
import os
import sqlite3
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DICT_DB = ROOT / "data/database/song_bureaucracy_dictionary_ch11t12.db"
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    str(ROOT / "data/database/song_bureaucracy_entries_ch1t12.db"),
)

base_spec = importlib.util.spec_from_file_location(
    "extract_11t12_442_461_helpers", HERE / "extract_11t12_442_461.py"
)
base = importlib.util.module_from_spec(base_spec)
assert base_spec.loader is not None
base_spec.loader.exec_module(base)


def load(entry_id):
    with sqlite3.connect(DICT_DB) as connection:
        row = connection.execute(
            "SELECT title,page,text,fields FROM chapter11t12 WHERE id=?", (entry_id,)
        ).fetchone()
    assert row, entry_id
    return {
        "title": row[0],
        "page": row[1],
        "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {entry_id: load(entry_id) for entry_id in range(462, 482)}


def configure(module):
    module.F = F
    module.ENTRY_DB = ENTRY_DB
    child = getattr(module, "base", None)
    if child is not None:
        configure(child)
    helpers = getattr(module, "helpers", None)
    if helpers is not None:
        helpers.F = F
        helpers.ENTRY_DB = ENTRY_DB
        helpers.NEW_SORT = {}


configure(base)

W = base.W
Q = base.Q
state = base.state
add_evolution = base.add_evolution
add_grade = base.add_grade
group_members = base.group_members


def sentence(entry_id, start_text):
    text = F[entry_id]["text"]
    start = text.index(start_text)
    return text[start:text.index("。", start) + 1]


EARLY_MEDICAL = {
    462: ("成全大夫", "军器库使", "第四", "正七品"),
    463: ("保和大夫", "西绫锦使", "第五", "正七品"),
    465: ("保安大夫", "榷易使", "第六", "正七品"),
    466: ("翰林良医", "翰林医官使", "第七", "正七品"),
    467: ("和安郎", None, "第八", "从七品"),
    468: ("成和郎", None, "第九", "从七品"),
    469: ("成安郎", None, "第十", "从七品"),
    470: ("成全郎", "军器库副使", "第十一", "从七品"),
    471: ("保和郎", "西绫锦副使", "第十二", "从七品"),
    473: ("保安郎", "榷易副使", "第十三", "从七品"),
    474: ("翰林医正", "翰林医官副使", "第十四", "从七品"),
}


def add_medical_properties(writer, entry_id, title, time, grade, order):
    add_grade(
        writer, entry_id, title, time, grade, Q(entry_id, grade),
        order, "医官阶",
    )
    household = Q(entry_id, "伎术官，理为官户")
    state(
        writer, entry_id, title, "宋代", "伎术官，理为官户",
        household, f"记录{title}的伎术官及官户属性。",
        category="医官阶", officer="医阶", sort_order=96000000,
    )


def extract_early_medical_ranks():
    for entry_id, (title, old_title, ordinal, grade) in EARLY_MEDICAL.items():
        writer = W(entry_id)
        rank_quote = Q(entry_id, f"为医官二十二阶之{ordinal}阶")
        group_members(
            writer, entry_id, "医官二十二阶",
            "北宋徽宗政和二年九月二十五日", "政和医官阶",
            (title,), rank_quote, 111201825, "医官阶",
        )
        origin = sentence(entry_id, "北宋政和二年九月二十五日")
        if old_title:
            add_evolution(
                writer, entry_id, old_title, title,
                "北宋徽宗政和二年九月二十五日", origin, 111201825,
                category="医官阶", old_event=f"阶名改为{title}",
                new_event=f"承接{old_title}医阶",
            )
        else:
            state(
                writer, entry_id, title,
                "北宋徽宗政和二年九月二十五日",
                f"创置，为医官二十二阶之{ordinal}阶", origin,
                f"建立{title}创置节点。", category="医官阶",
                officer="医阶", sort_order=111201825,
            )
        add_medical_properties(
            writer, entry_id, title,
            "北宋徽宗政和二年九月二十五日", grade, 111201825,
        )
        writer.commit()

    entry_id = 463
    writer = W(entry_id)
    rename = Q(entry_id, "宣和元年二月十二日废，改名为平和")
    add_evolution(
        writer, entry_id, "保和大夫", "平和大夫",
        "北宋徽宗宣和元年二月十二日", rename, 111902012,
        category="医官阶", old_event="废保和大夫名并改为平和",
        new_event="由保和大夫改名",
    )
    writer.commit()

    entry_id = 464
    writer = W(entry_id)
    identity = Q(entry_id, "医阶名。即保和大夫。宣和元年二月十二日改名")
    group_members(
        writer, entry_id, "医官二十二阶",
        "北宋徽宗宣和元年二月十二日", "承接保和大夫第五阶",
        ("平和大夫",), identity, 111902012, "医官阶",
    )
    add_evolution(
        writer, entry_id, "保和大夫", "平和大夫",
        "北宋徽宗宣和元年二月十二日", identity, 111902012,
        category="医官阶", old_event="改名为平和大夫",
        new_event="承接保和大夫医阶",
    )
    continuation = Q(entry_id, "其后迄南宋不废")
    state(
        writer, entry_id, "平和大夫", "南宋", "医阶名沿用不废",
        continuation, "记录平和大夫沿用至南宋。",
        category="医官阶", officer="医阶", sort_order=112700000,
    )
    add_medical_properties(
        writer, entry_id, "平和大夫", "宋代", "正七品", 96000000,
    )
    writer.commit()

    entry_id = 471
    writer = W(entry_id)
    rename = Q(entry_id, "宣和元年二月十二日废，易名为平和郎")
    add_evolution(
        writer, entry_id, "保和郎", "平和郎",
        "北宋徽宗宣和元年二月十二日", rename, 111902012,
        category="医官阶", old_event="废保和郎名并易为平和郎",
        new_event="由保和郎改名",
    )
    writer.commit()

    entry_id = 472
    writer = W(entry_id)
    identity = Q(entry_id, "医阶名。即保和郎。北宋宣和元年二月十二日，由保和郎改")
    group_members(
        writer, entry_id, "医官二十二阶",
        "北宋徽宗宣和元年二月十二日", "承接保和郎第十二阶",
        ("平和郎",), identity, 111902012, "医官阶",
    )
    add_evolution(
        writer, entry_id, "保和郎", "平和郎",
        "北宋徽宗宣和元年二月十二日", identity, 111902012,
        category="医官阶", old_event="改名为平和郎",
        new_event="承接保和郎医阶",
    )
    continuation = Q(entry_id, "迄南宋而不废")
    state(
        writer, entry_id, "平和郎", "南宋", "医阶名沿用不废",
        continuation, "记录平和郎沿用至南宋。",
        category="医官阶", officer="医阶", sort_order=112700000,
    )
    add_grade(
        writer, entry_id, "平和郎", "北宋徽宗宣和元年二月十二日",
        "从七品", Q(entry_id, "医阶名。即保和郎。"), 111902012,
        "医官阶",
    )
    writer.commit()

    entry_id = 474
    writer = W(entry_id)
    alias = F[entry_id]["fields"]["别名"]
    rename = "南宋诸《官品令》均易翰林医正为翰林医官"
    assert rename in alias
    group_members(
        writer, entry_id, "医官二十二阶", "南宋",
        "翰林医正易名翰林医官", ("翰林医官",), alias,
        112700000, "医官阶",
    )
    add_evolution(
        writer, entry_id, "翰林医正", "翰林医官", "南宋官品令",
        rename, 114000000, category="医官阶",
        old_event="官品令易名翰林医官",
        new_event="承接翰林医正医阶",
    )
    southern_grade = "和安至保安郎、翰林医官为从七品"
    assert southern_grade in alias
    add_grade(
        writer, entry_id, "翰林医官", "南宋庆元条法官品令",
        "从七品", southern_grade, 119500000, "医官阶",
    )
    writer.commit()


LATE_MEDICAL = {
    475: ("翰林医效", "第十五", "从七品"),
    476: ("翰林医痊", "第十六", "从七品"),
    477: ("翰林医愈", "第十七", "从八品"),
    478: ("翰林医证", "第十八", "从八品"),
    479: ("翰林医诊", "第十九", "从八品"),
    480: ("翰林医候", "第二十", "从八品"),
    481: ("翰林医学", "第二十一", "从九品"),
}


def extract_late_medical_ranks():
    for entry_id, (title, ordinal, grade) in LATE_MEDICAL.items():
        writer = W(entry_id)
        rank_quote = Q(entry_id, f"为医官二十二阶之{ordinal}阶")
        group_members(
            writer, entry_id, "医官二十二阶",
            "北宋徽宗政和三年八月二十五日", "政和新增医职八阶",
            (title,), rank_quote, 111308025, "医官阶",
        )
        origin = Q(entry_id, "北宋政和三年八月二十五日新增医职八阶之一")
        state(
            writer, entry_id, title, "北宋徽宗政和三年八月二十五日",
            f"新增，为医官二十二阶之{ordinal}阶", origin,
            f"建立{title}新增节点。", category="医官阶",
            officer="医阶", sort_order=111308025,
        )
        add_medical_properties(
            writer, entry_id, title,
            "北宋徽宗政和三年八月二十五日", grade, 111308025,
        )
        writer.commit()


def main():
    expected = [
        "成全大夫", "保和大夫", "平和大夫", "保安大夫", "翰林良医",
        "和安郎", "成和郎", "成安郎", "成全郎", "保和郎",
        "平和郎", "保安郎", "翰林医正", "翰林医效", "翰林医痊",
        "翰林医愈", "翰林医证", "翰林医诊", "翰林医候", "翰林医学",
    ]
    assert [F[i]["title"] for i in range(462, 482)] == expected
    extract_early_medical_ranks()
    extract_late_medical_ranks()


if __name__ == "__main__":
    main()
