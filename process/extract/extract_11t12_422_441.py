#!/usr/bin/env python3
"""提取 chapter11t12 第422-441条：无品副尉、班官与政和内侍阶。"""

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
    "extract_11t12_402_421_helpers", HERE / "extract_11t12_402_421.py"
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


F = {entry_id: load(entry_id) for entry_id in range(422, 442)}


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


def sentence(entry_id, start_text):
    text = F[entry_id]["text"]
    start = text.index(start_text)
    return text[start:text.index("。", start) + 1]


UNGRADED = {
    422: ("下班祗应", "殿侍", "第三", "北宋徽宗政和二年九月二十五日", 111201825),
    423: ("进武副尉", "大将", "第四", "北宋徽宗政和二年九月二十五日", 111201825),
    424: ("进义副尉", "正名军将", "第五", "北宋徽宗政和二年九月二十五日", 111201825),
    425: ("守阙进义副尉", "守阙军将", "第六", "北宋徽宗政和二年九月二十五日", 111201825),
    426: ("进勇副尉", "公据", "第七", "南宋高宗绍兴五年", 113500000),
    427: ("守阙进勇副尉", "甲头", "第八阶，即末", "南宋高宗绍兴五年", 113500000),
}


def extract_ungraded_deputies():
    for entry_id, (title, old_title, ordinal, origin_time, order) in UNGRADED.items():
        writer = W(entry_id)
        intro = Q(entry_id, "武阶名。属无品八阶列。")
        state(
            writer, entry_id, title, origin_time, "列入无品武阶",
            intro, f"记录{title}属于无品八阶序列。",
            category="无品武阶", officer="武阶", sort_order=order,
        )
        origin_start = (
            "北宋政和二年九月二十五日" if entry_id <= 425 else "南宋绍兴五年"
        )
        origin = sentence(entry_id, origin_start)
        add_evolution(
            writer, entry_id, old_title, title, origin_time, origin, order,
            category="无品武阶", old_event=f"阶名改为{title}",
            new_event=f"承接{old_title}武阶",
        )
        rank_needle = f"为无品武阶{ordinal}阶"
        rank_quote = Q(entry_id, rank_needle)
        state(
            writer, entry_id, title, "南宋高宗绍兴厘定",
            f"列为无品武阶{ordinal}阶", rank_quote,
            f"记录{title}绍兴厘定后的无品武阶序位。",
            category="绍兴无品武阶", officer="武阶", sort_order=113100000,
        )
        writer.commit()

    entry_id = 428
    writer = W(entry_id)
    northern = Q(
        entry_id,
        "①北宋政和二年九月二十五日，改军、大将为进武副尉等诸副尉，副尉为其通称。",
    )
    group_members(
        writer, entry_id, "副尉", "北宋徽宗政和二年九月二十五日",
        "政和改名后诸副尉的通称",
        ("进武副尉", "进义副尉", "守阙进义副尉"),
        northern, 111201825, "无品武阶",
    )
    southern = Q(
        entry_id,
        "②南宋绍兴五年改公据、甲头为进勇副尉、守阙进勇副尉后，副尉为进武副尉至守阙进勇副尉五阶的通称。",
    )
    group_members(
        writer, entry_id, "副尉", "南宋高宗绍兴五年",
        "无品副尉五阶的通称",
        ("进武副尉", "进义副尉", "守阙进义副尉", "进勇副尉", "守阙进勇副尉"),
        southern, 113500000, "无品武阶",
    )
    restore = Q(entry_id, "淳熙元年十二月十三日，诏军功副尉复隶兵部")
    state(
        writer, entry_id, "副尉", "南宋孝宗淳熙元年十二月十三日",
        "军功副尉复隶兵部", restore, "记录军功副尉选隶变化。",
        category="无品武阶", officer="职官总名", sort_order=117401213,
    )
    writer.commit()


BAN_MEMBERS = ("昭宣使", "宣政使", "宣庆使", "景福殿使", "延福宫使")
BAN_GRADES = {
    "昭宣使": "正六品", "宣政使": "正六品", "宣庆使": "正六品",
    "景福殿使": "从五品", "延福宫使": "从五品",
}


def preserve_as_additional(writer, entry_id, title, quote):
    state(
        writer, entry_id, title, "南宋", "作为内侍加官官称继续使用",
        quote, f"记录{title}阶名改易后仍作为加官名沿用。",
        category="内侍加官", officer="加官", sort_order=112700000,
    )


def extract_ban_officials():
    entry_id = 429
    writer = W(entry_id)
    start = Q(entry_id, "北宋太宗淳化四年置昭宣使，是为置班官之始")
    state(
        writer, entry_id, "班官", "北宋太宗淳化四年", "始置班官",
        start, "以昭宣使始置记录班官类别起点。",
        category="内侍班官", officer="职官总名", sort_order=99300000,
    )
    members = Q(
        entry_id,
        "班官包括昭宣使（正六品）、宣政使（正六品）、宣庆使（正六品）、景福殿使（从五品）、延福宫使（从五品）",
    )
    group_members(
        writer, entry_id, "班官", "宋代", "内侍班官五阶",
        BAN_MEMBERS, members, 96000000, "内侍班官",
    )
    for title, grade in BAN_GRADES.items():
        add_grade(
            writer, entry_id, title, "宋代", grade, members,
            96000000, "内侍班官",
        )
    exceptional = Q(entry_id, "属非常调，内侍官带阶皇城使以上须特旨除授、迁转")
    state(
        writer, entry_id, "班官", "宋代", "非常调，须特旨除授迁转",
        exceptional, "记录班官除授与迁转限制。",
        category="内侍班官", officer="职官总名", sort_order=96000000,
    )
    reform = Q(
        entry_id,
        "政和二年九月二十五日，班官纳入武选阶，而易其名：改延福宫使为正侍大夫、景福殿使为中侍大夫、宣庆使为中亮大夫、昭宣使为拱卫大夫。",
    )
    state(
        writer, entry_id, "班官", "北宋徽宗政和二年九月二十五日",
        "班官纳入武选阶并改易阶名", reform,
        "记录班官政和纳入武选阶的整体改制。",
        category="内侍班官", officer="职官总名", sort_order=111201825,
    )
    for old_title, new_title in (
        ("延福宫使", "正侍大夫"), ("景福殿使", "中侍大夫"),
        ("宣庆使", "中亮大夫"), ("昭宣使", "拱卫大夫"),
    ):
        add_evolution(
            writer, entry_id, old_title, new_title,
            "北宋徽宗政和二年九月二十五日", reform, 111201825,
            category="内侍班官", old_event=f"阶名改易为{new_title}",
            new_event=f"承接{old_title}阶名",
        )
    alias = F[entry_id]["fields"]["别名"]
    state(
        writer, entry_id, "班官", "宋代", "又称诸司使", alias,
        "记录辞典所列班官别名，不另建别名实体。",
        category="内侍班官", officer="职官总名", sort_order=96000000,
    )
    writer.commit()

    specs = {
        430: ("延福宫使", "北宋仁宗明道元年", "始置", "正侍大夫", "从五品", 103200000),
        431: ("景福殿使", "北宋真宗大中祥符五年", "特置", "中侍大夫", "从五品", 101200000),
        432: ("宣庆使", "北宋真宗大中祥符元年十二月十八日", "特置", "中亮大夫", "正六品", 100801218),
        433: ("宣政使", "北宋太宗淳化五年", "另立", "中卫大夫", None, 99400000),
        434: ("昭宣使", "北宋太宗淳化四年二月", "始置", "拱卫大夫", "正六品", 99302000),
    }
    for entry_id, spec in specs.items():
        title, origin_time, origin_event, successor, grade, order = spec
        writer = W(entry_id)
        intro = Q(entry_id, "阶官、加官名。属内侍班官。")
        group_members(
            writer, entry_id, "班官", "宋代", "内侍班官五阶",
            (title,), intro, 96000000, "内侍班官",
        )
        if entry_id == 430:
            origin = Q(entry_id, "北宋明道元年置")
        elif entry_id == 431:
            origin = sentence(entry_id, "北宋大中祥符五年")
        elif entry_id == 432:
            origin = sentence(entry_id, "北宋真宗大中祥符元年十二月十八日")
        elif entry_id == 433:
            origin = sentence(entry_id, "北宋太宗淳化五年")
        else:
            origin = Q(entry_id, "北宋淳化四年二月始置")
        state(
            writer, entry_id, title, origin_time, origin_event, origin,
            f"记录{title}的始置节点。", category="内侍班官",
            officer="阶官、加官", sort_order=order,
        )
        if grade:
            add_grade(
                writer, entry_id, title, "宋代", grade,
                Q(entry_id, grade), 96000000, "内侍班官",
            )
        reform_start = "政和二年九月二十五日" if entry_id in (430, 431) else "政和二年九月"
        reform = sentence(entry_id, reform_start)
        reform_time = (
            "北宋徽宗政和二年九月二十五日"
            if entry_id in (430, 431) else "北宋徽宗政和二年九月"
        )
        add_evolution(
            writer, entry_id, title, successor, reform_time, reform,
            111201825 if entry_id in (430, 431) else 111209000,
            category="内侍班官", old_event=f"阶名改易为{successor}",
            new_event=f"承接{title}阶名",
        )
        continuation = Q(entry_id, "迄南宋不废")
        preserve_as_additional(writer, entry_id, title, continuation)
        writer.commit()


INTERNAL_ELEVEN = (
    "供奉官", "左侍禁", "右侍禁", "左班殿直", "右班殿直", "黄门",
    "祗候侍禁", "祗候殿直", "祗候黄门内品", "祗候内品", "贴祗候内品",
)


def extract_internal_eunuch_ranks():
    entry_id = 435
    writer = W(entry_id)
    old_system = Q(
        entry_id,
        "北宋内侍叙迁阶官，初无定格，多出于用例，或以本官为阶，又有不同层次之分。",
    )
    state(
        writer, entry_id, "内侍阶官", "北宋徽宗政和二年以前",
        "内侍叙迁阶官初无定格", old_system,
        "建立内侍阶官政和改制前的制度节点。",
        category="内侍阶官", officer="职官总名", sort_order=96000000,
    )
    divisions = Q(
        entry_id,
        "入内侍省、内侍省内东、西头供奉官以下，各分内侍班、祗候班。",
    )
    group_members(
        writer, entry_id, "内侍阶官", "北宋徽宗政和二年以前",
        "两省各分内侍班与祗候班",
        ("入内内侍省内侍班", "入内内侍省祗候班", "内侍省内侍班", "内侍省祗候班"),
        divisions, 96000000, "内侍阶官",
    )
    ban = Q(entry_id, "皇城使以上特旨除昭宣使等班官")
    group_members(
        writer, entry_id, "内侍阶官", "北宋徽宗政和二年以前",
        "皇城使以上可特旨除班官", ("班官",), ban,
        96000000, "内侍阶官",
    )
    yuanfeng = Q(entry_id, "元丰改官制，言者请并省与改换内侍官名，未果")
    state(
        writer, entry_id, "内侍阶官", "北宋神宗元丰改制",
        "并省与改换内侍官名之议未果", yuanfeng,
        "记录元丰时内侍官名改革未实施。",
        category="内侍阶官", officer="职官总名", sort_order=108000000,
    )
    reform = Q(
        entry_id,
        "徽宗政和二年九月二十五日，改定供奉官以下至贴祗候内品内侍官新名十一阶。",
    )
    state(
        writer, entry_id, "内侍阶官", "北宋徽宗政和二年九月二十五日",
        "改定内侍官新名十一阶", reform,
        "记录政和内侍阶改制。", category="政和内侍十一阶",
        officer="职官总名", sort_order=111201825,
    )
    restore = Q(entry_id, "靖康元年罢，仍复旧称")
    state(
        writer, entry_id, "内侍阶官", "北宋钦宗靖康元年",
        "罢政和新名并复旧称", restore,
        "记录靖康罢政和内侍新名。", category="内侍阶官",
        officer="职官总名", sort_order=112600000,
    )
    writer.commit()

    entry_id = 436
    writer = W(entry_id)
    list_quote = Q(
        entry_id,
        "北宋徽宗政和二年九月二十五日，改定入内内侍省、内侍省供奉官以下阶官十一阶：供奉官、左侍禁、右侍禁、左班殿直、右班殿直、黄门、祗候侍禁、祗候殿直、祗候黄门内品、祗候内品、贴祗候内品。",
    )
    group_members(
        writer, entry_id, "内侍阶官", "北宋徽宗政和二年九月二十五日",
        "改定政和内侍十一阶", ("政和供奉官以下内侍阶",),
        list_quote, 111201825, "政和内侍十一阶",
    )
    group_members(
        writer, entry_id, "政和供奉官以下内侍阶",
        "北宋徽宗政和二年九月二十五日", "政和内侍十一阶",
        INTERNAL_ELEVEN, list_quote, 111201825, "政和内侍十一阶",
    )
    restore = Q(entry_id, "靖康元年罢，复旧称")
    state(
        writer, entry_id, "政和供奉官以下内侍阶", "北宋钦宗靖康元年",
        "罢十一阶并复旧称", restore, "记录政和内侍十一阶废止。",
        category="政和内侍十一阶", officer="职官总名", sort_order=112600000,
    )
    writer.commit()

    specs = {
        437: ("供奉官", ("入内内侍省内东头供奉官", "内侍省内东头供奉官")),
        438: ("左侍禁", ("入内内侍省内西头供奉官", "内侍省内西头供奉官")),
        439: ("右侍禁", ("入内内侍省内侍殿头", "内侍省内侍殿头")),
        440: ("左班殿直", ("入内内侍省内侍高品", "内侍省内侍高品")),
        441: ("右班殿直", ("入内内侍省内侍高班", "内侍省内侍高班")),
    }
    for entry_id, (title, old_titles) in specs.items():
        writer = W(entry_id)
        intro = Q(entry_id, "阶官名。属政和内侍十一阶列。")
        group_members(
            writer, entry_id, "政和供奉官以下内侍阶",
            "北宋徽宗政和二年九月二十五日", "政和内侍十一阶",
            (title,), intro, 111201825, "政和内侍十一阶",
        )
        origin = sentence(entry_id, "北宋政和二年九月二十五日")
        for old_title in old_titles:
            add_evolution(
                writer, entry_id, old_title, title,
                "北宋徽宗政和二年九月二十五日", origin, 111201825,
                category="政和内侍十一阶", old_event=f"阶名改为{title}",
                new_event=f"承接{old_title}阶名",
            )
        if entry_id == 437:
            promotion = Q(entry_id, "由此阶遇泛恩或磨勘许转入武选阶郎、大夫阶列")
            state(
                writer, entry_id, title, "北宋徽宗政和二年以后",
                "遇泛恩或磨勘可转入武选阶郎、大夫阶列", promotion,
                "记录供奉官向武选阶迁转的制度，不虚构单一目标阶。",
                category="内侍迁转", officer="内侍阶官", sort_order=111201825,
            )
        restore = sentence(entry_id, "靖康元年罢")
        for old_title in old_titles:
            add_evolution(
                writer, entry_id, title, old_title, "北宋钦宗靖康元年",
                restore, 112600000, category="政和内侍十一阶",
                old_event=f"罢新名并复{old_title}旧称",
                new_event=f"复用{old_title}旧称",
            )
        writer.commit()


def main():
    expected = [
        "下班祗应", "进武副尉", "进义副尉", "守阙进义副尉", "进勇副尉",
        "守阙进勇副尉", "副尉", "班官", "延福宫使", "景福殿使",
        "宣庆使", "宣政使", "昭宣使", "内侍阶官", "政和供奉官以下内侍阶",
        "供奉官", "左侍禁", "右侍禁", "左班殿直", "右班殿直",
    ]
    assert [F[i]["title"] for i in range(422, 442)] == expected
    extract_ungraded_deputies()
    extract_ban_officials()
    extract_internal_eunuch_ranks()


if __name__ == "__main__":
    main()
