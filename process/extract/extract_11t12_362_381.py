#!/usr/bin/env python3
"""提取 chapter11t12 第362-381条：流外武阶与政和以后武选官阶。"""

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
    "extract_11t12_322_341_helpers", HERE / "extract_11t12_322_341.py"
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


F = {entry_id: load(entry_id) for entry_id in range(362, 382)}
base.F = F
base.base.F = F
base.base.helpers.F = F
base.ENTRY_DB = ENTRY_DB
base.base.ENTRY_DB = ENTRY_DB
base.base.helpers.ENTRY_DB = ENTRY_DB
base.base.helpers.NEW_SORT = {}

W = base.W
Q = base.Q
state = base.state
relation = base.relation
add_evolution = base.add_evolution
add_grade = base.add_grade
group_members = base.group_members


def extract_military_general_terms():
    entry_id = 362
    writer = W(entry_id)
    intro = Q(entry_id, "无品武阶名。位次于正名军将。")
    group_members(
        writer, entry_id, "军将", "宋代", "正名军将与守阙军将的总称",
        ("守阙军将",), intro, 96000000, "无品武阶",
    )
    reform = Q(entry_id, "政和二年九月二十五日，其阶名易为守阙进义副尉")
    add_evolution(
        writer, entry_id, "守阙军将", "守阙进义副尉",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="无品武阶", old_event="阶名易为守阙进义副尉",
        new_event="承接守阙军将武阶",
    )
    writer.commit()

    entry_id = 363
    writer = W(entry_id)
    intro = Q(entry_id, "军将、守阙军将与大将之连称。")
    group_members(
        writer, entry_id, "军大将", "宋代", "军将、守阙军将与大将连称",
        ("军将", "守阙军将", "大将"), intro, 96000000, "无品武阶",
    )
    quota = Q(entry_id, "熙宁七年三月九日，诏大将、军将以一千五百人为额，守阙军将并募充")
    state(
        writer, entry_id, "军大将", "北宋神宗熙宁七年三月九日",
        "大将、军将以一千五百人为额，守阙军将并募充", quota,
        "记录军大将相关阶名的熙宁七年员额规定。", category="无品武阶",
        officer="职官总名", sort_order=107400609,
    )
    writer.commit()


def add_eight_rank_members(writer, entry_id, members, quote):
    group_members(
        writer, entry_id, "八资", "北宋神宗熙宁六年五月二十一日",
        "勇敢效用法所创八等赏功法", members, quote, 107301021,
        "流外武阶",
    )


def extract_outside_ranks():
    entry_id = 364
    writer = W(entry_id)
    intro = Q(entry_id, "流外武阶名。")
    group_members(
        writer, entry_id, "流外武阶", "北宋神宗熙宁六年五月二十一日",
        "勇敢效用法形成的流外武阶", ("甲头",), intro, 107301021,
        "流外武阶",
    )
    system = Q(
        entry_id,
        "北宋神宗熙宁六年五月二十一日，枢密院实行《勇敢效用法》，创立八等赏功法，八等即八资。其第二资为甲头",
    )
    add_eight_rank_members(writer, entry_id, ("甲头",), system)
    reform = Q(entry_id, "南宋绍兴五年正名，“甲头改作进勇副尉”，并正式纳入绍兴厘定武阶序列")
    add_evolution(
        writer, entry_id, "甲头", "进勇副尉", "南宋高宗绍兴五年",
        reform, 113500000, category="绍兴武阶",
        old_event="正名为进勇副尉", new_event="承接甲头流外武阶",
    )
    writer.commit()

    entry_id = 365
    writer = W(entry_id)
    intro = Q(entry_id, "流外武阶名。")
    group_members(
        writer, entry_id, "流外武阶", "北宋神宗熙宁六年五月二十一日",
        "勇敢效用法形成的流外武阶", ("公据",), intro, 107301021,
        "流外武阶",
    )
    system = Q(
        entry_id,
        "北宋神宗熙宁六年五月二十一日，枢密院实行《勇敢效用法》，创立八等赏功法，八等即八资。其第一等为“公据”，赏给有战功效用以“公据”，第八等为三班借职（入品武阶）",
    )
    add_eight_rank_members(writer, entry_id, ("公据", "三班借职"), system)
    reform = Q(entry_id, "南宋绍兴五年正名，“公据改作守阙进勇副尉”，正式列入武阶序列之内")
    add_evolution(
        writer, entry_id, "公据", "守阙进勇副尉", "南宋高宗绍兴五年",
        reform, 113500000, category="绍兴武阶",
        old_event="正名为守阙进勇副尉", new_event="承接公据流外武阶",
    )
    writer.commit()


def extract_grand_marshal():
    entry_id = 366
    writer = W(entry_id)
    reform = Q(
        entry_id,
        "政和二年九月二十五日，新定三公官，以少师易太尉，为三少之一，而太尉则列为武阶之首",
    )
    add_evolution(
        writer, entry_id, "太尉", "少师", "北宋徽宗政和二年九月二十五日",
        reform, 111201825, category="三公三少改制",
        old_event="旧三公官名易为少师", new_event="承接旧太尉三公官名",
    )
    group_members(
        writer, entry_id, "武阶", "北宋徽宗政和二年九月二十五日",
        "颁《改武选官名诏》，武阶改用新名，太尉居首",
        ("太尉",), reform, 111201825, "政和武阶新制",
    )
    grade = Q(entry_id, "政和二年十月三日，太尉官品由正一品降为正二品")
    add_grade(
        writer, entry_id, "太尉", "北宋徽宗政和二年十月三日以后",
        "正二品", grade, 111202003, "政和武阶新制",
    )
    writer.commit()


HENGXING_SPECS = {
    367: ("通侍大夫", ("内客省使",), "北宋徽宗政和二年九月二十五日", 111201825, 2, "正五品", None),
    368: ("正侍大夫", ("延福宫使",), "北宋徽宗政和二年九月二十五日", 111201825, 3, "正五品", None),
    369: ("宣正大夫", (), "北宋徽宗政和六年十一月三十日", 111602230, 4, "正五品", None),
    370: ("履正大夫", (), "北宋徽宗政和六年十一月三十日", 111602230, 5, "正五品", None),
    371: ("协忠大夫", (), "北宋徽宗政和六年十一月三十日", 111602230, 6, "正五品", None),
    372: ("中侍大夫", ("景福殿使",), "北宋徽宗政和二年九月二十五日", 111201825, 7, "正五品", "协忠大夫"),
    373: ("中亮大夫", ("客省使", "宣庆使"), "北宋徽宗政和二年九月二十五日", 111201825, 8, "从五品", "中侍大夫"),
    374: ("中卫大夫", ("引进使", "宣政使"), "北宋徽宗政和二年九月二十五日", 111201825, 9, "从五品", "中亮大夫"),
    375: ("翊卫大夫", (), "北宋徽宗政和六年十一月三十日", 111602230, 10, "从五品", "中卫大夫"),
    376: ("亲卫大夫", (), "北宋徽宗政和六年十一月三十日", 111602230, 11, "从五品", "翊卫大夫"),
    377: ("拱卫大夫", ("四方馆使", "昭宣使"), "北宋徽宗政和二年九月二十五日", 111201825, 12, "正六品", "亲卫大夫"),
    378: ("左武大夫", ("东上阁门使",), "北宋徽宗政和二年九月二十五日", 111201825, 13, "正六品", "拱卫大夫"),
    379: ("右武大夫", ("西上阁门使",), "北宋徽宗政和二年九月二十五日", 111201825, 14, "正六品", "左武大夫"),
}

CN_ORDINAL = {
    2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八",
    9: "九", 10: "十", 11: "十一", 12: "十二", 13: "十三", 14: "十四",
}


def origin_quote(entry_id, old_titles, title):
    text = F[entry_id]["text"]
    if not old_titles:
        return Q(entry_id, "北宋政和六年十一月三十日创置")
    if len(old_titles) == 1:
        needle = f"由{old_titles[0]}改"
        if needle not in text:
            needle = f"由{old_titles[0]}改名"
        return Q(entry_id, needle)
    joined = "、".join(old_titles)
    return Q(entry_id, f"由{joined}改")


def extract_hengxing_ranks():
    for entry_id, spec in HENGXING_SPECS.items():
        title, old_titles, origin_time, origin_order, ordinal, grade, promotion = spec
        writer = W(entry_id)
        intro = Q(entry_id, "武阶名。属横行正使十三阶列。")
        group_members(
            writer, entry_id, "横行正使",
            "北宋徽宗政和六年十一月三十日以后",
            "政和六年增阶后横行正使十三阶", (title,), intro,
            111602230, "横行武阶",
        )
        origin = origin_quote(entry_id, old_titles, title)
        if old_titles:
            for old_title in old_titles:
                add_evolution(
                    writer, entry_id, old_title, title, origin_time,
                    origin, origin_order, category="横行武阶",
                    old_event=f"阶名改为{title}", new_event=f"承接{old_title}武阶",
                )
        else:
            state(
                writer, entry_id, title, origin_time, "创置", origin,
                f"建立{title}创置节点。", category="横行武阶",
                officer="武阶", sort_order=origin_order,
            )
        rank_quote = Q(
            entry_id, f"绍兴厘定入品武阶五十二阶之第{CN_ORDINAL[ordinal]}"
        )
        state(
            writer, entry_id, title, "南宋高宗绍兴厘定",
            f"列入品武阶五十二阶之第{ordinal}阶", rank_quote,
            f"记录{title}绍兴厘定序位。", category="绍兴武阶",
            officer="武阶", sort_order=113100000,
        )
        grade_quote = Q(entry_id, grade)
        add_grade(
            writer, entry_id, title, "南宋高宗绍兴厘定", grade,
            grade_quote, 113100000, "绍兴武阶",
        )
        if promotion:
            if entry_id == 372:
                promotion_quote = Q(entry_id, "特旨方许迁转协忠大夫以上阶")
            else:
                promotion_quote = Q(entry_id, f"磨勘转{promotion}")
            add_evolution(
                writer, entry_id, title, promotion, "南宋绍兴磨勘迁转制度",
                promotion_quote, 114000000, category="武阶迁转",
                old_event=f"磨勘或特旨迁转{promotion}",
                new_event=f"由{title}迁转",
            )
        writer.commit()


def extract_regular_envoy_new_ranks():
    entry_id = 380
    writer = W(entry_id)
    intro = Q(entry_id, "武阶名。属诸司正使八阶列。")
    group_members(
        writer, entry_id, "诸司正使", "北宋徽宗政和二年九月二十五日",
        "改武选官名后合并为八阶大夫", ("武功大夫",), intro,
        111201825, "诸司正使武阶",
    )
    origin = Q(entry_id, "北宋政和二年九月二十五日，由皇城使改")
    add_evolution(
        writer, entry_id, "皇城使", "武功大夫",
        "北宋徽宗政和二年九月二十五日", origin, 111201825,
        category="诸司正使武阶", old_event="阶名改为武功大夫",
        new_event="承接皇城使武阶",
    )
    rank = Q(entry_id, "绍兴厘定入品武阶五十二阶之第十五阶")
    state(
        writer, entry_id, "武功大夫", "南宋高宗绍兴厘定",
        "列入品武阶五十二阶之第十五阶", rank,
        "记录武功大夫绍兴厘定序位。", category="绍兴武阶",
        officer="武阶", sort_order=113100000,
    )
    grade = Q(entry_id, "为正七品官")
    add_grade(writer, entry_id, "武功大夫", "南宋高宗绍兴厘定", "正七品", grade, 113100000, "绍兴武阶")
    initial = Q(entry_id, "政和改名初，武功大夫径迁横行（右武大夫）")
    add_evolution(
        writer, entry_id, "武功大夫", "右武大夫", "北宋徽宗政和改名初",
        initial, 111201825, category="武阶迁转",
        old_event="可径迁右武大夫", new_event="由武功大夫径迁",
    )
    restriction = Q(entry_id, "绍兴二年正月十六日，改定非军功不得由武功大夫转至右武大夫以上阶")
    state(
        writer, entry_id, "武功大夫", "南宋高宗绍兴二年正月十六日",
        "非军功不得转至右武大夫以上阶", restriction,
        "记录武功大夫横行止法。", category="武阶迁转限制",
        officer="武阶", sort_order=113200216,
    )
    writer.commit()

    entry_id = 381
    writer = W(entry_id)
    intro = Q(entry_id, "武阶名。属诸司正使八阶列。")
    group_members(
        writer, entry_id, "诸司正使", "北宋徽宗政和二年九月二十五日",
        "改武选官名后合并为八阶大夫", ("武德大夫",), intro,
        111201825, "诸司正使武阶",
    )
    origin = Q(entry_id, "北宋政和二年九月二十五日，由宫苑使、左右骐骥使、内藏库使改")
    for old_title in ("宫苑使", "左骐骥使", "右骐骥使", "内藏库使"):
        add_evolution(
            writer, entry_id, old_title, "武德大夫",
            "北宋徽宗政和二年九月二十五日", origin, 111201825,
            category="诸司正使武阶", old_event="阶名改为武德大夫",
            new_event=f"承接{old_title}武阶",
        )
    rank = Q(entry_id, "绍兴厘定入品武阶五十二阶之第十六阶")
    state(
        writer, entry_id, "武德大夫", "南宋高宗绍兴厘定",
        "列入品武阶五十二阶之第十六阶", rank,
        "记录武德大夫绍兴厘定序位。", category="绍兴武阶",
        officer="武阶", sort_order=113100000,
    )
    grade = Q(entry_id, "正七品")
    add_grade(writer, entry_id, "武德大夫", "南宋高宗绍兴厘定", "正七品", grade, 113100000, "绍兴武阶")
    writer.commit()


def main():
    expected = [
        "守阙军将", "军大将", "甲头", "公据", "太尉", "通侍大夫",
        "正侍大夫", "宣正大夫", "履正大夫", "协忠大夫",
        "中侍大夫", "中亮大夫", "中卫大夫", "翊卫大夫",
        "亲卫大夫", "拱卫大夫", "左武大夫", "右武大夫",
        "武功大夫", "武德大夫",
    ]
    assert [F[i]["title"] for i in range(362, 382)] == expected
    extract_military_general_terms()
    extract_outside_ranks()
    extract_grand_marshal()
    extract_hengxing_ranks()
    extract_regular_envoy_new_ranks()


if __name__ == "__main__":
    main()
