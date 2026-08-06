#!/usr/bin/env python3
"""提取 chapter11t12 第342-361条：三班小使臣、殿侍及大将。"""

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


F = {339: load(339), **{entry_id: load(entry_id) for entry_id in range(342, 362)}}
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
institution_state = base.institution_state
group_members = base.group_members


def attach_institution(writer, entry_id, institution, time, event, post, quote, order):
    _, institution_tp = institution_state(
        writer, entry_id, institution, time, event, quote,
        f"建立或复用{institution}{time}机构节点。", order,
    )
    _, post_tp = state(
        writer, entry_id, post, time, f"隶属{institution}", quote,
        f"建立或复用{post}在{institution}的编制节点。",
        category="机构职官", officer="官职", sort_order=order,
    )
    relation(
        writer, entry_id, institution_tp, post_tp, "编制隶属", quote,
        f"原文明示{post}在{time}隶属或由{institution}管领。",
    )
    return institution_tp, post_tp


def add_small_member(writer, entry_id, title, quote, *, time="北宋"):
    group_members(
        writer, entry_id, "小使臣", time, "三班小使臣阶列",
        (title,), quote, 96000000, "小使臣武阶",
    )


def extract_collective_titles():
    entry_id = 342
    writer = W(entry_id)
    quote = Q(entry_id, "东、西头供奉官通称。")
    group_members(
        writer, entry_id, "供奉官", "宋代", "东、西头供奉官通称",
        ("东头供奉官", "西头供奉官"), quote, 96000000, "小使臣武阶",
    )
    writer.commit()

    entry_id = 345
    writer = W(entry_id)
    quote = Q(entry_id, "左、右侍禁通称。")
    group_members(
        writer, entry_id, "侍禁", "宋代", "左、右侍禁通称",
        ("左侍禁", "右侍禁"), quote, 96000000, "小使臣武阶",
    )
    writer.commit()

    entry_id = 348
    writer = W(entry_id)
    quote = Q(entry_id, "左、右班殿直通称。")
    group_members(
        writer, entry_id, "殿直", "宋代", "左、右班殿直通称",
        ("左班殿直", "右班殿直"), quote, 96000000, "小使臣武阶",
    )
    organization = Q(entry_id, "国初，以供奉官、殿直、承旨为三班，隶宣徽院")
    _, three_tp = state(
        writer, entry_id, "三班", "宋初", "供奉官、殿直、承旨三班总称",
        organization, "建立三班宋初统称节点。", category="三班使臣",
        officer="职官总名", sort_order=96000000,
    )
    for title in ("供奉官", "殿直", "承旨"):
        _, member_tp = state(
            writer, entry_id, title, "宋初", "属于三班", organization,
            f"建立或复用{title}宋初三班实例节点。", category="三班使臣",
            officer="职官总名", sort_order=96000000,
        )
        relation(
            writer, entry_id, three_tp, member_tp, "统称与实例", organization,
            f"原文明示{title}为宋初三班之一。",
        )
    _, ministry_tp = institution_state(
        writer, entry_id, "宣徽院", "宋初", "管辖三班", organization,
        "建立或复用宣徽院宋初管辖节点。", 96000000,
    )
    relation(
        writer, entry_id, ministry_tp, three_tp, "编制隶属", organization,
        "原文明示宋初三班隶宣徽院。",
    )
    writer.commit()


def extract_guards():
    entry_id = 343
    writer = W(entry_id)
    intro = Q(entry_id, "武阶名。属三班小使臣阶列")
    add_small_member(writer, entry_id, "左侍禁", intro)
    origin = Q(entry_id, "北宋淳化二年正月十四日始置")
    state(
        writer, entry_id, "左侍禁", "北宋太宗淳化二年正月十四日",
        "始置", origin, "建立左侍禁始置节点。", category="小使臣武阶",
        officer="武阶", sort_order=99100214,
    )
    promotion = Q(entry_id, "左侍禁叙迁，转西头供奉官")
    add_evolution(
        writer, entry_id, "左侍禁", "西头供奉官", "北宋叙迁制度",
        promotion, 106000000, category="武阶迁转",
        old_event="叙迁转西头供奉官", new_event="由左侍禁叙迁",
    )
    early_grade = Q(entry_id, "宋前期八品")
    yuanfeng_grade = Q(entry_id, "元丰官制定为正九品")
    add_grade(writer, entry_id, "左侍禁", "宋前期", "八品", early_grade, 96000000, "小使臣武阶")
    add_grade(writer, entry_id, "左侍禁", "北宋神宗元丰官制", "正九品", yuanfeng_grade, 108000000, "小使臣武阶")
    reform = Q(entry_id, "政和二年九月二十五日，其阶名易为忠训郎")
    add_evolution(
        writer, entry_id, "左侍禁", "忠训郎",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="小使臣武阶", old_event="阶名易为忠训郎",
        new_event="承接左侍禁武阶",
    )
    writer.commit()

    entry_id = 344
    writer = W(entry_id)
    intro = Q(entry_id, "武阶名。属三班小使臣阶列")
    add_small_member(writer, entry_id, "右侍禁", intro)
    promotion = Q(entry_id, "叙迁转左侍禁")
    add_evolution(
        writer, entry_id, "右侍禁", "左侍禁", "北宋叙迁制度",
        promotion, 106000000, category="武阶迁转",
        old_event="叙迁转左侍禁", new_event="由右侍禁叙迁",
    )
    cross_reference = Q(entry_id, "余参“左侍禁”条。")
    add_grade(writer, entry_id, "右侍禁", "宋前期", "八品", cross_reference, 96000000, "小使臣武阶")
    add_grade(writer, entry_id, "右侍禁", "北宋神宗元丰官制", "正九品", cross_reference, 108000000, "小使臣武阶")
    reform = Q(entry_id, "政和二年九月二十五日，其阶名易为忠翊郎")
    add_evolution(
        writer, entry_id, "右侍禁", "忠翊郎",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="小使臣武阶", old_event="阶名易为忠翊郎",
        new_event="承接右侍禁武阶",
    )
    writer.commit()


def extract_palace_attendants():
    entry_id = 346
    writer = W(entry_id)
    intro = Q(entry_id, "武阶名。属三班小使臣阶列")
    add_small_member(writer, entry_id, "左班殿直", intro)
    origin = Q(entry_id, "“殿直”之官始见于五代后梁开平二年七月敕")
    state(
        writer, entry_id, "殿直", "五代后梁开平二年七月", "始见设置",
        origin, "建立殿直五代职源节点。", category="前代职源",
        officer="阶官", sort_order=90801400,
    )
    song = Q(entry_id, "北宋初沿置，但为三班之一，称左、右班殿直")
    group_members(
        writer, entry_id, "殿直", "北宋初", "分称左、右班殿直",
        ("左班殿直", "右班殿直"), song, 96000000, "小使臣武阶",
    )
    promotion = Q(entry_id, "其叙迁，转右侍禁")
    add_evolution(
        writer, entry_id, "左班殿直", "右侍禁", "北宋叙迁制度",
        promotion, 106000000, category="武阶迁转",
        old_event="叙迁转右侍禁", new_event="由左班殿直叙迁",
    )
    grade = Q(entry_id, "元丰官制为正九品")
    add_grade(writer, entry_id, "左班殿直", "北宋神宗元丰官制", "正九品", grade, 108000000, "小使臣武阶")
    reform = Q(entry_id, "政和二年九月二十五日，其阶名易为成忠郎")
    add_evolution(
        writer, entry_id, "左班殿直", "成忠郎",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="小使臣武阶", old_event="阶名易为成忠郎",
        new_event="承接左班殿直武阶",
    )
    writer.commit()

    entry_id = 347
    writer = W(entry_id)
    intro = Q(entry_id, "武阶名。属三班小使臣阶列。")
    add_small_member(writer, entry_id, "右班殿直", intro)
    promotion = Q(entry_id, "叙迁转左班殿直")
    add_evolution(
        writer, entry_id, "右班殿直", "左班殿直", "北宋叙迁制度",
        promotion, 106000000, category="武阶迁转",
        old_event="叙迁转左班殿直", new_event="由右班殿直叙迁",
    )
    cross_reference = Q(entry_id, "余参“左班殿直”条。")
    add_grade(writer, entry_id, "右班殿直", "北宋神宗元丰官制", "正九品", cross_reference, 108000000, "小使臣武阶")
    reform = Q(entry_id, "政和二年九月二十五日，其阶名易为保义郎")
    add_evolution(
        writer, entry_id, "右班殿直", "保义郎",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="小使臣武阶", old_event="阶名易为保义郎",
        new_event="承接右班殿直武阶",
    )
    writer.commit()


def extract_three_classes_posts():
    entry_id = 349
    writer = W(entry_id)
    intro = Q(entry_id, "武阶名。属三班小使臣阶列。")
    add_small_member(writer, entry_id, "三班奉职", intro)
    rename = Q(entry_id, "北宋太宗淳化二年正月十四日，改殿前承旨为三班奉职")
    add_evolution(
        writer, entry_id, "殿前承旨", "三班奉职",
        "北宋太宗淳化二年正月十四日", rename, 99100214,
        category="三班使臣", old_event="改为三班奉职",
        new_event="由殿前承旨改名",
    )
    affiliation = Q(entry_id, "属三班院使臣")
    attach_institution(
        writer, entry_id, "三班院", "北宋太宗淳化二年正月十四日",
        "设置使臣阶列", "三班奉职", affiliation, 99100214,
    )
    promotion = Q(entry_id, "其叙迁，由三班奉职转右班殿直")
    add_evolution(
        writer, entry_id, "三班奉职", "右班殿直", "北宋叙迁制度",
        promotion, 106000000, category="武阶迁转",
        old_event="叙迁转右班殿直", new_event="由三班奉职叙迁",
    )
    grade = Q(entry_id, "元丰新官制、《元祐令》均为从九品")
    add_grade(writer, entry_id, "三班奉职", "北宋神宗元丰新官制", "从九品", grade, 108000000, "小使臣武阶")
    reform = Q(entry_id, "政和二年九月二十五日，其阶名易为承节郎")
    add_evolution(
        writer, entry_id, "三班奉职", "承节郎",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="小使臣武阶", old_event="阶名易为承节郎",
        new_event="承接三班奉职武阶",
    )
    writer.commit()

    entry_id = 350
    writer = W(entry_id)
    intro = Q(entry_id, "武阶名。属三班小使臣阶列。")
    add_small_member(writer, entry_id, "三班借职", intro)
    rename = Q(entry_id, "北宋太宗淳化二年正月十四日，改借职承旨为三班借职")
    add_evolution(
        writer, entry_id, "借职承旨", "三班借职",
        "北宋太宗淳化二年正月十四日", rename, 99100214,
        category="三班使臣", old_event="改为三班借职",
        new_event="由借职承旨改名",
    )
    affiliation = Q(entry_id, "属三班院使臣")
    attach_institution(
        writer, entry_id, "三班院", "北宋太宗淳化二年正月十四日",
        "设置使臣阶列", "三班借职", affiliation, 99100214,
    )
    promotion = Q(entry_id, "其叙迁，转三班奉职")
    add_evolution(
        writer, entry_id, "三班借职", "三班奉职", "北宋叙迁制度",
        promotion, 106000000, category="武阶迁转",
        old_event="叙迁转三班奉职", new_event="由三班借职叙迁",
    )
    grade = Q(entry_id, "元丰官制，《元祐令》均为从九品")
    add_grade(writer, entry_id, "三班借职", "北宋神宗元丰官制", "从九品", grade, 108000000, "小使臣武阶")
    writer.commit()

    # 第350条未重录改名句；第339条“小使臣”总表明示旧三班借职改承信郎。
    writer = W(339)
    reform = Q(339, "承信郎（旧三班借职）")
    add_evolution(
        writer, 339, "三班借职", "承信郎",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="小使臣武阶", old_event="阶名易为承信郎",
        new_event="承接三班借职武阶",
    )
    writer.commit()


def extract_old_attendants():
    entry_id = 351
    writer = W(entry_id)
    duty = Q(entry_id, "宋初为三班祗应使臣，多以贵族子弟、豪门、侥幸者充")
    state(
        writer, entry_id, "殿前承旨", "宋初", "三班祗应使臣",
        duty, "建立殿前承旨宋初职能节点。", category="三班使臣",
        officer="官职", sort_order=96000000,
    )
    rename = Q(entry_id, "淳化二年正月十四日，改名为三班奉职")
    add_evolution(
        writer, entry_id, "殿前承旨", "三班奉职",
        "北宋太宗淳化二年正月十四日", rename, 99100214,
        category="三班使臣", old_event="改名为三班奉职",
        new_event="由殿前承旨改名",
    )
    writer.commit()

    entry_id = 352
    writer = W(entry_id)
    duty = Q(entry_id, "宋初为三班祗应使臣。端拱中置")
    state(
        writer, entry_id, "借职承旨", "北宋太宗端拱中", "设置，为三班祗应使臣",
        duty, "建立借职承旨端拱年间节点。", category="三班使臣",
        officer="官职", sort_order=98800000,
    )
    rename = Q(entry_id, "淳化二年正月十四日，改为三班借职")
    add_evolution(
        writer, entry_id, "借职承旨", "三班借职",
        "北宋太宗淳化二年正月十四日", rename, 99100214,
        category="三班使臣", old_event="改为三班借职",
        new_event="由借职承旨改名",
    )
    writer.commit()

    entry_id = 353
    writer = W(entry_id)
    origin = Q(entry_id, "宋初禁中祗应使臣。以武举有材武、试弓箭中选者充")
    state(
        writer, entry_id, "文班承旨", "宋初", "禁中祗应使臣，由武举中选者充",
        origin, "建立文班承旨宋初节点。", category="禁中祗应使臣",
        officer="官职", sort_order=96000000,
    )
    abolition = Q(entry_id, "太宗端拱年间，因任职者迁秩或去世，后不复除人，遂废")
    state(
        writer, entry_id, "文班承旨", "北宋太宗端拱年间", "不复除人，遂废",
        abolition, "记录文班承旨端拱年间废止。", category="禁中祗应使臣",
        officer="官职", sort_order=98800000,
    )
    writer.commit()


def extract_unranked_small_envoys():
    for entry_id, old, new in (
        (354, "三班差使", "进武校尉"),
        (355, "三班借差", "进义校尉"),
    ):
        writer = W(entry_id)
        intro = Q(entry_id, "无品武阶名。")
        state(
            writer, entry_id, old, "北宋前期", "无品武阶",
            intro, f"建立{old}北宋前期武阶节点。", category="无品武阶",
            officer="武阶", sort_order=96000000,
        )
        reform = Q(entry_id, f"政和二年九月二十五日，其阶名易为{new}")
        add_evolution(
            writer, entry_id, old, new,
            "北宋徽宗政和二年九月二十五日", reform, 111201825,
            category="无品武阶", old_event=f"阶名易为{new}",
            new_event=f"承接{old}武阶",
        )
        writer.commit()


def extract_low_attendants():
    entry_id = 356
    writer = W(entry_id)
    intro = Q(entry_id, "无品武阶名。北宋前期，作为武阶殿侍，有茶酒班殿侍、下班殿侍、披带班殿侍")
    group_members(
        writer, entry_id, "殿侍", "北宋前期", "武阶殿侍通称",
        ("茶酒班殿侍", "下班殿侍", "披带班殿侍"), intro,
        96000000, "无品武阶",
    )
    reform = Q(entry_id, "政和二年九月二十五日，改其阶名为下班祗应")
    add_evolution(
        writer, entry_id, "殿侍", "下班祗应",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="无品武阶", old_event="阶名改为下班祗应",
        new_event="承接殿侍武阶",
    )
    writer.commit()

    for entry_id, title in (
        (357, "茶酒班殿侍"), (358, "披带班殿侍"), (359, "下班殿侍")
    ):
        writer = W(entry_id)
        intro = Q(entry_id, "无品武阶名。殿侍之一。")
        group_members(
            writer, entry_id, "殿侍", "北宋前期", "武阶殿侍通称",
            (title,), intro, 96000000, "无品武阶",
        )
        writer.commit()


def extract_generals():
    entry_id = 360
    writer = W(entry_id)
    intro = Q(entry_id, "无品武阶名。")
    state(
        writer, entry_id, "大将", "北宋前期", "无品武阶",
        intro, "建立大将北宋前期武阶节点。", category="无品武阶",
        officer="武阶", sort_order=96000000,
    )
    origin = Q(entry_id, "唐末，藩镇置邸于京师，派大将领之，称“上都留后”，是即大将之名始于唐")
    state(
        writer, entry_id, "大将", "唐末", "藩镇派大将领京师邸，称上都留后",
        origin, "建立大将唐末职源节点。", category="前代职源",
        officer="官职", sort_order=88000000,
    )
    organization = Q(entry_id, "宋初，大将归隶三司为衙职，并承五代之制，用三司大将领粮料院职事，开宝六年罢")
    for institution, event in (
        ("三司", "大将归隶三司为衙职"),
        ("粮料院", "由三司大将领职事"),
    ):
        attach_institution(
            writer, entry_id, institution, "宋初至北宋太祖开宝六年",
            event, "大将", organization, 96000000,
        )
    rank = Q(entry_id, "此大将、军将，无疑兼具阶官职能。如酬赏改转，迁殿侍")
    for title in ("大将", "军将"):
        state(
            writer, entry_id, title, "宋代", "兼具阶官职能", rank,
            f"记录{title}兼具阶官职能。", category="无品武阶",
            officer="武阶", sort_order=96000000,
        )
    add_evolution(
        writer, entry_id, "大将", "殿侍", "宋代酬赏改转制度",
        rank, 106000000, category="武阶迁转",
        old_event="酬赏改转可迁殿侍", new_event="由大将酬赏改转",
    )
    reform = Q(entry_id, "政和二年九月二十五日，其阶名易为为进武副尉")
    add_evolution(
        writer, entry_id, "大将", "进武副尉",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="无品武阶", old_event="阶名易为进武副尉",
        new_event="承接大将武阶",
    )
    writer.commit()

    entry_id = 361
    writer = W(entry_id)
    intro = Q(entry_id, "无品武阶名。位次于大将。正名军将即军将，与守阙军将相对而言。")
    group_members(
        writer, entry_id, "军将", "宋代", "正名军将与守阙军将的总称",
        ("正名军将", "守阙军将"), intro, 96000000, "无品武阶",
    )
    reform = Q(entry_id, "政和二年九月二十五日，其阶名易为进义副尉")
    add_evolution(
        writer, entry_id, "正名军将", "进义副尉",
        "北宋徽宗政和二年九月二十五日", reform, 111201825,
        category="无品武阶", old_event="阶名易为进义副尉",
        new_event="承接正名军将武阶",
    )
    writer.commit()


def main():
    expected = [
        "供奉官", "左侍禁", "右侍禁", "侍禁", "左班殿直", "右班殿直",
        "殿直", "三班奉职", "三班借职", "殿前承旨", "借职承旨",
        "文班承旨", "三班差使", "三班借差", "殿侍", "茶酒班殿侍",
        "披带班殿侍", "下班殿侍", "大将", "正名军将",
    ]
    assert [F[i]["title"] for i in range(342, 362)] == expected
    extract_collective_titles()
    extract_guards()
    extract_palace_attendants()
    extract_three_classes_posts()
    extract_old_attendants()
    extract_unranked_small_envoys()
    extract_low_attendants()
    extract_generals()


if __name__ == "__main__":
    main()
