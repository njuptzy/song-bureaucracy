#!/usr/bin/env python3
"""提取 chapter11t12 第302-321条：诸司副使末阶与东班诸司使副。"""

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
    "extract_11t12_282_301_helpers", HERE / "extract_11t12_282_301.py"
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


F = {entry_id: load(entry_id) for entry_id in range(302, 322)}
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
establish_member = base.establish_member
add_group_members = base.base.add_group_members


def extract_deputy_envoys():
    specs = (
        (302, "西作坊副使", "武显郎", "余与“东作坊副使”同。"),
        (303, "庄宅副使", "武节郎", None),
        (304, "六宅副使", "武节郎", None),
        (305, "文思副使", "武节郎", None),
        (306, "内园副使", "武略郎", None),
        (307, "洛苑副使", "武略郎", None),
        (307, "如京副使", "武略郎", None),
        (308, "崇仪副使", "武略郎", None),
        (309, "西京左藏库副使", "武经郎", None),
        (310, "西京作坊副使", "武义郎", None),
        (311, "东染院副使", "武义郎", None),
        (312, "西染院副使", "武义郎", "余与“东染院副使”同。"),
        (313, "礼宾副使", "武义郎", None),
        (314, "供备库副使", "武翼郎", None),
    )
    for entry_id, title, successor, same_as in specs:
        writer = W(entry_id)
        if same_as:
            intro = Q(entry_id, same_as)
        elif entry_id == 309:
            intro = Q(entry_id, "武阶名。属诸司副使\n阶列。")
        else:
            intro = Q(entry_id, "武阶名。属诸司副使阶列。")
        establish_member(
            writer, entry_id, title, "诸司副使", "诸司副使武阶", intro
        )
        if same_as:
            grade_quote = intro
        elif entry_id == 311:
            grade_quote = Q(entry_id, "元丰新制为从七品")
        else:
            grade_quote = Q(entry_id, "元丰新制从七品")
        add_grade(
            writer, entry_id, title, "北宋神宗元丰新制", "从七品",
            grade_quote, 108000000, "诸司副使武阶",
        )
        if same_as:
            reform_quote = intro
        elif entry_id == 314:
            reform_quote = Q(entry_id, "政和二年九月二十五日，其阶名易为武翼郎")
        else:
            reform_quote = Q(
                entry_id, f"政和二年九月二十五日，其阶名易为{successor}"
            )
        add_evolution(
            writer, entry_id, title, successor,
            "北宋徽宗政和二年九月二十五日", reform_quote, 111201825,
            category="诸司副使武阶", old_event=f"阶名易为{successor}",
            new_event=f"承接{title}武阶",
        )
        writer.commit()


def east_group(writer, entry_id, quote):
    _, group_tp = state(
        writer, entry_id, "东班诸司使、副使", "北宋",
        "东班诸司使、副使阶列", quote,
        "据词条定义建立或复用东班诸司使、副使统称节点。",
        category="东班技术官阶", officer="职官总名", sort_order=96000000,
    )
    return group_tp


def add_east_member(writer, entry_id, title, quote, *, time="北宋"):
    group_tp = east_group(writer, entry_id, quote)
    _, member_tp = state(
        writer, entry_id, title, time, "属于东班诸司使副阶列", quote,
        f"据原文建立或复用{title}东班阶官节点。",
        category="东班技术官阶", officer="技术官阶", sort_order=96000000,
    )
    relation(
        writer, entry_id, group_tp, member_tp, "统称与实例", quote,
        f"原文明示{title}属于东班诸司使、副使阶列。",
    )
    return member_tp


def add_pair_grade(writer, entry_id, base_title, quote):
    add_grade(
        writer, entry_id, f"{base_title}使", "北宋神宗元丰官制", "正七品",
        quote, 108000000, "东班技术官阶",
    )
    add_grade(
        writer, entry_id, f"{base_title}副使", "北宋神宗元丰官制", "从七品",
        quote, 108000000, "东班技术官阶",
    )


def establish_pair(entry_id, base_title, intro_quote, grade_quote):
    writer = W(entry_id)
    add_east_member(writer, entry_id, f"{base_title}使", intro_quote)
    add_east_member(writer, entry_id, f"{base_title}副使", intro_quote)
    add_pair_grade(writer, entry_id, base_title, grade_quote)
    return writer


def extract_east_class_overview():
    entry_id = 315
    writer = W(entry_id)
    origin = Q(
        entry_id,
        "唐制，百职由九寺五监分掌。开元中，始置诸使，寺监物务多归诸使。"
    )
    state(
        writer, entry_id, "诸使", "唐玄宗开元中",
        "始置诸使，寺监物务多归诸使", origin,
        "据原文建立唐开元诸使职源节点。",
        category="前代职源", officer="职官总名", sort_order=71300000,
    )
    division = Q(entry_id, "宋诸司使副有东、西班之分。")
    _, group_tp = state(
        writer, entry_id, "诸司使副", "北宋", "分为东班、西班", division,
        "据原文建立诸司使副总称节点。", category="诸司使副班列",
        officer="职官总名", sort_order=96000000,
    )
    for title in ("东班", "西班"):
        _, member_tp = state(
            writer, entry_id, title, "北宋", "诸司使副的班列", division,
            f"据原文建立或复用{title}班列节点。",
            category="诸司使副班列", officer="职官总名", sort_order=96000000,
        )
        relation(
            writer, entry_id, group_tp, member_tp, "统称与实例", division,
            f"原文明示宋代诸司使副分为{title}。",
        )
    martial = Q(entry_id, "西班及皇城使、副构成武臣阶官序列")
    _, martial_tp = state(
        writer, entry_id, "武臣阶官序列", "北宋", "由西班及皇城使、副构成",
        martial, "据原文建立武臣阶官序列统称节点。", category="武阶",
        officer="职官总名", sort_order=96000000,
    )
    for title in ("西班", "皇城使", "皇城副使"):
        _, member_tp = state(
            writer, entry_id, title, "北宋", "属于武臣阶官序列", martial,
            f"据原文建立或复用{title}的武臣阶官序列节点。",
            category="武阶", officer="武阶", sort_order=96000000,
        )
        relation(
            writer, entry_id, martial_tp, member_tp, "统称与实例", martial,
            f"原文明示{title}构成武臣阶官序列。",
        )
    change = Q(
        entry_id,
        "熙宁以后，多为伎术官所带阶。政和二年九月二十五日改武选官、医职等名，部分东班诸司使、副，易其阶名为郎、大夫，成为医职官阶。"
    )
    state(
        writer, entry_id, "东班诸司使、副使", "北宋神宗熙宁以后",
        "多为伎术官所带阶", change,
        "记录熙宁以后东班诸司使副转为伎术官所带阶。",
        category="技术官阶", officer="职官总名", sort_order=106800000,
    )
    state(
        writer, entry_id, "东班诸司使、副使",
        "北宋徽宗政和二年九月二十五日",
        "部分阶名易为郎、大夫，成为医职官阶", change,
        "记录政和二年东班诸司使副阶名改革。",
        category="医职官阶", officer="职官总名", sort_order=111201825,
    )
    technical = Q(
        entry_id,
        "东班翰林使、副以下至翰林医官使、副，熙宁以后，多为伎术官所带阶"
    )
    add_group_members(
        writer, entry_id, "技术官", "北宋神宗熙宁以后",
        "东班翰林以下十九名使、副使并授技术官", technical,
        base.base.EASTERN_MEMBERS[2:], 106800000, category="技术官阶",
        member_officer="技术官阶",
    )
    grade = Q(entry_id, "东班诸司正使正七品、副使从七品")
    state(
        writer, entry_id, "东班诸司使、副使", "北宋神宗元丰官制",
        "正使正七品、副使从七品", grade,
        "记录东班诸司正使、副使的官品。",
        category="东班技术官阶", officer="职官总名", sort_order=108000000,
    )
    writer.commit()


def extract_hanlin_and_shangshi():
    entry_id = 316
    intro = Q(entry_id, "阶官名。属东班诸司使副阶列。")
    grade = Q(entry_id, "元丰官制定正使为正七品、副使从七品")
    writer = establish_pair(entry_id, "翰林", intro, grade)
    for time, event, needle, order in (
        ("唐宪宗元和中", "已有翰林使之名", "唐宪宗元和中已有翰林使之名", 80600000),
        ("五代后梁", "置翰林使", "五代后梁置翰林使", 90700000),
    ):
        quote = Q(entry_id, needle)
        state(writer, entry_id, "翰林使", time, event, quote,
              f"建立翰林使{time}职源节点。", category="前代职源",
              officer="阶官", sort_order=order)
    song = Q(entry_id, "宋初沿置翰林使、副使")
    for title in ("翰林使", "翰林副使"):
        state(writer, entry_id, title, "宋初", "沿置", song,
              f"记录宋初沿置{title}。", category="东班技术官阶",
              officer="技术官阶", sort_order=96000000)
    writer.commit()

    entry_id = 317
    intro = Q(entry_id, "阶官名。属东班诸司使副阶列。")
    grade = Q(entry_id, "正使正七品、副使从七品")
    writer = establish_pair(entry_id, "尚食", intro, grade)
    for time, titles, needle, order in (
        ("唐代", ("尚食使",), "唐置尚食使", 70000000),
        ("五代后梁", ("尚食使", "尚食副使"), "五代后梁有尚食使、副使", 90700000),
        ("宋代", ("尚食使", "尚食副使"), "宋沿置", 96000000),
    ):
        quote = Q(entry_id, needle)
        for title in titles:
            state(writer, entry_id, title, time, needle, quote,
                  f"记录{title}{time}职源。",
                  category="前代职源" if time != "宋代" else "东班技术官阶",
                  officer="技术官阶", sort_order=order)
    writer.commit()


def extract_kitchen_and_armory():
    entry_id = 318
    intro = Q(entry_id, "阶官名。属东班诸司使副阶列。")
    grade = Q(entry_id, "正使正七品、副使从七品")
    writer = establish_pair(entry_id, "御厨", intro, grade)
    tang = Q(entry_id, "唐昭宗天祐元年四月已见置御厨使")
    state(writer, entry_id, "御厨使", "唐昭宗天祐元年四月", "已见设置",
          tang, "建立御厨使唐代职源节点。", category="前代职源",
          officer="阶官", sort_order=90400800)
    liang = Q(entry_id, "后梁开平元年五月改御食使为司膳使")
    add_evolution(writer, entry_id, "御食使", "司膳使", "五代后梁开平元年五月",
                  liang, 90701000, category="前代职源",
                  old_event="改为司膳使", new_event="由御食使改名")
    song = Q(entry_id, "宋置御厨使、御厨副使")
    for title in ("御厨使", "御厨副使"):
        state(writer, entry_id, title, "宋代", "设置", song,
              f"记录宋代设置{title}。", category="东班技术官阶",
              officer="技术官阶", sort_order=96000000)
    writer.commit()

    entry_id = 319
    intro = Q(entry_id, "阶官名。属东班诸司使、副使阶列。")
    grade = Q(entry_id, "正使正七品、副使从七品")
    writer = establish_pair(entry_id, "军器库", intro, grade)
    tang = Q(entry_id, "唐开元三年十二月二十四日，“以军器使为监”，是即军器使始置于开元三年十二月之前")
    state(writer, entry_id, "军器使", "唐玄宗开元三年十二月二十四日之前",
          "已经设置", tang, "建立军器使唐代职源节点。", category="前代职源",
          officer="阶官", sort_order=71502424)
    for title, time, needle, order in (
        ("军器库使", "北宋太祖开宝四年五月三日", "军器库使楚昭辅检校左藏库金帛", 97101003),
        ("军器库副使", "北宋太宗太平兴国二年正月十二日", "陈赞以弓箭库官为军器库副使", 97700212),
    ):
        quote = Q(entry_id, needle)
        state(writer, entry_id, title, time, "已见设置", quote,
              f"据纪事建立{title}宋初节点。", category="东班技术官阶",
              officer="技术官阶", sort_order=order)
    reform = Q(entry_id, "政和二年九月二十五日，军器库使、副使分别易为医官成全大夫、成全郎阶")
    add_evolution(writer, entry_id, "军器库使", "成全大夫",
                  "北宋徽宗政和二年九月二十五日", reform, 111201825,
                  category="医职官阶", old_event="阶名易为成全大夫",
                  new_event="承接军器库使阶")
    add_evolution(writer, entry_id, "军器库副使", "成全郎",
                  "北宋徽宗政和二年九月二十五日", reform, 111201825,
                  category="医职官阶", old_event="阶名易为成全郎",
                  new_event="承接军器库副使阶")
    writer.commit()

    # 同一 OCR 行粘入的“仪鸾使、副使”是原书 p646 的独立词条。
    intro = Q(entry_id, "阶官名。属东班诸司使副阶列。")
    grade = Q(entry_id, "正使正七品、副使从七品")
    writer = establish_pair(entry_id, "仪鸾", intro, grade)
    origin = Q(entry_id, "唐天宝间置营幕使，后改同和院使")
    add_evolution(writer, entry_id, "营幕使", "同和院使", "唐玄宗天宝间",
                  origin, 74200000, category="前代职源",
                  old_event="改为同和院使", new_event="由营幕使改名")
    liang = Q(entry_id, "五代后梁开平元年五月，改同和院使为仪鸾院使，简称仪鸾使")
    add_evolution(writer, entry_id, "同和院使", "仪鸾院使",
                  "五代后梁开平元年五月", liang, 90701000,
                  category="前代职源", old_event="改为仪鸾院使",
                  new_event="由同和院使改名，简称仪鸾使")
    song = Q(entry_id, "宋沿置仪鸾使，并设副使")
    for title in ("仪鸾使", "仪鸾副使"):
        state(writer, entry_id, title, "宋代", "沿置或设置", song,
              f"记录宋代{title}设置。", category="东班技术官阶",
              officer="技术官阶", sort_order=96000000)
    writer.commit()


def extract_bow_and_clothing_store():
    entry_id = 320
    intro = Q(entry_id, "阶官名。属东班诸司使副阶列。")
    grade = Q(entry_id, "正使正七品、副使从七品")
    writer = establish_pair(entry_id, "弓箭库", intro, grade)
    tang = Q(entry_id, "唐玄宗朝已有内弓箭库使之名")
    state(writer, entry_id, "内弓箭库使", "唐玄宗朝", "已有此名", tang,
          "建立内弓箭库使唐代职源节点。", category="前代职源",
          officer="阶官", sort_order=73000000)
    rename = Q(entry_id, "五代后梁置弓箭库使，去“内”字")
    add_evolution(writer, entry_id, "内弓箭库使", "弓箭库使", "五代后梁",
                  rename, 90700000, category="前代职源",
                  old_event="去“内”字改称弓箭库使", new_event="由内弓箭库使改名")
    song = Q(entry_id, "宋置弓箭库使、副使")
    for title in ("弓箭库使", "弓箭库副使"):
        state(writer, entry_id, title, "宋代", "设置", song,
              f"记录宋代设置{title}。", category="东班技术官阶",
              officer="技术官阶", sort_order=96000000)
    writer.commit()

    entry_id = 321
    intro = Q(entry_id, "阶官名。属东班诸司使副阶列。")
    grade = Q(entry_id, "正使正七品、副使从七品")
    writer = establish_pair(entry_id, "衣库", intro, grade)
    early = Q(entry_id, "宋太祖、太宗朝为内衣库使、副使")
    for title in ("内衣库使", "内衣库副使"):
        state(writer, entry_id, title, "北宋太祖、太宗朝", "以此名设置", early,
              f"建立{title}宋初节点。", category="东班技术官阶",
              officer="技术官阶", sort_order=96000000)
    xianping = Q(entry_id, "真宗咸平间已省称衣库使、副使")
    for old, new in (("内衣库使", "衣库使"), ("内衣库副使", "衣库副使")):
        add_evolution(writer, entry_id, old, new, "北宋真宗咸平间", xianping,
                      100000000, category="东班技术官阶",
                      old_event=f"省称{new}", new_event=f"由{old}省称")
    unchanged = Q(entry_id, "其后“内衣库”改为“尚衣库”，衣库使、副使之名不变")
    for title in ("衣库使", "衣库副使"):
        state(writer, entry_id, title, "北宋真宗咸平间以后",
              "所属内衣库改尚衣库后官名不变", unchanged,
              f"记录机构改名后{title}之名不变。", category="东班技术官阶",
              officer="技术官阶", sort_order=100100000)
    writer.commit()


def main():
    expected = [
        "西作坊副使", "庄宅副使", "六宅副使", "文思副使", "内园副使",
        "洛苑副使", "崇仪副使", "西京左藏库副使", "西京作坊副使",
        "东染院副使", "西染院副使", "礼宾副使", "供备库副使",
        "东班诸司使、副使", "翰林使、副使", "尚食使、副使",
        "御厨使、副使", "军器库使、副使", "弓箭库使、副使",
        "衣库使、副使",
    ]
    assert [F[i]["title"] for i in range(302, 322)] == expected
    extract_deputy_envoys()
    extract_east_class_overview()
    extract_hanlin_and_shangshi()
    extract_kitchen_and_armory()
    extract_bow_and_clothing_store()


if __name__ == "__main__":
    main()
