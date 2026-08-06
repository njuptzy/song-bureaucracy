#!/usr/bin/env python3
"""提取 chapter11t12 第402-421条：政和新武阶第三十七阶至校尉统称。"""

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
    "extract_11t12_382_401_helpers", HERE / "extract_11t12_382_401.py"
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


F = {entry_id: load(entry_id) for entry_id in range(402, 422)}
base.F = F
base.base.F = F
base.base.base.F = F
base.base.base.helpers.F = F
base.ENTRY_DB = ENTRY_DB
base.base.ENTRY_DB = ENTRY_DB
base.base.base.ENTRY_DB = ENTRY_DB
base.base.base.helpers.ENTRY_DB = ENTRY_DB
base.base.base.helpers.NEW_SORT = {}

W = base.W
Q = base.Q
state = base.state
relation = base.base.relation
add_evolution = base.add_evolution
add_grade = base.add_grade
group_members = base.group_members


CN_ORDINAL = {
    37: "三十七", 38: "三十八", 39: "三十九", 40: "四十",
    41: "四十一", 42: "四十二", 43: "四十三", 44: "四十四",
    45: "四十五", 46: "四十六", 47: "四十七", 48: "四十八",
    49: "四十九", 50: "五十", 51: "五十一", 52: "五十二",
}


REGULAR_LANG = {
    402: ("武显郎", ("左藏库副使", "东作坊副使", "西作坊副使"), 37),
    403: ("武节郎", ("庄宅副使", "六宅副使", "文思副使"), 38),
    404: ("武略郎", ("内园副使", "洛苑副使", "如京副使", "崇仪副使"), 39),
    405: ("武经郎", ("西京左藏库副使",), 40),
    406: ("武义郎", ("西京作坊副使", "东染院副使", "西染院副使", "礼宾副使"), 41),
    407: ("武翼郎", ("供备库副使",), 42),
}


def sentence(entry_id, start_text):
    text = F[entry_id]["text"]
    start = text.index(start_text)
    return text[start:text.index("。", start) + 1]


def rank_state(writer, entry_id, title, ordinal, grade, category):
    ordinal_text = CN_ORDINAL[ordinal]
    rank_quote = Q(
        entry_id, f"绍兴厘定入品武阶五十二阶之第{ordinal_text}阶"
    )
    state(
        writer, entry_id, title, "南宋高宗绍兴厘定",
        f"列入品武阶五十二阶之第{ordinal_text}阶", rank_quote,
        f"记录{title}绍兴厘定序位。", category="绍兴武阶",
        officer="武阶", sort_order=113100000,
    )
    add_grade(
        writer, entry_id, title, "南宋高宗绍兴厘定", grade,
        Q(entry_id, grade), 113100000, category,
    )


def extract_regular_lang():
    for entry_id, (title, old_titles, ordinal) in REGULAR_LANG.items():
        writer = W(entry_id)
        intro = Q(entry_id, "武阶名。属诸司副使八阶列。")
        group_members(
            writer, entry_id, "诸司副使",
            "北宋徽宗政和二年九月二十五日",
            "改武选官名后合并为八阶郎", (title,), intro,
            111201825, "诸司副使武阶",
        )
        origin = sentence(entry_id, "北宋政和二年九月二十五日")
        for old_title in old_titles:
            add_evolution(
                writer, entry_id, old_title, title,
                "北宋徽宗政和二年九月二十五日", origin, 111201825,
                category="诸司副使武阶", old_event=f"阶名改为{title}",
                new_event=f"承接{old_title}武阶",
            )
        rank_state(writer, entry_id, title, ordinal, "从七品", "诸司副使武阶")
        if entry_id == 407:
            cycle = Q(entry_id, "自武翼郎，按磨勘常调，每五年转一阶，至武功大夫，有止法")
            state(
                writer, entry_id, title, "南宋", "磨勘常调每五年一转，至武功大夫止",
                cycle, "记录武翼郎以上武阶的磨勘周期与止法。",
                category="武阶迁转", officer="武阶", sort_order=112700000,
            )
        writer.commit()


LATER_RANKS = {
    408: ("训武郎", "大使臣", 43, "正八品"),
    410: ("修武郎", "大使臣", 44, "正八品"),
    411: ("从义郎", "小使臣", 45, "从八品"),
    412: ("秉义郎", "小使臣", 46, "从八品"),
    413: ("忠训郎", "小使臣", 47, "正九品"),
    414: ("忠翊郎", "小使臣", 48, "正九品"),
    415: ("成忠郎", "小使臣", 49, "正九品"),
    416: ("保义郎", "小使臣", 50, "正九品"),
    417: ("承节郎", "小使臣", 51, "从九品"),
    418: ("承信郎", "小使臣", 52, "从九品"),
}


ORIGINS = {
    410: ("内殿崇班",), 411: ("东头供奉官",), 412: ("西头供奉官",),
    413: ("左侍禁",), 414: ("右侍禁",), 415: ("左班殿直",),
    416: ("右班殿直",), 417: ("三班奉职",), 418: ("三班借职",),
}


def extract_dashi_xiaoshi():
    entry_id = 408
    writer = W(entry_id)
    intro = Q(entry_id, "武阶名。属大使臣二阶列。")
    group_members(
        writer, entry_id, "大使臣", "南宋", "大使臣二阶",
        ("训武郎",), intro, 112700000, "大使臣武阶",
    )
    reform = Q(entry_id, "北宋政和二年九月二十五日，由内殿承制改名敦武郎")
    add_evolution(
        writer, entry_id, "内殿承制", "敦武郎",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="大使臣武阶", old_event="阶名改为敦武郎",
        new_event="承接内殿承制武阶",
    )
    taboo = Q(entry_id, "南宋光宗朝避赵惇讳，改敦武郎为训武郎")
    add_evolution(
        writer, entry_id, "敦武郎", "训武郎", "南宋光宗朝",
        taboo, 119000000, category="大使臣武阶",
        old_event="避赵惇讳改为训武郎", new_event="由敦武郎避讳改名",
    )
    rank_state(writer, entry_id, "训武郎", 43, "正八品", "大使臣武阶")
    promotion = Q(entry_id, "其磨勘常调转武翼郎")
    add_evolution(
        writer, entry_id, "训武郎", "武翼郎", "南宋磨勘常调制度",
        promotion, 114000000, category="武阶迁转",
        old_event="磨勘常调转武翼郎", new_event="由训武郎磨勘迁转",
    )
    writer.commit()

    entry_id = 409
    writer = W(entry_id)
    reform = Q(entry_id, "北宋政和二年九月二十五日，由内殿承制改名")
    add_evolution(
        writer, entry_id, "内殿承制", "敦武郎",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="大使臣武阶", old_event="阶名改为敦武郎",
        new_event="承接内殿承制武阶",
    )
    taboo = Q(entry_id, "南宋光宗朝改为训武郎")
    add_evolution(
        writer, entry_id, "敦武郎", "训武郎", "南宋光宗朝",
        taboo, 119000000, category="大使臣武阶",
        old_event="改为训武郎", new_event="由敦武郎改名",
    )
    writer.commit()

    for entry_id, (title, group_title, ordinal, grade) in LATER_RANKS.items():
        if entry_id == 408:
            continue
        writer = W(entry_id)
        intro = Q(entry_id, f"武阶名。属{group_title}二阶列。") if entry_id == 410 else Q(
            entry_id, f"武阶名。属{group_title}八阶列。"
        )
        group_members(
            writer, entry_id, group_title,
            "北宋徽宗政和二年九月二十五日",
            f"改武选官名后的{group_title}阶列", (title,), intro,
            111201825, f"{group_title}武阶",
        )
        origin = sentence(entry_id, "北宋政和二年九月二十五日")
        for old_title in ORIGINS[entry_id]:
            add_evolution(
                writer, entry_id, old_title, title,
                "北宋徽宗政和二年九月二十五日", origin, 111201825,
                category=f"{group_title}武阶", old_event=f"阶名改为{title}",
                new_event=f"承接{old_title}武阶",
            )
        rank_state(writer, entry_id, title, ordinal, grade, f"{group_title}武阶")
        if entry_id == 418:
            cycle = Q(entry_id, "由承信郎以上至训武郎十阶，并五年一转，为磨勘常调")
            state(
                writer, entry_id, title, "南宋", "承信郎至训武郎十阶五年一转",
                cycle, "记录入品低阶武阶的磨勘周期。",
                category="武阶迁转", officer="武阶", sort_order=112700000,
            )
        writer.commit()


def extract_ungraded_and_generic():
    specs = {
        419: ("进武校尉", "三班差使", "首", "转承信郎"),
        420: ("进义校尉", "三班借差", "第二", None),
    }
    for entry_id, (title, old_title, ordinal, promotion_text) in specs.items():
        writer = W(entry_id)
        intro = Q(entry_id, "武阶名。属无品八阶列。")
        state(
            writer, entry_id, title,
            "北宋徽宗政和二年九月二十五日", "列入无品武阶",
            intro, f"记录{title}属于无品武阶序列。",
            category="无品武阶", officer="武阶", sort_order=111201825,
        )
        origin = sentence(entry_id, "北宋政和二年九月二十五日")
        group_members(
            writer, entry_id, "小使臣",
            "北宋徽宗政和二年九月二十五日",
            "改武选官名后划入小使臣阶", (title,), origin,
            111201825, "小使臣武阶",
        )
        add_evolution(
            writer, entry_id, old_title, title,
            "北宋徽宗政和二年九月二十五日", origin, 111201825,
            category="无品武阶", old_event=f"阶名改为{title}",
            new_event=f"承接{old_title}武阶",
        )
        rank_needle = (
            "为无品武阶之首阶" if entry_id == 419 else "为无品武阶第二阶"
        )
        rank_quote = Q(entry_id, rank_needle)
        state(
            writer, entry_id, title, "南宋高宗绍兴厘定",
            f"列为无品武阶{ordinal}阶，参吏部选", rank_quote,
            f"记录{title}绍兴厘定后的无品序位。",
            category="绍兴无品武阶", officer="武阶", sort_order=113100000,
        )
        if promotion_text:
            promotion = Q(entry_id, promotion_text)
            add_evolution(
                writer, entry_id, title, "承信郎", "南宋酬赏改转制度",
                promotion, 114000000, category="武阶迁转",
                old_event="遇酬赏改转承信郎", new_event="由进武校尉酬赏改转",
            )
        writer.commit()

    entry_id = 421
    writer = W(entry_id)
    quote = Q(entry_id, "进武校尉、进义校尉通称")
    _, group_tp = state(
        writer, entry_id, "校尉", "宋代", "进武校尉、进义校尉的通称",
        quote, "据词条定义建立校尉统称节点。",
        category="无品武阶", officer="职官总名", sort_order=96000000,
    )
    for title in ("进武校尉", "进义校尉"):
        _, member_tp = state(
            writer, entry_id, title, "宋代", "属于校尉所指范围", quote,
            f"据原文建立{title}作为校尉实例的节点。",
            category="无品武阶", officer="武阶", sort_order=96000000,
        )
        relation(
            writer, entry_id, group_tp, member_tp, "统称与实例", quote,
            f"原文明示校尉是进武校尉、进义校尉的通称，{title}为其实例。",
        )
    writer.commit()


def main():
    expected = [
        "武显郎", "武节郎", "武略郎", "武经郎", "武义郎", "武翼郎",
        "训武郎", "敦武郎", "修武郎", "从义郎", "秉义郎", "忠训郎",
        "忠翊郎", "成忠郎", "保义郎", "承节郎", "承信郎", "进武校尉",
        "进义校尉", "校尉",
    ]
    assert [F[i]["title"] for i in range(402, 422)] == expected
    extract_regular_lang()
    extract_dashi_xiaoshi()
    extract_ungraded_and_generic()


if __name__ == "__main__":
    main()
