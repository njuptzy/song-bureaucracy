#!/usr/bin/env python3
"""提取 chapter11t12 第182-201条：寄禄官末五阶、郎官及选人阶官。"""

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
    "extract_11t12_162_181_helpers", HERE / "extract_11t12_162_181.py"
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


F = {entry_id: load(entry_id) for entry_id in range(182, 202)}
helpers.F = F
helpers.helpers.F = F
helpers.helpers.helpers.F = F
helpers.helpers.helpers.ENTRY_DB = ENTRY_DB
helpers.helpers.helpers.NEW_SORT = {}

W = helpers.W
Q = helpers.Q
state = helpers.state
relation = helpers.relation
stipend_member = helpers.stipend_member
add_split = helpers.add_split
add_merge = helpers.add_merge


RANK_SPECS = {
    182: {
        "new": "宣德郎", "olds": ("著作佐郎", "大理寺丞"),
        "grade": "从八品", "ordinal": "第二十六",
        "quote": "寄禄官名。北宋元丰三年九月，由秘书省著作佐郎、大理寺丞阶改。为文臣京朝官三十阶中第二十六阶。",
    },
    186: {
        "new": "宣义郎", "olds": ("光禄寺丞", "卫尉寺丞", "将作监丞"),
        "grade": "从八品", "ordinal": "第二十七",
        "quote": "寄禄官名。北宋神宗元丰三年九月，由光禄、卫尉寺丞、将作监丞阶改。为文臣京朝官寄禄官三十阶之第二十七阶。",
    },
    188: {
        "new": "承事郎", "olds": ("大理评事",),
        "grade": "正九品", "ordinal": "第二十八",
        "quote": "寄禄官名。北宋神宗元丰三年九月，由大理评事阶改。为文臣京朝官寄禄官三十阶之第二十八阶。",
    },
    190: {
        "new": "承奉郎", "olds": ("太常寺太祝", "奉礼郎"),
        "grade": "正九品", "ordinal": "第二十九",
        "quote": "寄禄官名。北宋神宗元丰三年九月，由太常寺太祝、奉礼郎阶改。为文臣京朝官寄禄官三十阶之第二十九阶。",
    },
    192: {
        "new": "承务郎", "olds": ("秘书省校书郎", "正字", "将作监主簿"),
        "grade": "从九品", "ordinal": "第三十",
        "quote": "寄禄官名。北宋神宗元丰三年九月，由秘书省校书郎、正字、将作监主簿改。为文臣京朝官寄禄官三十阶之第三十阶，即末阶。",
    },
}


def extract_yuanfeng_ranks():
    for entry_id, spec in RANK_SPECS.items():
        writer = W(entry_id)
        quote = Q(entry_id, spec["quote"])
        old_summary = "、".join(spec["olds"])
        _, new_tp = state(
            writer, entry_id, spec["new"], "北宋神宗元丰三年九月",
            f"由{old_summary}改名，为寄禄官三十阶之{spec['ordinal']}阶",
            quote, f"据原文建立或复用{spec['new']}元丰寄禄官节点。",
            category="文臣京朝官寄禄官三十阶", officer="寄禄官",
            grade=spec["grade"], sort_order=108001800,
        )
        stipend_member(
            writer, entry_id, "北宋神宗元丰三年九月", new_tp,
            quote, spec["new"], 108001800,
        )
        for old_title in spec["olds"]:
            _, old_tp = state(
                writer, entry_id, old_title, "北宋神宗元丰三年九月",
                f"改名为{spec['new']}", quote,
                f"据原文建立或复用{old_title}元丰改名节点。",
                category="北宋前期本官阶终结", sort_order=108001800,
            )
            relation(
                writer, entry_id, old_tp, new_tp, "前后演变", quote,
                f"元丰三年{old_title}本官阶改名为{spec['new']}寄禄官阶。",
            )
        writer.commit()


PAIR_SPECS = {
    183: (
        "宣德郎", "左宣德郎", "右宣德郎",
        (
            ("split", "北宋哲宗元祐四年十一月", "宣德郎于北宋哲宗元祐四年十一月分左、右", 108902200),
            ("merge", "北宋哲宗绍圣二年四月", "绍圣二年四月罢分", 109500800),
        ),
    ),
    185: (
        "宣教郎", "左宣教郎", "右宣教郎",
        (
            ("split", "南宋高宗绍兴元年十二月", "宣教郎于南宋绍兴元年十二月分左、右", 113102400),
            ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月复罢左、右之分", 117400600),
        ),
    ),
    187: (
        "宣义郎", "左宣义郎", "右宣义郎",
        (
            ("split", "北宋哲宗元祐四年十一月", "宣义郎于北宋哲宗元祐四年十一月分左、右", 108902200),
            ("merge", "北宋哲宗绍圣二年四月", "绍圣二年四月罢分", 109500800),
            ("split", "南宋高宗绍兴元年十二月", "南宋绍兴元年十二月又分左、右", 113102400),
            ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月复罢左、右之分", 117400600),
        ),
    ),
    189: (
        "承事郎", "左承事郎", "右承事郎",
        (
            ("split", "北宋哲宗元祐四年十一月", "承事郎于北宋哲宗元祐四年十一月分左、右", 108902200),
            ("merge", "北宋哲宗绍圣二年四月", "绍圣二年四月罢分", 109500800),
            ("split", "南宋高宗绍兴元年十二月", "南宋绍兴元年十二月又分左、右", 113102400),
            ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月复罢左、右之分", 117400600),
        ),
    ),
    191: (
        "承奉郎", "左承奉郎", "右承奉郎",
        (
            ("split", "北宋哲宗元祐四年十一月", "承奉郎于北宋哲宗元祐四年十一月分左、右", 108902200),
            ("merge", "北宋哲宗绍圣二年四月", "绍圣二年四月罢分", 109500800),
            ("split", "南宋高宗绍兴元年十二月", "南宋绍兴元年十二月又分左、右", 113102400),
            ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月复罢左、右之分", 117400600),
        ),
    ),
    193: (
        "承务郎", "左承务郎", "右承务郎",
        (
            ("split", "北宋哲宗元祐四年十一月", "承务郎于北宋哲宗元祐四年十一月分左、右", 108902200),
            ("merge", "北宋哲宗绍圣二年四月", "绍圣二年四月罢分", 109500800),
            ("split", "南宋高宗绍兴元年十二月", "南宋绍兴元年十二月又分左、右", 113102400),
            ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月复罢左、右之分", 117400600),
        ),
    ),
}


def extract_left_right_entries():
    for entry_id, (base, left, right, changes) in PAIR_SPECS.items():
        writer = W(entry_id)
        for kind, time, needle, sort_order in changes:
            quote = Q(entry_id, needle)
            if kind == "split":
                add_split(writer, entry_id, base, left, right, time, quote, sort_order)
            else:
                add_merge(writer, entry_id, base, left, right, time, quote, sort_order)
        writer.commit()


def extract_xuande_rename():
    entry_id = 184
    writer = W(entry_id)
    quote = Q(
        entry_id,
        "北宋徽宗政和四年九月一日，因宣德郎与宣德门相犯，诏改宣德郎为宣教郎",
    )
    _, old_tp = state(
        writer, entry_id, "宣德郎", "北宋徽宗政和四年九月一日",
        "因与宣德门名相犯而改名宣教郎", quote,
        "据原文建立宣德郎精确到日的改名终结节点。",
        category="寄禄官改名", officer="寄禄官", sort_order=111401801,
    )
    _, new_tp = state(
        writer, entry_id, "宣教郎", "北宋徽宗政和四年九月一日",
        "由宣德郎避宣德门改名", quote,
        "据原文建立宣教郎精确到日的启用节点。",
        category="文臣京朝官寄禄官三十阶", officer="寄禄官",
        grade="从八品", sort_order=111401801,
    )
    relation(
        writer, entry_id, old_tp, new_tp, "前后演变", quote,
        "政和四年九月一日宣德郎因避宣德门改名宣教郎。",
    )
    stipend_member(writer, entry_id, "北宋徽宗政和四年九月一日", new_tp,
                   quote, "宣教郎", 111401801)
    writer.commit()


def add_group_relations(entry_id, group_title, time, event, members, quote,
                        sort_order=None, category="阶官统称"):
    writer = W(entry_id)
    _, group_tp = state(
        writer, entry_id, group_title, time, event, quote,
        f"据原文建立或复用{group_title}统称节点。",
        category=category, officer="职官总名", sort_order=sort_order,
    )
    for member_title, member_time, member_sort in members:
        _, member_tp = state(
            writer, entry_id, member_title, member_time,
            f"属于{group_title}所指阶官范围", quote,
            f"据原文建立或复用{member_title}作为{group_title}实例的节点。",
            category=category, officer="阶官", sort_order=member_sort,
        )
        relation(
            writer, entry_id, group_tp, member_tp, "统称与实例", quote,
            f"原文明示{group_title}包括{member_title}。",
        )
    writer.commit()


def extract_rank_classifications():
    # 元丰后五个末阶均属京官；宣德在政和四年改名后由宣教承接。
    quote = Q(192, "自承务郎以上至宣德郎（宣教郎）为京官")
    add_group_relations(
        192, "京官", "北宋神宗元丰三年九月",
        "承务郎至宣德郎为京官",
        [(title, "北宋神宗元丰三年九月", 108001800)
         for title in ("宣德郎", "宣义郎", "承事郎", "承奉郎", "承务郎")],
        quote, 108001800, "文臣京官类别",
    )
    quote = Q(184, "诏改宣德郎为宣教郎，迄南宋未变")
    add_group_relations(
        184, "京官", "北宋徽宗政和四年九月一日",
        "宣德郎改宣教郎后，宣教郎承接京官上界",
        [("宣教郎", "北宋徽宗政和四年九月一日", 111401801)],
        quote, 111401801, "文臣京官类别",
    )

    civil = (
        "朝请郎", "朝散郎", "朝奉郎", "承议郎", "奉议郎", "通直郎",
        "宣教郎", "宣义郎", "承事郎", "承奉郎", "承务郎",
    )
    military = (
        "正侍郎", "宣正郎", "履正郎", "协忠郎", "中侍郎", "中亮郎",
        "中卫郎", "翊卫郎", "亲卫郎", "拱卫郎", "左武郎", "右武郎",
        "武功郎", "武德郎", "武显郎", "武节郎", "武略郎", "武经郎",
        "武义郎", "武翼郎", "训武郎", "修武郎", "从义郎", "秉义郎",
        "忠训郎", "忠翊郎", "成忠郎", "保义郎", "承节郎",
    )
    quote = F[194]["text"]
    member_time = "北宋元丰官制及政和改武选官名后"
    member_sort = 111100000
    add_group_relations(
        194, "郎官", member_time,
        "文臣承务郎至朝请郎、武臣正侍郎至承节郎的通称",
        [(title, member_time, member_sort) for title in civil + military],
        quote, member_sort, "文武阶官统称",
    )


OLD_SELECTION_TIERS = (
    (("三京府判官", "留守司判官", "节度判官", "观察判官"), "第一等第一阶"),
    (("节度掌书记", "观察支使", "防御判官", "团练判官"), "第一等第二阶"),
    (("军事判官", "京府推官", "留守司推官", "节度推官", "观察推官"), "第一等第三阶"),
    (("防御推官", "团练推官", "军事推官", "军判官", "监判官"), "第二等第四阶"),
    (("县令", "录事参军"), "第三等第五阶"),
    (("试衔知县令", "知录事参军"), "第三等第六阶"),
    (("三京军巡判官", "司理参军", "司户参军", "司法参军", "户曹参军",
      "法曹参军", "县主簿", "县尉"), "第四等第七阶"),
)


def selection_group_state(writer, entry_id, time, event, quote, sort_order):
    return state(
        writer, entry_id, "选人阶官", time, event, quote,
        "据原文建立或复用选人阶官制度节点。",
        category="文臣选人阶官", officer="职官总名", sort_order=sort_order,
    )[1]


def extract_selection_system():
    entry_id = 195
    writer = W(entry_id)
    old_quote = Q(
        entry_id,
        "北宋前期由幕职州县官构成选人四阶七等，即：①两使职官（三京府判官、留守司判官、节察判官，节度掌书记、观察支使、防御、团练判官，京府留守司推官、节度、观察推官、军事判官三阶）；②初等职官（防御推官、团练推官、军事推官、军判官、监判官一阶）；③令录（县令、录事参军与试衔知县令、试衔知录事参军二阶）；④判司簿尉（三京军巡判官，司理、司户、司法、户曹、法曹参军，县主簿、县尉一阶）。",
    )
    old_group = selection_group_state(
        writer, entry_id, "北宋前期", "由幕职州县官构成四等七阶",
        old_quote, 96000000,
    )
    for titles, tier in OLD_SELECTION_TIERS:
        for title in titles:
            _, member_tp = state(
                writer, entry_id, title, "北宋前期", f"列选人四等七阶之{tier}",
                old_quote, f"据选人阶官总制条拆建{title}正式阶官实体。",
                category=f"选人四等七阶{tier}", officer="选人阶官",
                sort_order=96000000,
            )
            relation(
                writer, entry_id, old_group, member_tp, "统称与实例", old_quote,
                f"原文明示{title}属于北宋前期选人阶官。",
            )

    changes = (
        (
            "北宋徽宗崇宁二年九月二十五日",
            "七阶改名为承直郎至将仕郎",
            "徽宗崇宁二年九月改选人阶名后，其七阶为：承直郎、儒林郎、文林郎、从事郎、通仕郎、登仕郎、将仕郎。",
            ("承直郎", "儒林郎", "文林郎", "从事郎", "通仕郎", "登仕郎", "将仕郎"),
            110301825,
        ),
        (
            "北宋徽宗政和六年十一月",
            "由七阶增为十阶",
            "政和六年十一月，又从七阶增为十阶：承直郎、儒林郎、文林郎、从事郎、从政郎、修职郎、迪功郎、通仕郎、登仕郎、将仕郎。",
            ("承直郎", "儒林郎", "文林郎", "从事郎", "从政郎", "修职郎", "迪功郎", "通仕郎", "登仕郎", "将仕郎"),
            111602200,
        ),
    )
    for time, event, needle, titles, sort_order in changes:
        quote = Q(entry_id, needle)
        group_tp = selection_group_state(writer, entry_id, time, event, quote, sort_order)
        for title in titles:
            _, member_tp = state(
                writer, entry_id, title, time, "列入选人阶官序列", quote,
                f"据选人阶官总制条建立或复用{title}{time}节点。",
                category="选人阶官阶序", officer="选人阶官",
                sort_order=sort_order,
            )
            relation(
                writer, entry_id, group_tp, member_tp, "统称与实例", quote,
                f"原文明示{title}属于{time}的选人阶官序列。",
            )

    for time, event, needle, sort_order in (
        ("南宋高宗绍兴二年二月", "选人七阶分左、右，一依京朝官寄禄官制度",
         "南宋绍兴二年二月，选人七阶分左、右，其制一依京朝官寄禄官。", 113200400),
        ("南宋孝宗淳熙元年", "罢选人阶官左右之分", "淳熙元年罢分", 117400000),
    ):
        quote = Q(entry_id, needle)
        selection_group_state(writer, entry_id, time, event, quote, sort_order)
    writer.commit()


SELECTION_EVOLUTIONS = {
    196: (("三京府判官", "留守司判官", "节度判官", "观察判官"), "承直郎", None),
    197: (("节度掌书记", "观察支使", "防御判官", "团练判官"), "儒林郎", None),
    198: (("军事判官", "京府推官", "留守司推官", "节度推官", "观察推官"), "文林郎", None),
    199: (("防御推官", "团练推官", "军事推官", "军判官", "监判官"), "从事郎", None),
    200: (("县令", "录事参军"), "通仕郎", "从政郎"),
    201: (("试衔知县令", "知录事参军"), "登仕郎", "修职郎"),
}


def extract_selection_evolutions():
    for entry_id, (old_titles, chongning_title, zhenghe_title) in SELECTION_EVOLUTIONS.items():
        writer = W(entry_id)
        if entry_id == 196:
            needle = "徽宗崇宁二年九月二十五日后，改名为承直郎"
        elif entry_id == 197:
            needle = "徽宗崇宁二年九月二十五日后，改名儒林郎"
        elif entry_id == 198:
            needle = "崇宁二年九月二十五日后，改名为文林郎"
        elif entry_id == 199:
            needle = "徽宗崇宁二年九月二十五日后，改名为从事郎"
        elif entry_id == 200:
            needle = "崇宁二年九月二十五日，改名为通仕郎；政和六年十一月，又改为从政郎"
        else:
            needle = "崇宁二年九月二十五日改名登仕郎，政和六年十一月复改为修职郎"
        quote = Q(entry_id, needle)
        _, new_tp = state(
            writer, entry_id, chongning_title,
            "北宋徽宗崇宁二年九月二十五日", "由旧选人阶名改置", quote,
            f"据原文建立或复用{chongning_title}崇宁改名节点。",
            category="选人阶官阶序", officer="选人阶官",
            grade="从八品", sort_order=110301825,
        )
        for old_title in old_titles:
            _, old_tp = state(
                writer, entry_id, old_title,
                "北宋徽宗崇宁二年九月二十五日",
                f"改名为{chongning_title}", quote,
                f"据原文建立{old_title}崇宁改名终结节点。",
                category="北宋前期选人阶官终结", officer="选人阶官",
                sort_order=110301825,
            )
            relation(
                writer, entry_id, old_tp, new_tp, "前后演变", quote,
                f"崇宁二年{old_title}改名为{chongning_title}。",
            )
        if zhenghe_title:
            _, old_new_tp = state(
                writer, entry_id, chongning_title, "北宋徽宗政和六年十一月",
                f"改名为{zhenghe_title}", quote,
                f"据原文建立{chongning_title}政和改名终结节点。",
                category="选人阶官旧阶终结", officer="选人阶官",
                sort_order=111602200,
            )
            _, zhenghe_tp = state(
                writer, entry_id, zhenghe_title, "北宋徽宗政和六年十一月",
                f"由{chongning_title}改名", quote,
                f"据原文建立或复用{zhenghe_title}政和改名节点。",
                category="选人阶官阶序", officer="选人阶官",
                grade="从八品", sort_order=111602200,
            )
            relation(
                writer, entry_id, old_new_tp, zhenghe_tp, "前后演变", quote,
                f"政和六年{chongning_title}改名为{zhenghe_title}。",
            )
        writer.commit()


def main():
    expected = [
        "宣德郎", "左、右宣德郎", "宣教郎", "左、右宣教郎", "宣义郎",
        "左、右宣义郎", "承事郎", "左、右承事郎", "承奉郎",
        "左、右承奉郎", "承务郎", "左、右承务郎", "郎官", "选人阶官",
        "三京府判官，留守司判官，节度、观察判官",
        "节度掌书记、观察支使，防御、团练判官",
        "军事判官，京府、留守司、节度、观察推官",
        "防御、团练、军事推官，军、监判官", "县令、录事参军",
        "试衔知县令、知录事参军",
    ]
    assert [F[i]["title"] for i in range(182, 202)] == expected
    assert F[186]["title"] == "宣义郎"
    assert "简称" in F[199]["fields"] and "\n简称 " not in F[199]["text"]
    extract_yuanfeng_ranks()
    extract_left_right_entries()
    extract_xuande_rename()
    extract_rank_classifications()
    extract_selection_system()
    extract_selection_evolutions()


if __name__ == "__main__":
    main()
