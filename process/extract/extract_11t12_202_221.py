#!/usr/bin/env python3
"""提取 chapter11t12 第202-221条：选人阶官末阶、职官统称及武阶总制。"""

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

prior_spec = importlib.util.spec_from_file_location(
    "extract_11t12_182_201_helpers", HERE / "extract_11t12_182_201.py"
)
prior = importlib.util.module_from_spec(prior_spec)
assert prior_spec.loader is not None
prior_spec.loader.exec_module(prior)


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


F = {entry_id: load(entry_id) for entry_id in range(202, 222)}
prior.F = F
prior.helpers.F = F
prior.helpers.helpers.F = F
prior.helpers.helpers.helpers.F = F
prior.helpers.helpers.helpers.ENTRY_DB = ENTRY_DB
prior.helpers.helpers.helpers.NEW_SORT = {}

W = prior.W
Q = prior.Q
state = prior.state
relation = prior.relation


def field_quote(entry_id, field, needle):
    value = F[entry_id]["fields"].get(field, "")
    assert needle in value, (entry_id, field, needle)
    return needle


def classification(
    entry_id,
    group_title,
    group_time,
    group_event,
    quote,
    members,
    group_sort,
    *,
    category="选人阶官统称",
):
    """建立总称节点及总称→实例关系；members 为 (title,time,sort) 列表。"""
    writer = W(entry_id)
    _, group_tp = state(
        writer, entry_id, group_title, group_time, group_event, quote,
        f"据原文建立或复用{group_title}统称节点。",
        category=category, officer="职官总名", sort_order=group_sort,
    )
    for member_title, member_time, member_sort in members:
        _, member_tp = state(
            writer, entry_id, member_title, member_time,
            f"属于{group_title}所指范围", quote,
            f"据原文建立或复用{member_title}作为{group_title}实例的节点。",
            category=category, officer="选人阶官", sort_order=member_sort,
        )
        relation(
            writer, entry_id, group_tp, member_tp, "统称与实例", quote,
            f"原文明示{group_title}包括{member_title}。",
        )
    writer.commit()


def evolve(
    writer,
    entry_id,
    old_titles,
    new_title,
    time,
    quote,
    sort_order,
    *,
    category="选人阶官阶序",
    grade=None,
):
    _, new_tp = state(
        writer, entry_id, new_title, time,
        f"由{'、'.join(old_titles)}改名", quote,
        f"据原文建立或复用{new_title}{time}节点。",
        category=category, officer="选人阶官", grade=grade,
        sort_order=sort_order,
    )
    for old_title in old_titles:
        _, old_tp = state(
            writer, entry_id, old_title, time, f"改名为{new_title}", quote,
            f"据原文建立或复用{old_title}{time}改名终结节点。",
            category="选人阶官旧阶终结", officer="选人阶官",
            sort_order=sort_order,
        )
        relation(
            writer, entry_id, old_tp, new_tp, "前后演变", quote,
            f"原文明示{old_title}在{time}改名为{new_title}。",
        )
    return new_tp


LAST_OLD_TIER = (
    "三京军巡判官", "司理参军", "司户参军", "司法参军",
    "户曹参军", "法曹参军", "县主簿", "县尉",
)


def extract_last_old_tier():
    # #202 只是目录占位，原书无独立正文；不得由占位条伪造事实。
    assert not F[202]["text"] and F[202]["fields"].get("__status__") == "placeholder"

    entry_id = 203
    writer = W(entry_id)
    quote = Q(
        entry_id,
        "选人阶名。北宋前期选人四等七阶之第四等（判司簿尉）第七阶（资）。",
    )
    for title in LAST_OLD_TIER:
        state(
            writer, entry_id, title, "北宋前期",
            "列选人四等七阶之第四等第七阶", quote,
            f"据并列正式词头拆建或复用{title}北宋前期选人阶节点。",
            category="选人四等七阶第四等第七阶", officer="选人阶官",
            sort_order=96000000,
        )
    change_quote = Q(
        entry_id,
        "崇宁二年九月二十五日改名为将仕郎，政和六年十一月，又改名为迪功郎",
    )
    evolve(
        writer, entry_id, LAST_OLD_TIER, "将仕郎",
        "北宋徽宗崇宁二年九月二十五日", change_quote, 110301825,
        grade="从九品",
    )
    evolve(
        writer, entry_id, ("将仕郎",), "迪功郎",
        "北宋徽宗政和六年十一月", change_quote, 111602200,
        grade="从九品",
    )
    writer.commit()


TWO_COMMISSIONERS = (
    "三京府判官", "留守司判官", "节度判官", "观察判官",
    "节度掌书记", "观察支使", "防御判官", "团练判官",
    "京府推官", "留守司推官", "节度推官", "观察推官", "军事判官",
)
JUNIOR_OFFICES = ("防御推官", "团练推官", "军事推官", "军判官", "监判官")
COUNTY_RECORDS = ("县令", "录事参军", "试衔知县令", "知录事参军")


def extract_old_classifications():
    quote = Q(
        204,
        "职官总名。北宋前期选人四等之第一等（含选人七阶中之第一、二、三阶）",
    )
    classification(
        204, "两使职官", "北宋前期", "选人四等之第一等，含前三阶",
        quote, [(title, "北宋前期", 96000000) for title in TWO_COMMISSIONERS],
        96000000,
    )
    quote = Q(204, "崇宁二年，选人一等三阶分别改为承直、儒林、文林郎。")
    classification(
        204, "两使职官", "北宋徽宗崇宁二年",
        "原三阶分别改称承直郎、儒林郎、文林郎",
        quote,
        [(title, "北宋徽宗崇宁二年", 110300000)
         for title in ("承直郎", "儒林郎", "文林郎")],
        110300000,
    )

    quote = Q(
        205,
        "职官总名。北宋前期选人四等之第二等（含选人第四阶），即防御、团练、军事推官与军、监判官阶。",
    )
    classification(
        205, "初等职官", "北宋前期", "选人四等之第二等，含第四阶",
        quote, [(title, "北宋前期", 96000000) for title in JUNIOR_OFFICES],
        96000000,
    )
    quote = Q(205, "崇宁二年九月后改名为从事郎。")
    classification(
        205, "初等职官", "北宋徽宗崇宁二年九月以后",
        "原第四阶改称从事郎", quote,
        [("从事郎", "北宋徽宗崇宁二年九月以后", 110301800)],
        110301800,
    )

    quote = Q(206, "两使职官、初等职官的通称。或称幕职官。")
    members = [
        ("两使职官", "北宋前期", 96000000),
        ("初等职官", "北宋前期", 96000000),
    ]
    classification(
        206, "职官", "北宋前期", "两使职官、初等职官的通称",
        quote, members, 96000000,
    )
    classification(
        206, "幕职官", "北宋前期", "职官的别称，范围同两使职官与初等职官",
        quote, members, 96000000,
    )
    quote = Q(206, "崇宁后改名为承直郎、儒林郎、文林郎、从事郎。")
    classification(
        206, "职官", "北宋徽宗崇宁二年以后",
        "崇宁后指承直郎至从事郎四阶", quote,
        [(title, "北宋徽宗崇宁二年以后", 110300000)
         for title in ("承直郎", "儒林郎", "文林郎", "从事郎")],
        110300000,
    )

    quote = Q(
        207,
        "职官总名。北宋前期选人第三等（含选人第五、六阶），即县令、录事参军与试衔知县令、知录事参军二阶。",
    )
    classification(
        207, "令录", "北宋前期", "选人第三等，含第五、六阶",
        quote, [(title, "北宋前期", 96000000) for title in COUNTY_RECORDS],
        96000000,
    )
    quote = Q(207, "崇宁二年改名为通仕郎、登仕郎二阶")
    classification(
        207, "令录", "北宋徽宗崇宁二年",
        "第五、六阶改称通仕郎、登仕郎", quote,
        [(title, "北宋徽宗崇宁二年", 110300000)
         for title in ("通仕郎", "登仕郎")],
        110300000,
    )
    quote = Q(207, "政和六年分别改为从政郎、修职郎二阶。")
    classification(
        207, "令录", "北宋徽宗政和六年",
        "分别改称从政郎、修职郎", quote,
        [(title, "北宋徽宗政和六年", 111600000)
         for title in ("从政郎", "修职郎")],
        111600000,
    )
    quote = Q(207, "应称知令录者，系修职郎。")
    classification(
        207, "知令录", "南宋", "修职郎的官称",
        quote, [("修职郎", "南宋", 112700000)], 112700000,
    )

    quote = Q(208, "职官（含两使职官、初等职官）与令录的合称。")
    classification(
        208, "职令", "北宋前期", "职官与令录的合称", quote,
        [
            ("职官", "北宋前期", 96000000),
            ("令录", "北宋前期", 96000000),
        ],
        96000000,
    )

    quote = Q(
        209,
        "职官总名。北宋前期选人四等之第四等（含选人第七阶），即三京军巡判官、司理、司户、司法、法曹，县主簿、县尉阶。",
    )
    classification(
        209, "判司簿尉", "北宋前期", "选人四等之第四等，含第七阶",
        quote, [(title, "北宋前期", 96000000) for title in LAST_OLD_TIER],
        96000000,
    )
    quote = Q(209, "崇宁二年改称将仕郎、政和六年改名迪功郎。")
    classification(
        209, "判司簿尉", "北宋徽宗崇宁二年",
        "第七阶改称将仕郎", quote,
        [("将仕郎", "北宋徽宗崇宁二年", 110300000)], 110300000,
    )
    classification(
        209, "判司簿尉", "北宋徽宗政和六年",
        "第七阶改称迪功郎", quote,
        [("迪功郎", "北宋徽宗政和六年", 111600000)], 111600000,
    )


EXACT_CHONGNING = {
    210: (("三京府判官", "留守司判官", "节度判官", "观察判官"), "承直郎", "从八品"),
    211: (("节度掌书记", "观察支使", "防御判官", "团练判官"), "儒林郎", "从八品"),
    212: (("京府推官", "留守司推官", "节度推官", "观察推官", "军事判官"), "文林郎", "从八品"),
    213: (("防御推官", "团练推官", "军事推官", "军判官", "监判官"), "从事郎", "从八品"),
}


def extract_exact_new_ranks():
    for entry_id, (old_titles, new_title, grade) in EXACT_CHONGNING.items():
        writer = W(entry_id)
        quote = F[entry_id]["text"]
        assert "北宋徽宗崇宁二年九月二十五日" in quote
        evolve(
            writer, entry_id, old_titles, new_title,
            "北宋徽宗崇宁二年九月二十五日", quote, 110301825,
            grade=grade,
        )
        writer.commit()

    quote = Q(
        214,
        "北宋崇宁后选人承直郎、儒林郎、文林郎、从事郎四阶之通称",
    )
    classification(
        214, "职官", "北宋徽宗崇宁二年以后",
        "承直郎、儒林郎、文林郎、从事郎四阶的通称", quote,
        [(title, "北宋徽宗崇宁二年以后", 110300000)
         for title in ("承直郎", "儒林郎", "文林郎", "从事郎")],
        110300000,
    )

    for entry_id, old_title, new_title, grade in (
        (215, "通仕郎", "从政郎", "从八品"),
        (216, "登仕郎", "修职郎", "从八品"),
        (217, "将仕郎", "迪功郎", "从九品"),
    ):
        writer = W(entry_id)
        quote = Q(
            entry_id,
            f"北宋徽宗政和六年十一月，由{old_title}阶改名",
        )
        evolve(
            writer, entry_id, (old_title,), new_title,
            "北宋徽宗政和六年十一月", quote, 111602200,
            grade=grade,
        )
        writer.commit()


def extract_reused_low_ranks():
    entry_id = 218
    writer = W(entry_id)
    quote = Q(
        entry_id,
        "北宋徽宗崇宁二年九月二十五日，由县令、录事参军阶改名，为崇宁选人新阶第五阶",
    )
    evolve(
        writer, entry_id, ("县令", "录事参军"), "通仕郎",
        "北宋徽宗崇宁二年九月二十五日", quote, 110301825,
        grade="从八品",
    )
    quote = Q(
        entry_id,
        "徽宗政和六年十一月，改通仕郎阶为从政郎，而以假承事郎、假承奉郎为通仕郎。",
    )
    evolve(
        writer, entry_id, ("通仕郎",), "从政郎",
        "北宋徽宗政和六年十一月", quote, 111602200, grade="从八品",
    )
    evolve(
        writer, entry_id, ("假承事郎", "假承奉郎"), "通仕郎",
        "北宋徽宗政和六年十一月", quote, 111602200, grade="从八品",
    )
    writer.commit()

    entry_id = 219
    writer = W(entry_id)
    quote = Q(
        entry_id,
        "北宋徽宗崇宁二年九月二十五日，由试衔知县、知录事参军改名，为崇宁选人新阶之第六阶",
    )
    evolve(
        writer, entry_id, ("试衔知县令", "知录事参军"), "登仕郎",
        "北宋徽宗崇宁二年九月二十五日", quote, 110301825,
        grade="从八品",
    )
    quote = Q(
        entry_id,
        "政和六年十一月，改登仕郎阶为修职郎，易假承务郎为登仕郎",
    )
    evolve(
        writer, entry_id, ("登仕郎",), "修职郎",
        "北宋徽宗政和六年十一月", quote, 111602200, grade="从八品",
    )
    evolve(
        writer, entry_id, ("假承务郎",), "登仕郎",
        "北宋徽宗政和六年十一月", quote, 111602200, grade="从八品",
    )
    writer.commit()

    entry_id = 220
    writer = W(entry_id)
    quote = Q(
        entry_id,
        "北宋徽宗崇宁二年九月二十五日，由判司簿尉阶改名，属崇宁新阶第七阶",
    )
    # 此处“判司簿尉”是总称本身，不再虚构为八个旧阶各自的第二组改名事实。
    evolve(
        writer, entry_id, ("判司簿尉",), "将仕郎",
        "北宋徽宗崇宁二年九月二十五日", quote, 110301825,
        grade="从九品",
    )
    quote = Q(
        entry_id,
        "政和六年十一月，改将仕郎为迪功郎，易假将仕郎为将仕郎",
    )
    evolve(
        writer, entry_id, ("将仕郎",), "迪功郎",
        "北宋徽宗政和六年十一月", quote, 111602200, grade="从九品",
    )
    evolve(
        writer, entry_id, ("假将仕郎",), "将仕郎",
        "北宋徽宗政和六年十一月", quote, 111602200, grade="从九品",
    )
    writer.commit()


def extract_military_rank_system():
    entry_id = 221
    writer = W(entry_id)
    intro = Q(
        entry_id,
        "职官总名。宋代武官官阶，以政和二年九月二十五日颁《改武选官名诏》为界，分前期旧名号与后期新名号两种。",
    )
    _, general_tp = state(
        writer, entry_id, "武阶", "宋代",
        "宋代武官官阶总名，以政和二年改名诏分前后两制", intro,
        "据武阶总制条建立武阶总称节点。",
        category="武官阶官总称", officer="职官总名",
    )
    # 别名证据只追加到武阶总称节点，不另造别名实体或伪实例关系。
    for needle in (
        "武选。《群书考索·后集》卷20《官制门·武阶类》",
        "右阶、右列。《挥麈三录》卷3",
        "右选、西阶。《彝斋文编·从伯故丽水丞赵公墓志铭》",
    ):
        alias_quote = field_quote(entry_id, "别名", needle)
        state(
            writer, entry_id, "武阶", "宋代",
            "宋代武官官阶总名，以政和二年改名诏分前后两制", alias_quote,
            "以原书别名字段为武阶总称节点补充别名证据。",
            category="武官阶官总称", officer="职官总名",
        )

    old_quote = Q(
        entry_id,
        "旧名号沿唐制，包括正任官（自节度使至刺史）、遥郡官（自遥郡节度观察留后至遥郡刺史）、横行（自内客省使至西上阁门副使）、班官（自延福宫使至昭宣使）、诸司正使（自皇城使至供备库使）、诸司副使（自皇城副使至供备库副使）、大使臣（内殿承制、内殿崇班、阁门祗候）、小使臣（自东头供奉官至三班借职），以及殿侍以下非品官、无磨勘转官法的杂阶",
    )
    old_time = "北宋徽宗政和二年九月二十五日以前"
    _, old_tp = state(
        writer, entry_id, "武阶", old_time,
        "政和改武选官名以前沿用唐制旧名号", old_quote,
        "建立政和改名前武阶制度节点。",
        category="政和前武阶旧制", officer="职官总名", sort_order=111201825,
    )
    for title in (
        "正任官", "遥郡官", "横行", "班官", "诸司正使", "诸司副使",
        "大使臣", "小使臣", "杂阶",
    ):
        _, member_tp = state(
            writer, entry_id, title, old_time, "属于政和前武阶旧名号类别",
            old_quote, f"据武阶条建立或复用{title}旧制类别节点。",
            category="政和前武阶旧制", officer="职官总名", sort_order=111201825,
        )
        relation(
            writer, entry_id, old_tp, member_tp, "统称与实例", old_quote,
            f"原文明示武阶旧制包括{title}。",
        )

    reform_quote = Q(
        entry_id,
        "政和二年九月二十五日，武阶易以新名，太尉为武阶之首",
    )
    reform_time = "北宋徽宗政和二年九月二十五日"
    _, reform_tp = state(
        writer, entry_id, "武阶", reform_time,
        "颁《改武选官名诏》，武阶改用新名，太尉居首", reform_quote,
        "建立政和二年武阶新制节点。",
        category="政和武阶新制", officer="职官总名", sort_order=111201825,
    )
    relation(
        writer, entry_id, old_tp, reform_tp, "前后演变", reform_quote,
        "政和二年九月二十五日武阶由旧名号改用新名号。",
    )

    ranked_quote = Q(
        entry_id,
        "总计入品武阶，自太尉至承信郎为五十二阶",
    )
    _, ranked_tp = state(
        writer, entry_id, "入品武阶", reform_time,
        "自太尉至承信郎共五十二阶", ranked_quote,
        "建立政和以后入品武阶类别节点。",
        category="政和武阶新制", officer="职官总名", sort_order=111201825,
    )
    relation(
        writer, entry_id, reform_tp, ranked_tp, "统称与实例", ranked_quote,
        "武阶新制包括入品武阶五十二阶。",
    )
    for title in ("太尉", "承信郎"):
        _, member_tp = state(
            writer, entry_id, title, reform_time, "作为入品武阶序列边界",
            ranked_quote, f"据原文建立或复用{title}入品武阶边界节点。",
            category="入品武阶五十二阶", officer="武阶", sort_order=111201825,
        )
        relation(
            writer, entry_id, ranked_tp, member_tp, "统称与实例", ranked_quote,
            f"原文明示入品武阶序列以{title}为边界。",
        )

    unranked_quote = Q(
        entry_id,
        "不包括自进武校尉至下班祗应不入品六阶，南宋时不入品杂阶又增进勇副尉、守阙进勇副尉二阶",
    )
    _, unranked_tp = state(
        writer, entry_id, "不入品武阶", reform_time,
        "政和时自进武校尉至下班祗应共六阶", unranked_quote,
        "建立政和以后不入品武阶类别节点。",
        category="政和武阶新制", officer="职官总名", sort_order=111201825,
    )
    relation(
        writer, entry_id, reform_tp, unranked_tp, "统称与实例", unranked_quote,
        "武阶新制另含不入品武阶。",
    )
    for title in ("进武校尉", "下班祗应"):
        _, member_tp = state(
            writer, entry_id, title, reform_time, "作为不入品武阶序列边界",
            unranked_quote, f"据原文建立或复用{title}不入品武阶边界节点。",
            category="不入品武阶六阶", officer="武阶", sort_order=111201825,
        )
        relation(
            writer, entry_id, unranked_tp, member_tp, "统称与实例", unranked_quote,
            f"原文明示不入品武阶序列以{title}为边界。",
        )

    additions_quote = Q(
        entry_id,
        "政和二年十一月至政和六年十一月，先后又增拱卫郎等十一阶",
    )
    state(
        writer, entry_id, "武阶", "北宋徽宗政和二年十一月至政和六年十一月",
        "先后增置拱卫郎等十一阶", additions_quote,
        "建立政和二年至六年武阶增置节点。",
        category="政和武阶新制", officer="职官总名", sort_order=111202200,
    )

    shaoxing_quote = Q(
        entry_id,
        "绍兴厘正武阶序列，凡郎皆移置大夫之下，自太尉至承信郎共为五十二阶；自进武校尉至守阙进勇副尉共八阶，总六十阶。",
    )
    shaoxing_time = "南宋高宗绍兴年间"
    _, shaoxing_tp = state(
        writer, entry_id, "武阶", shaoxing_time,
        "厘正序列，郎阶移置大夫之下，入品与不入品合计六十阶",
        shaoxing_quote, "建立绍兴厘正武阶制度节点。",
        category="绍兴武阶六十阶", officer="职官总名", sort_order=113100000,
    )
    for group_title, event, endpoints in (
        ("入品武阶", "自太尉至承信郎共五十二阶", ("太尉", "承信郎")),
        ("不入品武阶", "自进武校尉至守阙进勇副尉共八阶",
         ("进武校尉", "守阙进勇副尉")),
    ):
        _, group_tp = state(
            writer, entry_id, group_title, shaoxing_time, event, shaoxing_quote,
            f"建立绍兴厘正后的{group_title}节点。",
            category="绍兴武阶六十阶", officer="职官总名", sort_order=113100000,
        )
        relation(
            writer, entry_id, shaoxing_tp, group_tp, "统称与实例", shaoxing_quote,
            f"绍兴厘正后的武阶包括{group_title}。",
        )
        for title in endpoints:
            _, endpoint_tp = state(
                writer, entry_id, title, shaoxing_time,
                f"作为{group_title}序列边界", shaoxing_quote,
                f"据原文建立或复用{title}绍兴武阶边界节点。",
                category="绍兴武阶六十阶", officer="武阶", sort_order=113100000,
            )
            relation(
                writer, entry_id, group_tp, endpoint_tp, "统称与实例",
                shaoxing_quote, f"原文明示{group_title}序列以{title}为边界。",
            )
    writer.commit()


def main():
    expected = [
        "知令录",
        "三京府军巡判官，司理、司户、司法、户曹、法曹参军，县主簿、县尉",
        "两使职官", "初等职官", "职官", "令录", "职令", "判司簿尉",
        "承直郎", "儒林郎", "文林郎", "从事郎", "职官", "从政郎",
        "修职郎", "迪功郎", "通仕郎", "登仕郎", "将仕郎", "武阶",
    ]
    assert [F[i]["title"] for i in range(202, 222)] == expected
    assert "简称与别名" in F[217]["fields"] and "\n简称与别名 " not in F[217]["text"]
    assert "永乐大典" in F[216]["fields"]["简称与别名"]
    extract_last_old_tier()
    extract_old_classifications()
    extract_exact_new_ranks()
    extract_reused_low_ranks()
    extract_military_rank_system()


if __name__ == "__main__":
    main()
