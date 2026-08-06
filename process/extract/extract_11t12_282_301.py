#!/usr/bin/env python3
"""提取 chapter11t12 第282-301条：诸司正使后十一阶及诸司副使前八阶。"""

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


F = {entry_id: load(entry_id) for entry_id in range(282, 302)}
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


def establish_member(writer, entry_id, title, group_title, category, quote):
    _, group_tp = state(
        writer, entry_id, group_title, "北宋前期", f"{group_title}武阶范围",
        quote, f"据本条建立或复用{group_title}统称节点。",
        category=category, officer="职官总名", sort_order=96000000,
    )
    _, member_tp = state(
        writer, entry_id, title, "北宋前期", f"属于{group_title}阶列",
        quote, f"据本条建立或复用{title}北宋前期武阶节点。",
        category=category, officer="武阶", sort_order=96000000,
    )
    relation(
        writer, entry_id, group_tp, member_tp, "统称与实例", quote,
        f"本条明示{title}属于{group_title}阶列。",
    )
    return member_tp


def regular_intro(entry_id):
    if entry_id in (291,):
        return Q(entry_id, "武阶名。属诸司正使阶列。位次于东染院使。余与“东染院使”同。")
    return Q(entry_id, "武阶名。属诸司正使阶列。")


def deputy_intro(entry_id):
    if entry_id == 298:
        return Q(entry_id, "武阶名。位次于左骐骥副使。\n余与“左骐骥副使”同。")
    return Q(entry_id, "武阶名。属诸司副使阶列。")


def extract_regular_envoys():
    specs = {
        282: {
            "title": "六宅使", "new": "武节大夫",
            "origins": (("唐玄宗时", "唐玄宗时置十王宅使、六王宅使", 72000000),),
        },
        283: {
            "title": "文思使", "new": "武节大夫",
            "origins": (
                ("五代后梁", "五代后梁有文思院使", 90700000),
                ("北宋太宗太平兴国三年", "北宋太平兴国三年置文思院，亦有文思使", 97800000),
            ),
        },
        284: {
            "title": "内园使", "new": "武略大夫",
            "origins": (
                ("唐武则天时", "唐武则天时始置", 69000000),
                ("五代后梁", "五代后梁有内园栽接使", 90700000),
            ),
        },
        285: {
            "title": "洛苑使", "new": "武略大夫",
            "origins": (
                ("唐代", "唐官", 70000000),
                ("五代后梁", "五代后梁亦有洛苑使", 90700000),
            ),
        },
        286: {
            "title": "如京使", "new": "武略大夫",
            "origins": (("唐文宗开成三年九月", "唐文宗开成三年（838）九月已有如京使", 83801800),),
        },
        287: {
            "title": "崇仪使", "new": "武略大夫", "origins": (),
        },
        288: {
            "title": "西京左藏库使", "new": "武经大夫",
            "origins": (("北宋真宗咸平三年四月六日", "北宋真宗咸平三年四月六日，见置“西京左藏库使刘绍荣”之名，疑始置于宋初", 100000806),),
        },
        289: {
            "title": "西京作坊使", "new": "武义大夫",
            "origins": (("北宋太祖开宝六年七月", "宋太祖开宝六年七月见置", 97301400),),
        },
        290: {
            "title": "东染院使", "new": "武义大夫", "origins": (),
        },
        291: {
            "title": "西染院使", "new": "武义大夫", "origins": (),
        },
        292: {
            "title": "礼宾使", "new": "武义大夫",
            "origins": (
                ("唐玄宗天宝十三年三月二十七日", "唐天宝十三年三月二十七日，鸿胪寺已有礼宾院，疑已置使名", 75400627),
                ("唐代宗永泰二年八月二十一日", "代宗永泰二年八月二十一日见鱼朝恩充礼宾使", 76601621),
            ),
        },
        293: {
            "title": "供备库使", "new": "武翼大夫",
            "origins": (
                ("五代后梁", "五代后梁有武备库使", 90700000),
                ("北宋太祖乾德二年十二月十五日", "宋太祖乾德二年十二月十五日见有“供备库使麹彦饶”", 96402415),
            ),
        },
    }
    for entry_id, spec in specs.items():
        writer = W(entry_id)
        title = spec["title"]
        intro = regular_intro(entry_id)
        establish_member(
            writer, entry_id, title, "诸司正使", "诸司正使武阶", intro
        )
        for time, needle, sort_order in spec["origins"]:
            quote = Q(entry_id, needle)
            state(
                writer, entry_id, title, time, needle, quote,
                f"建立或复用{title}{time}职源节点。",
                category="前代职源" if not time.startswith("北宋") else "诸司正使武阶",
                officer="武阶", sort_order=sort_order,
            )

        if entry_id == 287:
            rename = Q(
                entry_id,
                "北宋太平兴国五年正月七日，改闲厩使为崇仪使",
            )
            add_evolution(
                writer, entry_id, "闲厩使", "崇仪使",
                "北宋太宗太平兴国五年正月七日", rename, 98000207,
                category="诸司正使武阶", old_event="改名为崇仪使",
                new_event="由闲厩使改名",
            )
        elif entry_id == 290:
            split_quote = Q(
                entry_id,
                "宋太祖开宝九年七月已分染院为东、西染院，各置使名",
            )
            for title2 in ("东染院使", "西染院使"):
                state(
                    writer, entry_id, title2, "北宋太祖开宝九年七月",
                    "染院分为东、西染院时设置使名", split_quote,
                    f"建立或复用{title2}开宝九年始见节点。",
                    category="诸司正使武阶", officer="武阶", sort_order=97601400,
                )

        if entry_id == 291:
            grade_quote = Q(entry_id, "余与“东染院使”同")
        else:
            grade_quote = Q(entry_id, "元丰新制、《元祐令》为正七品")
        add_grade(
            writer, entry_id, title, "北宋神宗元丰新制", "正七品",
            grade_quote, 108000000, "诸司正使武阶",
        )
        if entry_id == 291:
            reform_quote = Q(entry_id, "余与“东染院使”同")
        else:
            reform_quote = Q(
                entry_id,
                f"政和二年九月二十五日，其阶名易为{spec['new']}",
            )
        add_evolution(
            writer, entry_id, title, spec["new"],
            "北宋徽宗政和二年九月二十五日", reform_quote, 111201825,
            category="诸司正使武阶", old_event=f"阶名易为{spec['new']}",
            new_event=f"承接{title}武阶",
        )
        writer.commit()


def extract_imperial_city_deputy():
    entry_id = 294
    writer = W(entry_id)
    intro = deputy_intro(entry_id)
    establish_member(
        writer, entry_id, "皇城副使", "诸司副使", "诸司副使武阶", intro
    )
    grade = Q(entry_id, "元丰新制从七品")
    add_grade(
        writer, entry_id, "皇城副使", "北宋神宗元丰新制", "从七品",
        grade, 108000000, "诸司副使武阶",
    )
    reform = Q(entry_id, "政和二年九月二十五日，其阶名易为武功郎")
    add_evolution(
        writer, entry_id, "皇城副使", "武功郎",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="诸司副使武阶", old_event="阶名易为武功郎",
        new_event="承接皇城副使武阶",
    )
    writer.commit()

    entry_id = 295
    writer = W(entry_id)
    duty = Q(entry_id, "宋初置，内侍充。为武德使副贰。")
    state(
        writer, entry_id, "武德副使", "宋初", "由内侍充任，为武德使副贰",
        duty, "建立或复用武德副使宋初职掌节点。",
        category="皇城门禁官", officer="官职", sort_order=96000000,
    )
    rename = Q(
        entry_id,
        "太平兴国六年十一月十日，随改司名为皇城，称皇城副使",
    )
    add_evolution(
        writer, entry_id, "武德副使", "皇城副使",
        "北宋太宗太平兴国六年十一月十日", rename, 98102210,
        category="诸司副使武阶", old_event="改称皇城副使",
        new_event="由武德副使改名",
    )
    writer.commit()


def extract_deputy_envoys():
    specs = {
        296: ("宫苑副使", "武德郎"),
        297: ("左骐骥副使", "武德郎"),
        298: ("右骐骥副使", "武德郎"),
        299: ("内藏库副使", "武德郎"),
        300: ("左藏库副使", "武显郎"),
        301: ("东作坊副使", "武显郎"),
    }
    for entry_id, (title, successor) in specs.items():
        writer = W(entry_id)
        intro = deputy_intro(entry_id)
        establish_member(
            writer, entry_id, title, "诸司副使", "诸司副使武阶", intro
        )
        if entry_id == 298:
            grade_quote = Q(entry_id, "余与“左骐骥副使”同")
            reform_quote = grade_quote
        else:
            grade_quote = Q(entry_id, "元丰新制从七品")
            reform_quote = Q(
                entry_id,
                f"政和二年九月二十五日，其阶名易为{successor}",
            )
        add_grade(
            writer, entry_id, title, "北宋神宗元丰新制", "从七品",
            grade_quote, 108000000, "诸司副使武阶",
        )
        add_evolution(
            writer, entry_id, title, successor,
            "北宋徽宗政和二年九月二十五日", reform_quote, 111201825,
            category="诸司副使武阶", old_event=f"阶名易为{successor}",
            new_event=f"承接{title}武阶",
        )
        writer.commit()


def main():
    expected = [
        "六宅使", "文思使", "内园使", "洛苑使", "如京使", "崇仪使",
        "西京左藏库使", "西京作坊使", "东染院使", "西染院使", "礼宾使",
        "供备库使", "皇城副使", "武德副使", "宫苑副使", "左骐骥副使",
        "右骐骥副使", "内藏库副使", "左藏库副使", "东作坊副使",
    ]
    assert [F[i]["title"] for i in range(282, 302)] == expected
    extract_regular_envoys()
    extract_imperial_city_deputy()
    extract_deputy_envoys()


if __name__ == "__main__":
    main()
