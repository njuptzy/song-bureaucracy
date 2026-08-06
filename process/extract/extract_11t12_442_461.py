#!/usr/bin/env python3
"""提取 chapter11t12 第442-461条：内侍阶后段、南宋八阶与医官阶开端。"""

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
    "extract_11t12_422_441_helpers", HERE / "extract_11t12_422_441.py"
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


F = {entry_id: load(entry_id) for entry_id in range(442, 462)}


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
relation = base.relation
add_evolution = base.add_evolution
add_grade = base.add_grade
group_members = base.group_members

typed_module = base
while not hasattr(typed_module, "typed_state"):
    typed_module = typed_module.base
typed_state = typed_module.typed_state


def sentence(entry_id, start_text):
    text = F[entry_id]["text"]
    start = text.index(start_text)
    return text[start:text.index("。", start) + 1]


LATE_INTERNAL = {
    442: ("黄门", ("入内内侍省内侍黄门", "内侍省内侍黄门")),
    443: ("祗候侍禁", ("入内祗候殿头",)),
    444: ("祗候殿直", ("祗候高品",)),
    445: ("祗候黄门内品", ("入内祗候高班内品", "祗候高班内品")),
    446: ("祗候内品", ("入内祗候内品", "祗候内品")),
    447: ("贴祗候内品", ("入内贴祗候内品", "贴祗候内品")),
}


def extract_late_internal_ranks():
    for entry_id, (title, old_titles) in LATE_INTERNAL.items():
        writer = W(entry_id)
        intro_start = "武阶名。" if entry_id == 447 else "阶官名。"
        intro = Q(entry_id, f"{intro_start}属政和内侍十一阶列。")
        group_members(
            writer, entry_id, "政和供奉官以下内侍阶",
            "北宋徽宗政和二年九月二十五日", "政和内侍十一阶",
            (title,), intro, 111201825, "政和内侍十一阶",
        )
        origin = sentence(entry_id, "北宋政和二年九月二十五日")
        for old_title in old_titles:
            if old_title == title:
                state(
                    writer, entry_id, title,
                    "北宋徽宗政和二年九月二十五日",
                    "同名旧称纳入政和内侍十一阶", origin,
                    f"{title}在内侍省沿用同名，记录制度归属变化而不建自环关系。",
                    category="政和内侍十一阶", officer="内侍阶官",
                    sort_order=111201825,
                )
                continue
            add_evolution(
                writer, entry_id, old_title, title,
                "北宋徽宗政和二年九月二十五日", origin, 111201825,
                category="政和内侍十一阶", old_event=f"阶名改为{title}",
                new_event=f"承接{old_title}阶名",
            )
        restore = sentence(entry_id, "靖康元年罢")
        for old_title in old_titles:
            if old_title == title:
                state(
                    writer, entry_id, title, "北宋钦宗靖康元年",
                    "罢政和阶制并复同名旧称", restore,
                    f"记录{title}在靖康复旧时同名恢复，不建自环关系。",
                    category="内侍阶官", officer="内侍阶官",
                    sort_order=112600000,
                )
                continue
            add_evolution(
                writer, entry_id, title, old_title, "北宋钦宗靖康元年",
                restore, 112600000, category="政和内侍十一阶",
                old_event=f"罢新名并复{old_title}旧称",
                new_event=f"复用{old_title}旧称",
            )
        writer.commit()


SOUTHERN_MEMBERS = (
    "内常侍", "东头供奉官", "西头供奉官", "殿头",
    "高品", "高班", "黄门", "内品",
)


def institution_evolution(writer, entry_id, old_title, new_title, time, quote, order):
    _, old_tp = typed_state(
        writer, entry_id, old_title, "机构", time, f"并入{new_title}", quote,
        f"据原文建立或复用{old_title}并省节点。",
        category="机构沿革", officer=None, sort_order=order,
    )
    _, new_tp = typed_state(
        writer, entry_id, new_title, "机构", time, f"并入后承接{old_title}", quote,
        f"据原文建立或复用{new_title}承接节点。",
        category="机构沿革", officer=None, sort_order=order,
    )
    relation(
        writer, entry_id, old_tp, new_tp, "前后演变", quote,
        f"原文明示{old_title}在{time}并入{new_title}。",
    )


def extract_southern_internal_ranks():
    entry_id = 448
    writer = W(entry_id)
    reform = Q(
        entry_id,
        "北宋政和二年九月改内侍官名，定供奉官以下十一阶迁转阶官。",
    )
    state(
        writer, entry_id, "南宋内侍阶官", "北宋徽宗政和二年九月",
        "政和改定供奉官以下十一阶", reform,
        "记录南宋内侍阶官制度的政和前置阶段。",
        category="内侍阶官", officer="职官总名", sort_order=111209000,
    )
    restore = Q(entry_id, "靖康元年罢，仍复元丰八年入内、内侍二省内常侍以下官称")
    state(
        writer, entry_id, "南宋内侍阶官", "北宋钦宗靖康元年",
        "罢政和新名并恢复元丰旧称", restore,
        "记录南宋内侍八阶形成前的复旧节点。",
        category="南宋内侍八阶", officer="职官总名", sort_order=112600000,
    )
    merger = Q(entry_id, "绍兴三十年九月，内侍省并入入内内侍省")
    institution_evolution(
        writer, entry_id, "内侍省", "入内内侍省",
        "南宋高宗绍兴三十年九月", merger, 116009000,
    )
    group_quote = Q(
        entry_id,
        "南宋内侍常调八阶为：内常侍（正八品），东头供奉官、西头供奉官（从八品），殿头、高品（正九品），高班、黄门、内品（从九品）",
    )
    group_members(
        writer, entry_id, "南宋内侍阶官", "南宋", "内侍常调八阶",
        SOUTHERN_MEMBERS, group_quote, 112700000, "南宋内侍八阶",
    )
    for title, grade in (
        ("内常侍", "正八品"), ("东头供奉官", "从八品"),
        ("西头供奉官", "从八品"), ("殿头", "正九品"),
        ("高品", "正九品"), ("高班", "从九品"),
        ("黄门", "从九品"), ("内品", "从九品"),
    ):
        add_grade(
            writer, entry_id, title, "南宋", grade, group_quote,
            112700000, "南宋内侍八阶",
        )
    writer.commit()

    specs = {
        449: ("内常侍", None, "正八品", "为南宋内侍常调八阶之一"),
        450: ("东头供奉官", "供奉官", "从八品", "为南宋内侍常调八阶第二阶"),
        451: ("西头供奉官", "左侍禁", "从八品", "为南宋内侍常调八阶第三阶"),
        452: ("殿头", "右侍禁", "正九品", "为南宋内侍常调八阶之第四阶"),
        453: ("高品", "左班殿直", "正九品", "为南宋内侍常调八阶之第五阶"),
        454: ("高班", "右班殿直", "从九品", "为南宋内侍常调八阶之第六阶"),
        455: ("黄门", None, "从九品", "为南宋内侍阶官第七阶"),
        456: ("内品", None, "从九品", "内品被列为南宋内侍常调八阶之第八阶"),
    }
    for entry_id, (title, reform_title, grade, rank_needle) in specs.items():
        writer = W(entry_id)
        intro = Q(entry_id, "内侍官称、阶官名。属南宋内侍八阶列。")
        group_members(
            writer, entry_id, "南宋内侍阶官", "南宋", "内侍常调八阶",
            (title,), intro, 112700000, "南宋内侍八阶",
        )
        yuanfeng = sentence(entry_id, "北宋元丰八年")
        state(
            writer, entry_id, title, "北宋神宗元丰八年",
            "列入两省内侍诸级", yuanfeng,
            f"记录{title}元丰八年的内侍诸级序位。",
            category="元丰内侍诸级", officer="内侍阶官", sort_order=108500000,
        )
        reform = sentence(entry_id, "政和二年九月")
        if reform_title:
            add_evolution(
                writer, entry_id, title, reform_title,
                "北宋徽宗政和二年九月", reform, 111209000,
                category="政和内侍十一阶", old_event=f"阶名改为{reform_title}",
                new_event=f"承接{title}阶名",
            )
            restore_quote = sentence(entry_id, "靖康元年")
            add_evolution(
                writer, entry_id, reform_title, title, "北宋钦宗靖康元年",
                restore_quote, 112600000, category="南宋内侍八阶",
                old_event=f"罢政和新名并复{title}", new_event=f"恢复{title}旧称",
            )
        else:
            state(
                writer, entry_id, title, "北宋徽宗政和二年九月",
                "未改名或未纳入供奉官以下十一阶", reform,
                f"记录{title}在政和内侍改名中的处置。",
                category="政和内侍十一阶", officer="内侍阶官",
                sort_order=111209000,
            )
        rank_quote = Q(entry_id, rank_needle)
        state(
            writer, entry_id, title, "南宋", rank_needle,
            rank_quote, f"记录{title}在南宋内侍八阶中的序位。",
            category="南宋内侍八阶", officer="内侍阶官", sort_order=112700000,
        )
        add_grade(
            writer, entry_id, title, "南宋", grade,
            Q(entry_id, grade), 112700000, "南宋内侍八阶",
        )
        if entry_id == 449:
            uncommon = Q(entry_id, "然不常除")
            state(
                writer, entry_id, title, "南宋", "不常除授", uncommon,
                "记录内常侍在南宋不常除授。", category="南宋内侍八阶",
                officer="内侍阶官", sort_order=112700000,
            )
        writer.commit()


def extract_technical_and_medical_ranks():
    entry_id = 457
    writer = W(entry_id)
    tang = Q(entry_id, "唐制，伎术官由本官司确定与选授、迁转")
    state(
        writer, entry_id, "伎术官阶", "唐代", "已有伎术官选授迁转制度",
        tang, "建立伎术官阶的前代职源节点。",
        category="前代职源", officer="职官总名", sort_order=70000000,
    )
    song = Q(entry_id, "宋沿唐制")
    state(
        writer, entry_id, "伎术官阶", "宋代", "沿唐制另立迁转之途",
        song, "建立宋代伎术官阶制度节点。",
        category="伎术官阶", officer="职官总名", sort_order=96000000,
    )
    separate = Q(entry_id, "伎术官地位卑下，不入文、武官迁转阶列，另立迁转之途")
    state(
        writer, entry_id, "伎术官阶", "宋代",
        "不入文武官迁转阶列，另立迁转之途", separate,
        "记录伎术官阶与文武迁转序列相互独立。",
        category="伎术官阶", officer="职官总名", sort_order=96000000,
    )
    early = Q(entry_id, "北宋前期，东班诸司使翰林使、副使以下十九阶，多用作伎术官官阶")
    state(
        writer, entry_id, "伎术官阶", "北宋前期",
        "东班翰林使、副使以下十九阶多用作伎术官阶", early,
        "记录北宋前期伎术官借用东班阶的制度。",
        category="伎术官阶", officer="职官总名", sort_order=96000000,
    )
    reform = Q(
        entry_id,
        "政和二年九月二十五日，定医职阶时，部分东班诸司正使、副使阶易为大夫、郎",
    )
    state(
        writer, entry_id, "伎术官阶", "北宋徽宗政和二年九月二十五日",
        "定医职阶并改易部分东班使副阶名", reform,
        "记录政和医职阶改制对伎术官阶的影响。",
        category="伎术官阶", officer="职官总名", sort_order=111201825,
    )
    writer.commit()

    entry_id = 458
    writer = W(entry_id)
    first = Q(
        entry_id,
        "北宋政和二年九月二十五日，改定医职自和安大夫至翰林良医七阶、和安郎至翰林医正（医官）共十四阶",
    )
    state(
        writer, entry_id, "医官二十二阶", "北宋徽宗政和二年九月二十五日",
        "改定医职十四阶", first,
        "建立医官阶政和二年首批十四阶节点。",
        category="医官阶", officer="职官总名", sort_order=111201825,
    )
    additional = Q(
        entry_id,
        "政和三年八月二十五日，立定翰林医效、翰林医痊、翰林医愈、翰林医证、翰林医诊、翰林医候、翰林医学、翰林祗候八阶",
    )
    state(
        writer, entry_id, "医官二十二阶", "北宋徽宗政和三年八月二十五日",
        "增定八阶，合为二十二阶", additional,
        "记录医官二十二阶完整形成。",
        category="医官阶", officer="职官总名", sort_order=111308025,
    )
    technical = Q(
        entry_id,
        "宋制，伎术官非战功及随龙人不许换武职，医官阶迁转至和安大夫止",
    )
    group_members(
        writer, entry_id, "伎术官阶", "宋代", "另立迁转的伎术官阶",
        ("医官二十二阶",), technical, 96000000, "伎术官阶",
    )
    limit = Q(entry_id, "医官阶迁转至和安大夫止，不得转遥郡刺史以上")
    state(
        writer, entry_id, "医官二十二阶", "宋代",
        "迁转至和安大夫止，不得转遥郡刺史以上", limit,
        "记录医官阶迁转止法。", category="医官阶",
        officer="职官总名", sort_order=96000000,
    )
    official_households = Q(
        entry_id, "宣和四年六月十三日，诏自翰林医学以上医官通理为官户"
    )
    state(
        writer, entry_id, "医官二十二阶", "北宋徽宗宣和四年六月十三日",
        "翰林医学以上通理为官户", official_households,
        "记录医官理为官户的制度节点。",
        category="医官阶", officer="职官总名", sort_order=112206013,
    )
    writer.commit()

    for entry_id, title, ordinal in (
        (459, "和安大夫", "第一"),
        (460, "成和大夫", "第二"),
        (461, "成安大夫", "第三"),
    ):
        writer = W(entry_id)
        intro = Q(entry_id, "医阶名。")
        rank_quote = Q(entry_id, f"为医官二十二阶{'中' if entry_id != 461 else ''}之{ordinal}阶")
        group_members(
            writer, entry_id, "医官二十二阶",
            "北宋徽宗政和二年九月二十五日", "政和医官阶",
            (title,), rank_quote, 111201825, "医官阶",
        )
        creation = Q(entry_id, "北宋政和二年九月二十五日创置")
        state(
            writer, entry_id, title, "北宋徽宗政和二年九月二十五日",
            f"创置，为医官二十二阶之{ordinal}阶", creation,
            f"建立{title}创置节点。", category="医官阶",
            officer="医阶", sort_order=111201825,
        )
        add_grade(
            writer, entry_id, title, "北宋徽宗政和二年九月二十五日",
            "从六品", Q(entry_id, "从六品"), 111201825, "医官阶",
        )
        household = Q(entry_id, "伎术官，理为官户")
        state(
            writer, entry_id, title, "宋代", "伎术官，理为官户",
            household, f"记录{title}的伎术官及官户属性。",
            category="医官阶", officer="医阶", sort_order=96000000,
        )
        if entry_id == 459:
            stop = Q(entry_id, "医官迁转至本阶止")
            state(
                writer, entry_id, title, "宋代", "医官迁转至本阶止",
                stop, "记录和安大夫为医官迁转止阶。",
                category="医官阶", officer="医阶", sort_order=96000000,
            )
        writer.commit()


def main():
    expected = [
        "黄门", "祗候侍禁", "祗候殿直", "祗候黄门内品", "祗候内品",
        "贴祗候内品", "南宋内侍阶官", "内常侍", "东头供奉官",
        "西头供奉官", "殿头", "高品", "高班", "黄门", "内品",
        "伎术官阶", "医官二十二阶", "和安大夫", "成和大夫", "成安大夫",
    ]
    assert [F[i]["title"] for i in range(442, 462)] == expected
    extract_late_internal_ranks()
    extract_southern_internal_ranks()
    extract_technical_and_medical_ranks()


if __name__ == "__main__":
    main()
