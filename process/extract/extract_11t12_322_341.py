#!/usr/bin/env python3
"""提取 chapter11t12 第322-341条：东班使副末阶及大、小使臣。"""

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
    "extract_11t12_262_281_helpers", HERE / "extract_11t12_262_281.py"
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


F = {entry_id: load(entry_id) for entry_id in range(322, 342)}
base.F = F
base.helpers.F = F
base.ENTRY_DB = ENTRY_DB
base.helpers.ENTRY_DB = ENTRY_DB
base.helpers.NEW_SORT = {}

W = base.W
Q = base.Q
state = base.state
relation = base.relation
add_evolution = base.add_evolution
add_grade = base.add_grade


def typed_state(
    writer, entry_id, title, entity_type, time, event, quotation, decision, *,
    category=None, officer=None, grade=None, sort_order=None,
):
    entity_id = writer.entity(title, entity_type, decision, quotation=quotation)
    before = {
        row[0]
        for row in writer.conn.execute(
            "SELECT id FROM Timepoints WHERE entity_id=?", (entity_id,)
        )
    }
    timepoint_id = writer.timepoint(
        entity_id, time, event, decision, quotation,
        attr_category=category, attr_officer_type=officer, attr_grade=grade,
        chain="none",
    )
    if timepoint_id not in before and sort_order is not None:
        base.helpers.place_new_timepoint(
            writer, entity_id, timepoint_id, sort_order,
            f"按历史顺序插入{title}{time}节点：{decision}",
        )
    base.helpers.cite(
        writer, "Timepoints", timepoint_id, entry_id, quotation, decision
    )
    return entity_id, timepoint_id


def institution_state(writer, entry_id, title, time, event, quote, decision, order):
    return typed_state(
        writer, entry_id, title, "机构", time, event, quote, decision,
        category="机构沿革", officer=None, sort_order=order,
    )


def east_group(writer, entry_id, quote):
    _, group_tp = state(
        writer, entry_id, "东班诸司使、副使", "北宋",
        "东班诸司使、副使阶列", quote,
        "据词条定义建立或复用东班诸司使、副使统称节点。",
        category="东班技术官阶", officer="职官总名", sort_order=96000000,
    )
    return group_tp


def establish_pair(entry_id, base_title, intro, grade_quote, *, time="宋代", event="设置"):
    writer = W(entry_id)
    group_tp = east_group(writer, entry_id, intro)
    result = {}
    for suffix, grade in (("使", "正七品"), ("副使", "从七品")):
        title = f"{base_title}{suffix}"
        _, member_tp = state(
            writer, entry_id, title, time, event, intro,
            f"据原文建立或复用{title}{time}节点。",
            category="东班技术官阶", officer="技术官阶", sort_order=96000000,
        )
        relation(
            writer, entry_id, group_tp, member_tp, "统称与实例", intro,
            f"原文明示{title}属于东班诸司使、副使阶列。",
        )
        add_grade(
            writer, entry_id, title, "北宋神宗元丰官制", grade,
            grade_quote, 108000000, "东班技术官阶",
        )
        result[title] = member_tp
    return writer, result


def attach_posts(writer, entry_id, institution_title, institution_tp, posts, time, quote, order):
    for title in posts:
        _, post_tp = state(
            writer, entry_id, title, time, f"隶属{institution_title}", quote,
            f"据原文建立或复用{title}在{institution_title}的编制节点。",
            category="机构职官", officer="官职", sort_order=order,
        )
        relation(
            writer, entry_id, institution_tp, post_tp, "编制隶属", quote,
            f"原文明示{institution_title}设置或管领{title}。",
        )


def group_members(writer, entry_id, group_title, time, event, members, quote, order, category):
    _, group_tp = state(
        writer, entry_id, group_title, time, event, quote,
        f"据原文建立或复用{group_title}{time}统称节点。",
        category=category, officer="职官总名", sort_order=order,
    )
    for title in members:
        _, member_tp = state(
            writer, entry_id, title, time, f"属于{group_title}所指范围", quote,
            f"据原文建立或复用{title}{time}实例节点。",
            category=category, officer="武阶", sort_order=order,
        )
        relation(
            writer, entry_id, group_tp, member_tp, "统称与实例", quote,
            f"原文明示{group_title}在{time}包括{title}。",
        )
    return group_tp


def extract_east_pairs_322_325():
    for entry_id, base_title in ((322, "东绫锦"), (323, "西绫锦")):
        intro = Q(entry_id, "阶官名。属东班诸司使副阶列。")
        grade = Q(entry_id, "正使正七品、副使从七品")
        writer, _ = establish_pair(
            entry_id, base_title, intro, grade, time="宋初", event="设置"
        )
        if entry_id == 323:
            reform = Q(
                entry_id,
                "政和二年九月二十五日，西绫锦使、副使分别易阶名为保和大夫、保和郎，充医官阶",
            )
            add_evolution(
                writer, entry_id, "西绫锦使", "保和大夫",
                "北宋徽宗政和二年九月二十五日", reform, 111201825,
                category="医职官阶", old_event="阶名易为保和大夫",
                new_event="承接西绫锦使阶",
            )
            add_evolution(
                writer, entry_id, "西绫锦副使", "保和郎",
                "北宋徽宗政和二年九月二十五日", reform, 111201825,
                category="医职官阶", old_event="阶名易为保和郎",
                new_event="承接西绫锦副使阶",
            )
        writer.commit()

    entry_id = 324
    intro = Q(entry_id, "阶官名。属东班诸司使副阶列。")
    grade = Q(entry_id, "正使正七品、副使从七品")
    writer, _ = establish_pair(entry_id, "东八作", intro, grade)
    tang = Q(entry_id, "唐玄宗开元初有内八作使")
    state(
        writer, entry_id, "内八作使", "唐玄宗开元初", "已有设置", tang,
        "建立内八作使唐代职源节点。", category="前代职源",
        officer="阶官", sort_order=71300000,
    )
    song = Q(entry_id, "宋初置八作使，后分为东八作使、西八作使，领八作司公事")
    _, old_tp = state(
        writer, entry_id, "八作使", "宋初", "设置并领八作司公事", song,
        "建立八作使宋初节点。", category="机构职官", officer="官职",
        sort_order=96000000,
    )
    _, bureau_tp = institution_state(
        writer, entry_id, "八作司", "宋初", "由八作使领公事", song,
        "建立八作司宋初机构节点。", 96000000,
    )
    relation(
        writer, entry_id, bureau_tp, old_tp, "编制隶属", song,
        "原文明示宋初八作使领八作司公事。",
    )
    split = Q(entry_id, "太平兴国二年，八作司一分为二，以“东、西”称")
    for title in ("东八作使", "西八作使"):
        add_evolution(
            writer, entry_id, "八作使", title, "北宋太宗太平兴国二年",
            split, 97700000, category="东班技术官阶",
            old_event=f"分为{title}", new_event="由八作使分置",
        )
    for title in ("东八作司", "西八作司"):
        _, new_bureau_tp = institution_state(
            writer, entry_id, title, "北宋太宗太平兴国二年",
            "由八作司一分为二", split, f"建立{title}分置节点。", 97700000,
        )
        relation(
            writer, entry_id, bureau_tp, new_bureau_tp, "前后演变", split,
            f"原文明示八作司在太平兴国二年分为{title}。",
        )
    writer.commit()

    entry_id = 325
    intro = Q(entry_id, "阶官名。属东班诸司使副阶列。")
    same = Q(entry_id, "余与“东八作使、副使”条同。")
    writer, _ = establish_pair(entry_id, "西八作", intro, same)
    writer.commit()


def extract_east_pairs_326_332():
    entry_id = 326
    intro = Q(entry_id, "阶官名。属东班诸司使副阶列。")
    grade = Q(entry_id, "正使正七品、副使从七品")
    writer, _ = establish_pair(entry_id, "香药库", intro, grade, time="宋初")
    origin = Q(entry_id, "宋初有香药库，因置使、副使")
    _, inst_tp = institution_state(
        writer, entry_id, "香药库", "宋初", "设置，并因而置使、副使",
        origin, "建立香药库宋初机构节点。", 96000000,
    )
    attach_posts(
        writer, entry_id, "香药库", inst_tp, ("香药库使", "香药库副使"),
        "宋初", origin, 96000000,
    )
    writer.commit()

    entry_id = 327
    intro = Q(entry_id, "阶官名。属东班诸司使副阶列。")
    grade = Q(entry_id, "正使正七品、副使从七品")
    writer, _ = establish_pair(
        entry_id, "牛羊", intro, grade, time="宋初（或置）", event="或已设置"
    )
    origin = Q(entry_id, "北宋开宝二年六月已见置牛羊司。牛羊使、副或为宋朝初年所置")
    _, inst_tp = institution_state(
        writer, entry_id, "牛羊司", "北宋太祖开宝二年六月", "已见设置",
        origin, "建立牛羊司开宝二年节点。", 96901200,
    )
    attach_posts(
        writer, entry_id, "牛羊司", inst_tp, ("牛羊使", "牛羊副使"),
        "宋初（或置）", origin, 96000000,
    )
    writer.commit()

    entry_id = 328
    intro = Q(entry_id, "阶官名。属东班诸司使副阶列。")
    reform = Q(entry_id, "徽宗政和二年九月二十五日，其阶名易为医官保安大夫、保安郎")
    writer, _ = establish_pair(entry_id, "榷易", intro, reform, time="宋初")
    origin = Q(entry_id, "宋初有香药榷易院（大中祥符二年二月并入榷货务），香药、榷易分别置使副")
    _, old_inst_tp = institution_state(
        writer, entry_id, "香药榷易院", "宋初", "设置香药、榷易使副",
        origin, "建立香药榷易院宋初机构节点。", 96000000,
    )
    attach_posts(
        writer, entry_id, "香药榷易院", old_inst_tp, ("榷易使", "榷易副使"),
        "宋初", origin, 96000000,
    )
    _, new_inst_tp = institution_state(
        writer, entry_id, "榷货务", "北宋真宗大中祥符二年二月",
        "并入香药榷易院", origin, "建立榷货务承接节点。", 100900400,
    )
    relation(
        writer, entry_id, old_inst_tp, new_inst_tp, "前后演变", origin,
        "原文明示香药榷易院在大中祥符二年二月并入榷货务。",
    )
    add_evolution(
        writer, entry_id, "榷易使", "保安大夫",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="医职官阶", old_event="阶名易为保安大夫",
        new_event="承接榷易使阶",
    )
    add_evolution(
        writer, entry_id, "榷易副使", "保安郎",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="医职官阶", old_event="阶名易为保安郎",
        new_event="承接榷易副使阶",
    )
    writer.commit()

    entry_id = 329
    intro = Q(entry_id, "阶官名。属东班诸司使副阶列。")
    grade = Q(entry_id, "正使正七品、副使从七品")
    writer, _ = establish_pair(entry_id, "毡毯", intro, grade, time="宋代", event="沿置")
    origin = Q(entry_id, "唐有毡坊、毯坊使，五代合而为一，称毡毯使。宋沿置")
    for title in ("毡坊使", "毯坊使"):
        state(
            writer, entry_id, title, "唐代", "设置", origin,
            f"建立{title}唐代职源节点。", category="前代职源",
            officer="阶官", sort_order=70000000,
        )
        add_evolution(
            writer, entry_id, title, "毡毯使", "五代", origin, 90700000,
            category="前代职源", old_event="合为毡毯使",
            new_event=f"由{title}合并而来",
        )
    writer.commit()

    entry_id = 330
    intro = Q(entry_id, "阶官名。属东班诸司使副阶列。")
    grade = Q(entry_id, "正使正七品、副使从七品")
    writer, _ = establish_pair(entry_id, "鞍辔库", intro, grade)
    origin = Q(entry_id, "唐神策军中有鞍辔库，五代以及辽国置鞍辔库使。宋置鞍辔库使、副使")
    for time, event, order in (("唐代", "神策军中有鞍辔库", 70000000), ("五代以及辽国", "置鞍辔库使", 90700000)):
        state(
            writer, entry_id, "鞍辔库使", time, event, origin,
            f"建立鞍辔库使{time}职源节点。", category="前代职源",
            officer="阶官", sort_order=order,
        )
    _, inst_tp = institution_state(
        writer, entry_id, "鞍辔库", "宋代", "设置使、副使", origin,
        "建立鞍辔库宋代机构节点。", 96000000,
    )
    attach_posts(
        writer, entry_id, "鞍辔库", inst_tp, ("鞍辔库使", "鞍辔库副使"),
        "宋代", origin, 96000000,
    )
    writer.commit()

    entry_id = 331
    intro = Q(entry_id, "阶官名。属东班诸司使副阶列。")
    grade = Q(entry_id, "正使正七品、副使从七品")
    writer, _ = establish_pair(entry_id, "酒坊", intro, grade, time="宋代", event="沿置")
    origin = Q(entry_id, "唐有酒坊使。宋沿置，并置副使")
    state(
        writer, entry_id, "酒坊使", "唐代", "设置", origin,
        "建立酒坊使唐代职源节点。", category="前代职源",
        officer="阶官", sort_order=70000000,
    )
    writer.commit()

    entry_id = 332
    intro = Q(entry_id, "阶官名。属东班诸司使副阶列。")
    grade = Q(entry_id, "正使正七品、副使从七品")
    writer, _ = establish_pair(
        entry_id, "法酒库", intro, grade, time="北宋太祖平河中", event="设置"
    )
    origin = Q(entry_id, "宋太祖平河中，得酒工王恩，善造法曲酒，因置法酒库使、并置副使")
    _, inst_tp = institution_state(
        writer, entry_id, "法酒库", "北宋太祖平河中", "因王恩善造法曲酒而置",
        origin, "建立法酒库设置节点。", 96000000,
    )
    attach_posts(
        writer, entry_id, "法酒库", inst_tp, ("法酒库使", "法酒库副使"),
        "北宋太祖平河中", origin, 96000000,
    )
    writer.commit()


def extract_medical_envoys():
    entry_id = 333
    intro = Q(entry_id, "医职名、阶官名。")
    grade = Q(entry_id, "正使正七品、副使从七品")
    writer, _ = establish_pair(
        entry_id, "翰林医官", intro, grade, time="宋初", event="已设置"
    )
    dual = Q(
        entry_id,
        "具有双重职能，为翰林医官院医职，又充医官迁转官阶，此为不同于东班其余诸司使、副使之处",
    )
    _, inst_tp = institution_state(
        writer, entry_id, "翰林医官院", "宋初", "设置医官使、副使",
        dual, "建立翰林医官院宋初机构节点。", 96000000,
    )
    attach_posts(
        writer, entry_id, "翰林医官院", inst_tp,
        ("翰林医官使", "翰林医官副使"), "宋初", dual, 96000000,
    )
    first = Q(entry_id, "北宋太宗淳化五年八月，以翰林医官赵自化为少府监丞、充医官副使")
    state(
        writer, entry_id, "翰林医官副使", "北宋太宗淳化五年八月",
        "赵自化充任", first, "记录翰林医官副使淳化五年任官实例。",
        category="医职官", officer="医职", sort_order=99401600,
    )
    review = Q(entry_id, "神宗熙宁八年六月四日，规定翰林医官副使、正使五年一磨勘（旧无磨勘法）")
    for title in ("翰林医官使", "翰林医官副使"):
        state(
            writer, entry_id, title, "北宋神宗熙宁八年六月四日",
            "规定五年一磨勘", review, f"记录{title}磨勘制度。",
            category="医职官阶", officer="医职官阶", sort_order=107501204,
        )
    reform = Q(entry_id, "政和二年九月二十五日，翰林医官使、副使分别易为医官阶翰林良医、翰林医正")
    add_evolution(
        writer, entry_id, "翰林医官使", "翰林良医",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="医职官阶", old_event="阶名易为翰林良医",
        new_event="承接翰林医官使阶",
    )
    add_evolution(
        writer, entry_id, "翰林医官副使", "翰林医正",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="医职官阶", old_event="阶名易为翰林医正",
        new_event="承接翰林医官副使阶",
    )
    writer.commit()


def extract_envoy_groups():
    entry_id = 334
    writer = W(entry_id)
    quote = Q(entry_id, "大使臣、小使臣通称。")
    group_members(
        writer, entry_id, "使臣", "宋代", "大使臣、小使臣的通称",
        ("大使臣", "小使臣"), quote, 96000000, "武阶总称",
    )
    origin = Q(entry_id, "使臣之义，始于藩镇")
    state(
        writer, entry_id, "使臣", "唐代藩镇时期", "称谓之义始于藩镇",
        origin, "建立使臣称谓的前代职源节点。", category="前代职源",
        officer="职官总名", sort_order=75000000,
    )
    writer.commit()

    entry_id = 335
    writer = W(entry_id)
    intro = Q(entry_id, "武阶总名。为武臣、内侍迁转官阶。")
    state(
        writer, entry_id, "大使臣", "北宋太宗朝创置内殿崇班后",
        "大使臣名称开始使用", intro,
        "建立大使臣名称始用节点。", category="武阶总称",
        officer="职官总名", sort_order=99100000,
    )
    broad = Q(
        entry_id,
        "《元祐官品令》、政和三年官称、南宋后《吏部条法》，以诸司正使（武功大夫）至内殿崇班（修武郎）或阁门祗候“为大使臣”",
    )
    group_members(
        writer, entry_id, "大使臣", "北宋哲宗元祐官品令至南宋",
        "包括诸司使副、内殿承制崇班及阁门祗候",
        ("诸司正使", "诸司副使", "内殿承制", "内殿崇班", "阁门祗候"),
        broad, 108600000, "大使臣武阶",
    )
    narrow = Q(entry_id, "南宋以敦武郎（光宗朝以后改训武郎）、修武郎、阁门祗候为大使臣，即不包括旧诸司正使、副使")
    group_members(
        writer, entry_id, "大使臣", "南宋", "狭义范围不包括旧诸司正使副使",
        ("敦武郎", "训武郎", "修武郎", "阁门祗候"), narrow,
        112700000, "大使臣武阶",
    )
    alternative = Q(entry_id, "或止以内殿承制、内殿崇班为大使臣，而不将阁门祗候列入大使臣阶之内")
    group_members(
        writer, entry_id, "大使臣", "宋代另一用法",
        "仅指内殿承制、内殿崇班",
        ("内殿承制", "内殿崇班"), alternative, 96000000, "大使臣武阶",
    )
    grades = Q(entry_id, "元丰官制，诸司使正七品、副使从七品，内殿承制、内殿崇班正八品")
    for title, grade in (
        ("诸司正使", "正七品"), ("诸司副使", "从七品"),
        ("内殿承制", "正八品"), ("内殿崇班", "正八品"),
    ):
        add_grade(
            writer, entry_id, title, "北宋神宗元丰官制", grade,
            grades, 108000000, "武阶",
        )
    writer.commit()


def extract_senior_envoy_members():
    entry_id = 336
    writer = W(entry_id)
    intro = Q(entry_id, "武阶名。属大使臣阶列。")
    group_members(
        writer, entry_id, "大使臣", "北宋前期", "大使臣阶列",
        ("内殿承制",), intro, 96000000, "大使臣武阶",
    )
    origin = Q(entry_id, "北宋大中祥符二年正月九日始置")
    state(
        writer, entry_id, "内殿承制", "北宋真宗大中祥符二年正月九日",
        "始置", origin, "建立内殿承制始置节点。", category="大使臣武阶",
        officer="武阶", sort_order=100900209,
    )
    promotion = Q(entry_id, "内殿承制叙迁转诸司副使")
    add_evolution(
        writer, entry_id, "内殿承制", "诸司副使", "北宋叙迁制度",
        promotion, 106000000, category="武阶迁转",
        old_event="叙迁转诸司副使", new_event="由内殿承制叙迁",
    )
    grades = Q(entry_id, "宋前期为七品，元丰官制、《元祐令》为正八品")
    add_grade(writer, entry_id, "内殿承制", "宋前期", "七品", grades, 96000000, "大使臣武阶")
    add_grade(writer, entry_id, "内殿承制", "北宋神宗元丰官制", "正八品", grades, 108000000, "大使臣武阶")
    reform = Q(entry_id, "政和二年九月二十五日，其阶名易为敦武郎")
    add_evolution(
        writer, entry_id, "内殿承制", "敦武郎",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="大使臣武阶", old_event="阶名易为敦武郎",
        new_event="承接内殿承制武阶",
    )
    writer.commit()

    entry_id = 337
    writer = W(entry_id)
    intro = Q(entry_id, "武阶名。属大使臣阶列。")
    group_members(
        writer, entry_id, "大使臣", "北宋前期", "大使臣阶列",
        ("内殿崇班",), intro, 96000000, "大使臣武阶",
    )
    origin = Q(entry_id, "北宋太宗淳化二年正月十四日创置")
    state(
        writer, entry_id, "内殿崇班", "北宋太宗淳化二年正月十四日",
        "创置", origin, "建立内殿崇班创置节点。", category="大使臣武阶",
        officer="武阶", sort_order=99100214,
    )
    promotion = Q(entry_id, "一由东头供奉官转内殿崇班，一由阁门祗候转内殿崇班；内殿崇班转内殿承制")
    for old, new in (
        ("东头供奉官", "内殿崇班"), ("阁门祗候", "内殿崇班"),
        ("内殿崇班", "内殿承制"),
    ):
        add_evolution(
            writer, entry_id, old, new, "北宋叙迁制度", promotion,
            106000000, category="武阶迁转", old_event=f"叙迁转{new}",
            new_event=f"由{old}叙迁",
        )
    grades = Q(entry_id, "宋前期为七品，元丰官制为正八品")
    add_grade(writer, entry_id, "内殿崇班", "宋前期", "七品", grades, 96000000, "大使臣武阶")
    add_grade(writer, entry_id, "内殿崇班", "北宋神宗元丰官制", "正八品", grades, 108000000, "大使臣武阶")
    reform = Q(entry_id, "政和二年九月二十五日，其阶名易为修武郎")
    add_evolution(
        writer, entry_id, "内殿崇班", "修武郎",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="大使臣武阶", old_event="阶名易为修武郎",
        new_event="承接内殿崇班武阶",
    )
    writer.commit()

    entry_id = 338
    writer = W(entry_id)
    intro = Q(entry_id, "武阶名。属大使臣阶列。")
    group_members(
        writer, entry_id, "大使臣", "宋代", "包括阁门祗候",
        ("阁门祗候",), intro, 96000000, "大使臣武阶",
    )
    duties = Q(entry_id, "阁门祗候具有三重职能：职事官、阁职、武阶")
    state(
        writer, entry_id, "阁门祗候", "宋代", "兼具职事官、阁职、武阶三重职能",
        duties, "记录阁门祗候三重职能。", category="复合职能",
        officer="官职、职名、武阶", sort_order=96000000,
    )
    promotion = Q(entry_id, "至东头供奉官者转阁门祗候，阁门祗候转内殿崇班")
    add_evolution(
        writer, entry_id, "东头供奉官", "阁门祗候", "北宋叙迁制度",
        promotion, 106000000, category="武阶迁转",
        old_event="可转阁门祗候", new_event="由东头供奉官叙迁",
    )
    add_evolution(
        writer, entry_id, "阁门祗候", "内殿崇班", "北宋叙迁制度",
        promotion, 106000000, category="武阶迁转",
        old_event="转内殿崇班", new_event="由阁门祗候叙迁",
    )
    writer.commit()


OLD_SMALL = (
    "东头供奉官", "西头供奉官", "左侍禁", "右侍禁", "左班殿直",
    "右班殿直", "三班奉职", "三班借职",
)
NEW_SMALL = (
    "敦武郎", "修武郎", "从义郎", "秉义郎", "忠训郎", "忠翊郎",
    "成忠郎", "保义郎", "承节郎", "承信郎", "进武校尉", "进义校尉",
)


def extract_small_envoys():
    entry_id = 339
    writer = W(entry_id)
    old_quote = Q(entry_id, "以东、西头供奉官，左、右班殿直，左、右侍禁，三班奉职、三班借职为小使臣")
    group_members(
        writer, entry_id, "小使臣", "北宋通常用法", "东头供奉官以下八阶",
        OLD_SMALL, old_quote, 96000000, "小使臣武阶",
    )
    reform_quote = Q(entry_id, "所谓有“小使臣十二阶”：敦武郎（旧内殿承制）、修武郎（旧内殿崇班）、从义郎（旧东头供奉官）、秉义郎（旧西头供奉官）、忠训郎、忠翊郎、成忠郎、保义郎、承节郎、承信郎、进武校尉（旧三班差使）、进义校尉（旧三班借差）")
    group_members(
        writer, entry_id, "小使臣", "北宋徽宗政和二年九月二十五日",
        "改武选官名诏所列十二阶", NEW_SMALL, reform_quote,
        111201825, "小使臣武阶",
    )
    grades = Q(entry_id, "其官品分别为从八品（东、西头供奉官，从义、秉义郎）、正九品（左、右侍禁，左、右班殿直，忠训、忠翊、成忠、保义郎），从九品（三班奉职、三班借职，承节、承信郎）")
    for title, grade in (
        ("从义郎", "从八品"), ("秉义郎", "从八品"),
        ("忠训郎", "正九品"), ("忠翊郎", "正九品"),
        ("成忠郎", "正九品"), ("保义郎", "正九品"),
        ("承节郎", "从九品"), ("承信郎", "从九品"),
    ):
        add_grade(
            writer, entry_id, title, "南宋官品令", grade, grades,
            112700000, "小使臣武阶",
        )
    writer.commit()

    entry_id = 340
    writer = W(entry_id)
    intro = Q(entry_id, "武阶名。属三班小使臣阶列")
    group_members(
        writer, entry_id, "小使臣", "北宋", "三班小使臣阶列",
        ("东头供奉官",), intro, 96000000, "小使臣武阶",
    )
    origin = Q(entry_id, "唐高宗永徽（650—655）以后，皇帝听政从太极宫移至东北头新建的大明宫，另置从官称“东头供奉官”")
    state(
        writer, entry_id, "东头供奉官", "唐高宗永徽以后（650—655以后）",
        "始置", origin, "建立东头供奉官唐代职源节点。",
        category="前代职源", officer="阶官", sort_order=65000000,
    )
    song = Q(entry_id, "北宋沿置，原为禁中供奉皇帝之职，后遂为武臣迁转之阶")
    state(
        writer, entry_id, "东头供奉官", "北宋", "由禁中供奉职转为武臣迁转阶",
        song, "记录东头供奉官北宋职能变化。", category="小使臣武阶",
        officer="武阶", sort_order=96000000,
    )
    promotion = Q(entry_id, "东头供奉官叙迁，转内殿崇班（或阁门祗候）")
    for new in ("内殿崇班", "阁门祗候"):
        add_evolution(
            writer, entry_id, "东头供奉官", new, "北宋叙迁制度",
            promotion, 106000000, category="武阶迁转",
            old_event=f"叙迁转{new}", new_event="由东头供奉官叙迁",
        )
    grades = Q(entry_id, "北宋前期八品，元丰新制从八品")
    add_grade(writer, entry_id, "东头供奉官", "北宋前期", "八品", grades, 96000000, "小使臣武阶")
    add_grade(writer, entry_id, "东头供奉官", "北宋神宗元丰新制", "从八品", grades, 108000000, "小使臣武阶")
    reform = Q(entry_id, "政和二年九月二十五日，其阶名易为从义郎")
    add_evolution(
        writer, entry_id, "东头供奉官", "从义郎",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="小使臣武阶", old_event="阶名易为从义郎",
        new_event="承接东头供奉官武阶",
    )
    writer.commit()

    entry_id = 341
    writer = W(entry_id)
    intro = Q(entry_id, "武阶名。属三班小使臣阶列。")
    group_members(
        writer, entry_id, "小使臣", "北宋", "三班小使臣阶列",
        ("西头供奉官",), intro, 96000000, "小使臣武阶",
    )
    origin = Q(entry_id, "唐高宗永徽（650—655）以后，大明宫皇帝侍从称东头供奉官，原大内太极宫侍从称西头供奉官")
    state(
        writer, entry_id, "西头供奉官", "唐高宗永徽以后（650—655以后）",
        "始置", origin, "建立西头供奉官唐代职源节点。",
        category="前代职源", officer="阶官", sort_order=65000000,
    )
    promotion = Q(entry_id, "叙迁则转东头供奉官")
    add_evolution(
        writer, entry_id, "西头供奉官", "东头供奉官", "北宋叙迁制度",
        promotion, 106000000, category="武阶迁转",
        old_event="叙迁转东头供奉官", new_event="由西头供奉官叙迁",
    )
    same = Q(entry_id, "余与“东头供奉官”同。")
    add_grade(writer, entry_id, "西头供奉官", "北宋前期", "八品", same, 96000000, "小使臣武阶")
    add_grade(writer, entry_id, "西头供奉官", "北宋神宗元丰新制", "从八品", same, 108000000, "小使臣武阶")
    reform = Q(entry_id, "政和二年九月二十五日，其阶名易为秉义郎")
    add_evolution(
        writer, entry_id, "西头供奉官", "秉义郎",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="小使臣武阶", old_event="阶名易为秉义郎",
        new_event="承接西头供奉官武阶",
    )
    writer.commit()


def main():
    expected = [
        "东绫锦使、副使", "西绫锦使、副使", "东八作使、副使",
        "西八作使、副使", "香药库使、副使", "牛羊使、副使",
        "榷易使、副使", "毡毯使、副使", "鞍辔库使、副使",
        "酒坊使、副使", "法酒库使、副使", "翰林医官使、副使",
        "使臣", "大使臣", "内殿承制", "内殿崇班", "阁门祗候",
        "小使臣", "东头供奉官", "西头供奉官",
    ]
    assert [F[i]["title"] for i in range(322, 342)] == expected
    extract_east_pairs_322_325()
    extract_east_pairs_326_332()
    extract_medical_envoys()
    extract_envoy_groups()
    extract_senior_envoy_members()
    extract_small_envoys()


if __name__ == "__main__":
    main()
