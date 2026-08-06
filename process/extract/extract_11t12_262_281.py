#!/usr/bin/env python3
"""提取 chapter11t12 第262-281条：横行末五阶、诸司使副、东/西班及正使前十阶。"""

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

helper_spec = importlib.util.spec_from_file_location(
    "extract_11t12_082_101_helpers", HERE / "extract_11t12_082_101.py"
)
helpers = importlib.util.module_from_spec(helper_spec)
assert helper_spec.loader is not None
helper_spec.loader.exec_module(helpers)


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


F = {entry_id: load(entry_id) for entry_id in range(262, 282)}
helpers.F = F
helpers.ENTRY_DB = ENTRY_DB
helpers.NEW_SORT = {}

W = helpers.W
Q = helpers.Q
state = helpers.state
relation = helpers.relation


def add_group_members(
    writer,
    entry_id,
    group_title,
    time,
    event,
    quote,
    members,
    sort_order,
    *,
    category,
    group_officer="职官总名",
    member_officer="武阶",
    grade=None,
):
    _, group_tp = state(
        writer, entry_id, group_title, time, event, quote,
        f"据原文建立或复用{group_title}统称节点。",
        category=category, officer=group_officer, grade=grade,
        sort_order=sort_order,
    )
    result = {}
    for title in members:
        _, member_tp = state(
            writer, entry_id, title, time, f"属于{group_title}所指范围", quote,
            f"据原文明列建立或复用{title}实例节点。",
            category=category, officer=member_officer, sort_order=sort_order,
        )
        relation(
            writer, entry_id, group_tp, member_tp, "统称与实例", quote,
            f"原文明示{group_title}包括{title}。",
        )
        result[title] = member_tp
    return group_tp, result


def add_evolution(
    writer,
    entry_id,
    old_title,
    new_title,
    time,
    quote,
    sort_order,
    *,
    category,
    old_event=None,
    new_event=None,
):
    _, old_tp = state(
        writer, entry_id, old_title, time,
        old_event or f"改名或转为{new_title}", quote,
        f"据原文建立或复用{old_title}演变节点。",
        category=category, officer="武阶", sort_order=sort_order,
    )
    _, new_tp = state(
        writer, entry_id, new_title, time,
        new_event or f"承接{old_title}", quote,
        f"据原文建立或复用{new_title}承接节点。",
        category=category, officer="武阶", sort_order=sort_order,
    )
    relation(
        writer, entry_id, old_tp, new_tp, "前后演变", quote,
        f"原文明示{old_title}在{time}演变为{new_title}。",
    )
    return old_tp, new_tp


def add_grade(writer, entry_id, title, time, grade, quote, sort_order, category):
    state(
        writer, entry_id, title, time, f"官品定为{grade}", quote,
        f"据原文建立或复用{title}{time}官品节点。",
        category=category, officer="武阶", grade=grade, sort_order=sort_order,
    )


HORIZONTAL_END = (
    (262, "东上阁门使", "左武大夫", "五代后梁有东上阁门使", "正六品"),
    (263, "客省副使", "中亮郎", None, "从七品"),
    (264, "引进副使", "中卫郎", None, "从七品"),
    (265, "西上阁门副使", "右武郎", "五代十国见置", "从七品"),
    (266, "东上阁门副使", "左武郎", "五代十国见置", "从七品"),
)


def extract_horizontal_end():
    for entry_id, title, successor, origin_needle, grade in HORIZONTAL_END:
        writer = W(entry_id)
        intro = Q(entry_id, "横行武阶名。")
        state(
            writer, entry_id, title, "北宋前期", "属于横行武阶",
            intro, f"据词条定义补证{title}的横行武阶性质。",
            category="横行武阶", officer="武阶", sort_order=96000000,
        )
        if origin_needle:
            origin_quote = Q(entry_id, origin_needle)
            origin_time = "五代后梁" if entry_id == 262 else "五代十国"
            state(
                writer, entry_id, title, origin_time, origin_needle,
                origin_quote, f"建立或复用{title}前代职源节点。",
                category="前代职源", officer="武阶", sort_order=90700000,
            )
        grade_label = "《元祐令》正六品" if entry_id == 262 else (
            "《元祐官品令》从七品"
        )
        grade_quote = Q(entry_id, grade_label)
        add_grade(
            writer, entry_id, title, "北宋哲宗元祐官品令", grade,
            grade_quote, 108600000, "横行武阶",
        )
        reform_quote = Q(
            entry_id, f"政和二年九月二十五日，易阶名为{successor}"
        )
        add_evolution(
            writer, entry_id, title, successor,
            "北宋徽宗政和二年九月二十五日", reform_quote, 111201825,
            category="横行武阶", old_event=f"武阶易为{successor}",
            new_event=f"承接{title}武阶",
        )
        writer.commit()


REGULAR_ENVOYS = (
    "皇城使", "宫苑使", "左骐骥使", "右骐骥使", "内藏库使", "左藏库使",
    "东作坊使", "西作坊使", "庄宅使", "六宅使", "文思使", "内园使",
    "洛苑使", "如京使", "崇仪使", "西京左藏库使", "西京作坊使",
    "东染院使", "西染院使", "礼宾使", "供备库使",
)
DEPUTY_ENVOYS = tuple(title[:-1] + "副使" for title in REGULAR_ENVOYS)
REFORM_DAFU = (
    "武功大夫", "武德大夫", "武显大夫", "武节大夫",
    "武略大夫", "武经大夫", "武义大夫", "武翼大夫",
)
REFORM_LANG = (
    "武功郎", "武德郎", "武显郎", "武节郎",
    "武略郎", "武经郎", "武义郎", "武翼郎",
)


def extract_commissioner_groups():
    entry_id = 267
    writer = W(entry_id)
    old_quote = Q(
        entry_id,
        "北宋前期诸司正使有东班、西班之分，西班构成了武臣迁转官阶序列，共二十一使，分为五等：其一，皇城使；其二，宫苑使、左骐骥使、右骐骥使、内藏库使、左藏库使；其三，东作坊使、西作坊使、庄宅使、六宅使、文思使；其四，内园使、洛苑使、如京使、崇仪使、西京左藏库使；其五，西京作坊使、东染院使、西染院使、礼宾使、供备库使。",
    )
    add_group_members(
        writer, entry_id, "诸司正使", "北宋前期",
        "北宋前期诸司正使二十一使的总称", old_quote,
        REGULAR_ENVOYS, 96000000, category="诸司正使武阶",
    )
    grade_quote = Q(entry_id, "元丰新制、《元祐令》为正七品")
    add_grade(
        writer, entry_id, "诸司正使", "北宋神宗元丰新制", "正七品",
        grade_quote, 108000000, "诸司正使武阶",
    )
    reform_quote = Q(
        entry_id,
        "诸司正使共八阶，即武功大夫、武德大夫、武显大夫、武节大夫、武略大夫、武经大夫、武义大夫、武翼大夫。",
    )
    add_group_members(
        writer, entry_id, "诸司正使", "北宋徽宗政和二年九月二十五日",
        "改武选官名后合并为八阶大夫", reform_quote,
        REFORM_DAFU, 111201825, category="诸司正使武阶",
    )
    writer.commit()

    entry_id = 268
    writer = W(entry_id)
    old_quote = Q(
        entry_id,
        "西班诸司副使，构成了武臣迁转官阶序列，共二十一副使，分为五等：其一，皇城副使；其二，宫苑副使、左骐骥副使，右骐骥副使、内藏库副使、左藏库副使；其三，东作坊副使、西作坊副使、庄宅副使、六宅副使、文思副使；其四，内园副使、洛苑副使、如京副使、崇仪副使、西京左藏库副使；其五，西京作坊副使、东染院副使、西染院副使、礼宾副使、供备库副使。",
    )
    add_group_members(
        writer, entry_id, "诸司副使", "北宋前期",
        "北宋前期诸司副使二十一副使的总称", old_quote,
        DEPUTY_ENVOYS, 96000000, category="诸司副使武阶",
    )
    grade_quote = Q(entry_id, "元丰新制从七品")
    add_grade(
        writer, entry_id, "诸司副使", "北宋神宗元丰新制", "从七品",
        grade_quote, 108000000, "诸司副使武阶",
    )
    reform_quote = Q(
        entry_id,
        "诸司副使合并为八阶，即武功郎、武德郎、武显郎、武节郎、武略郎、武经郎、武义郎、武翼郎",
    )
    add_group_members(
        writer, entry_id, "诸司副使", "北宋徽宗政和二年九月二十五日",
        "改武选官名后合并为八阶郎", reform_quote,
        REFORM_LANG, 111201825, category="诸司副使武阶",
    )
    writer.commit()


WESTERN_BASES = (
    "宫苑", "左骐骥", "右骐骥", "内藏库", "左藏库", "东作坊", "西作坊",
    "庄宅", "六宅", "文思", "内园", "洛苑", "如京", "崇仪", "西京左藏库",
    "西京作坊", "东染院", "西染院", "礼宾", "供备库",
)
WESTERN_MEMBERS = tuple(
    title for base in WESTERN_BASES for title in (f"{base}使", f"{base}副使")
)
EASTERN_BASES = (
    "皇城", "翰林", "尚食", "御厨", "军器库", "仪鸾", "弓箭库", "衣库",
    "东绫锦", "西绫锦", "东八作", "西八作", "牛羊", "香药库", "榷易",
    "毡毯", "鞍辔库", "酒坊", "法酒库", "翰林医官",
)
EASTERN_MEMBERS = tuple(
    title for base in EASTERN_BASES for title in (f"{base}使", f"{base}副使")
)


def extract_east_west_classes():
    entry_id = 270
    writer = W(entry_id)
    quote = Q(
        entry_id,
        "北宋前期，宫苑、左骐骥、右骐骥、内藏库、左藏库、东作坊、西作坊、庄宅、六宅、文思、内园、洛苑、如京、崇仪、西京左藏库、西京作坊、东染院、西染院、礼宾、供备库使、副使，总称西班，用作武阶",
    )
    add_group_members(
        writer, entry_id, "西班", "北宋前期", "西班使、副使武阶总称",
        quote, WESTERN_MEMBERS, 96000000, category="西班武阶",
    )
    writer.commit()

    entry_id = 271
    writer = W(entry_id)
    quote = Q(
        entry_id,
        "北宋前期，皇城、翰林、尚食、御厨、军器库、仪鸾、弓箭库、衣库、东绫锦院、西绫锦院、东八作、西八作、牛羊、香药库、榷易、毡毯、鞍辔库、酒坊、法酒库、翰林医官使、副使，总称东班。",
    )
    add_group_members(
        writer, entry_id, "东班", "北宋前期", "东班使、副使总称",
        quote, EASTERN_MEMBERS, 96000000, category="东班武阶及技术官阶",
    )
    reform_quote = Q(
        entry_id,
        "熙宁后，除皇城使、副进入诸司正使、副使武阶序列外，翰林以下十九名使、副使，并授技术官",
    )
    add_group_members(
        writer, entry_id, "诸司正使", "北宋神宗熙宁以后",
        "皇城使进入诸司正使武阶序列", reform_quote,
        ("皇城使",), 106800000, category="诸司正使武阶",
    )
    add_group_members(
        writer, entry_id, "诸司副使", "北宋神宗熙宁以后",
        "皇城副使进入诸司副使武阶序列", reform_quote,
        ("皇城副使",), 106800000, category="诸司副使武阶",
    )
    add_group_members(
        writer, entry_id, "技术官", "北宋神宗熙宁以后",
        "东班翰林以下十九名使、副使并授技术官", reform_quote,
        EASTERN_MEMBERS[2:], 106800000, category="技术官阶",
        member_officer="技术官阶",
    )
    writer.commit()


def establish_regular_rank(writer, entry_id, title, quote=None):
    quote = quote or Q(entry_id, "武阶名。属诸司正使阶列。")
    state(
        writer, entry_id, title, "北宋前期", "属于诸司正使阶列",
        quote, f"据词条定义补证{title}的诸司正使武阶性质。",
        category="诸司正使武阶", officer="武阶", sort_order=96000000,
    )


def extract_imperial_city_and_old_name():
    entry_id = 272
    writer = W(entry_id)
    intro = Q(entry_id, "武阶名。属诸司正使阶列。")
    establish_regular_rank(writer, entry_id, "皇城使", intro)
    origin = Q(entry_id, "始见于唐德宗建中四年（783）十月")
    state(
        writer, entry_id, "皇城使", "唐德宗建中四年十月", "已见设置",
        origin, "建立皇城使唐代职源节点。",
        category="前代职源", officer="武阶", sort_order=78302000,
    )
    rename = Q(
        entry_id,
        "宋初称武德使（《长编》卷21己丑），太平兴国六年十一月十日改皇城使",
    )
    add_evolution(
        writer, entry_id, "武德使", "皇城使", "北宋太宗太平兴国六年十一月十日",
        rename, 98102210, category="诸司正使武阶",
        old_event="改名为皇城使", new_event="由武德使改名",
    )
    grade = Q(entry_id, "元丰官制、《元祐令》均为正七品")
    add_grade(
        writer, entry_id, "皇城使", "北宋神宗元丰官制", "正七品",
        grade, 108000000, "诸司正使武阶",
    )
    reform = Q(entry_id, "政和二年九月二十五日，其阶名，易为武功大夫")
    add_evolution(
        writer, entry_id, "皇城使", "武功大夫",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="诸司正使武阶", old_event="阶名易为武功大夫",
        new_event="承接皇城使武阶",
    )
    transfer = Q(
        entry_id,
        "治平二年五月一日，诏皇城使改官七年，如曾历边任、有五人（监司或总管）以上保荐者，与转遥郡刺史",
    )
    add_evolution(
        writer, entry_id, "皇城使", "遥郡刺史", "北宋英宗治平二年五月一日",
        transfer, 106501001, category="武阶迁转",
        old_event="符合边任与保荐条件者得转遥郡刺史",
        new_event="符合条件时由皇城使迁转",
    )
    writer.commit()

    entry_id = 273
    writer = W(entry_id)
    duty = Q(entry_id, "宋初置，掌宫城门锁钥、木契等事，按时限启用宫门。")
    state(
        writer, entry_id, "武德使", "宋初",
        "掌宫城门锁钥、木契等事，按时限启用宫门", duty,
        "建立或复用武德使宋初职掌节点。",
        category="皇城门禁官", officer="官职", sort_order=96000000,
    )
    rename = Q(entry_id, "太平兴国六年十一月十日改为皇城使")
    add_evolution(
        writer, entry_id, "武德使", "皇城使", "北宋太宗太平兴国六年十一月十日",
        rename, 98102210, category="诸司正使武阶",
        old_event="改名为皇城使", new_event="由武德使改名",
    )
    writer.commit()


def extract_individual_regular_envoys():
    specs = {
        274: ("宫苑使", "武德大夫", (
            ("唐开元十九年", "唐开元十九年，见置五坊宫苑使", 73100000),
            ("五代后梁", "五代后梁置宫苑使", 90700000),
        ), "政和二年九月二十五日，易阶名为武德大夫"),
        275: ("左骐骥使", "武德大夫", (
            ("北宋太宗雍熙二年", "北宋雍熙二年始置", 98500000),
        ), "政和二年九月二十五日，其阶名易为武德大夫"),
        276: ("右骐骥使", "武德大夫", (), "余同“左骐骥使”"),
        277: ("内藏库使", "武德大夫", (
            ("北宋太宗太平兴国三年十月", "北宋太平兴国三年十月初置库及使名", 97802000),
        ), "政和二年九月二十五日，其阶名易为武德大夫"),
        278: ("左藏库使", "武显大夫", (
            ("唐玄宗朝", "唐玄宗朝，已有殿中侍御史为监左藏库使", 73000000),
            ("五代", "五代有左藏库使", 90700000),
        ), "政和二年九月二十五日，其阶名易为武显大夫"),
        280: ("西作坊使", "武显大夫", (), "余与“东作坊使”同"),
        281: ("庄宅使", "武节大夫", (
            ("唐前期", "始置于唐前期", 65000000),
        ), "政和二年九月二十五日，其阶名易为武节大夫"),
    }
    for entry_id, (title, successor, origins, reform_needle) in specs.items():
        writer = W(entry_id)
        establish_regular_rank(writer, entry_id, title)
        for time, needle, sort_order in origins:
            quote = Q(entry_id, needle)
            state(
                writer, entry_id, title, time, needle, quote,
                f"建立或复用{title}{time}职源节点。",
                category="前代职源" if not time.startswith("北宋") else "诸司正使武阶",
                officer="武阶", sort_order=sort_order,
            )
        if entry_id == 276:
            grade_quote = Q(entry_id, "余同“左骐骥使”")
        elif entry_id == 280:
            grade_quote = Q(entry_id, "余与“东作坊使”同")
        else:
            grade_quote = Q(
                entry_id, "元丰新制、《元祐令》均为正七品"
                if entry_id in (274, 275, 277, 278)
                else "元丰新制、《元祐令》为正七品"
            )
        add_grade(
            writer, entry_id, title, "北宋神宗元丰新制", "正七品",
            grade_quote, 108000000, "诸司正使武阶",
        )
        reform_quote = Q(entry_id, reform_needle)
        add_evolution(
            writer, entry_id, title, successor,
            "北宋徽宗政和二年九月二十五日", reform_quote, 111201825,
            category="诸司正使武阶", old_event=f"阶名易为{successor}",
            new_event=f"承接{title}武阶",
        )
        writer.commit()


def extract_workshop_envoy():
    entry_id = 279
    writer = W(entry_id)
    establish_regular_rank(writer, entry_id, "东作坊使")
    rename = Q(
        entry_id,
        "北宋熙宁三年十二月十二日，改南、北作坊使为东、西作坊使",
    )
    for old_title, new_title in (("南作坊使", "东作坊使"), ("北作坊使", "西作坊使")):
        add_evolution(
            writer, entry_id, old_title, new_title,
            "北宋神宗熙宁三年十二月十二日", rename, 107002412,
            category="诸司正使武阶", old_event=f"改为{new_title}",
            new_event=f"由{old_title}改名",
        )
    grade = Q(entry_id, "元丰新制、《元祐令》为正七品")
    add_grade(
        writer, entry_id, "东作坊使", "北宋神宗元丰新制", "正七品",
        grade, 108000000, "诸司正使武阶",
    )
    reform = Q(entry_id, "政和二年九月二十五日，其阶名易为武显大夫")
    add_evolution(
        writer, entry_id, "东作坊使", "武显大夫",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="诸司正使武阶", old_event="阶名易为武显大夫",
        new_event="承接东作坊使武阶",
    )
    writer.commit()


def main():
    expected = [
        "东上阁门使", "客省副使", "引进副使", "西上阁门副使",
        "东上阁门副使", "诸司正使", "诸司副使", "武功郎", "西班",
        "东班", "皇城使", "武德使", "宫苑使", "左骐骥使", "右骐骥使",
        "内藏库使", "左藏库使", "东作坊使", "西作坊使", "庄宅使",
    ]
    assert [F[i]["title"] for i in range(262, 282)] == expected
    assert F[269]["text"] == "" and F[269]["fields"].get("__status__") == "placeholder"
    assert F[271]["text"].endswith("·皇城使》）。")
    assert F[272]["text"].startswith("武阶名。属诸司正使阶列。")
    extract_horizontal_end()
    extract_commissioner_groups()
    extract_east_west_classes()
    extract_imperial_city_and_old_name()
    extract_individual_regular_envoys()
    extract_workshop_envoy()


if __name__ == "__main__":
    main()
