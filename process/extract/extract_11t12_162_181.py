#!/usr/bin/env python3
"""提取 chapter11t12 第162-181条：寄禄官第十八至二十五阶及其统称。"""

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
    "extract_11t12_122_141_helpers", HERE / "extract_11t12_122_141.py"
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


F = {128: load(128), **{entry_id: load(entry_id) for entry_id in range(162, 182)}}
helpers.F = F
helpers.helpers.F = F
helpers.helpers.ENTRY_DB = ENTRY_DB
helpers.helpers.NEW_SORT = {}

W = helpers.W
Q = helpers.Q
state = helpers.state
relation = helpers.relation
stipend_member = helpers.stipend_member
add_split = helpers.add_split
add_merge = helpers.add_merge


RANK_SPECS = {
    163: {
        "new": "朝散大夫", "olds": ("中行郎中",), "grade": "从六品", "ordinal": "第十八",
        "quote": "寄禄官名。北宋神宗元丰三年九月，由中行郎中阶改。为文臣寄禄官三十阶之第十八阶。从六品",
    },
    165: {
        "new": "朝奉大夫", "olds": ("后行郎中",), "grade": "从六品", "ordinal": "第十九",
        "quote": "寄禄官名。北宋神宗元丰三年九月，由后行郎中阶改。为文臣京朝官寄禄官阶三十阶之第十九阶。从六品",
    },
    169: {
        "new": "朝请郎", "olds": ("前行员外郎", "侍御史"), "grade": "正七品", "ordinal": "第二十",
        "quote": "寄禄官名。北宋神宗元丰三年九月，由前行员外郎、侍御史阶改名。为文臣京朝官三十阶之第二十阶。“三朝郎”之一。正七品。",
    },
    171: {
        "new": "朝散郎", "olds": ("中行员外郎", "起居舍人"), "grade": "正七品", "ordinal": "第二十一",
        "quote": "寄禄官名。北宋神宗元丰三年九月，由中行员外郎、起居舍人阶改。为文臣京朝官寄禄官三十阶之第二十一阶。“三朝郎”之一。正七品",
    },
    173: {
        "new": "朝奉郎", "olds": ("后行员外郎", "左司谏", "右司谏"), "grade": "正七品", "ordinal": "第二十二",
        "quote": "寄禄官名。北宋神宗元丰三年九月，由后行员外郎、左、右司谏阶改。为文臣京朝官三十阶之第二十二阶。“三朝郎”之一。正七品",
    },
    176: {
        "new": "承议郎", "olds": ("左正言", "右正言", "太常博士", "国子博士"), "grade": "从七品", "ordinal": "第二十三",
        "quote": "寄禄官名。北宋神宗元丰三年九月，由左、右正言、太常博士、国子博士阶改。为文臣京朝官三十阶之第二十三阶。从七品。",
    },
    178: {
        "new": "奉议郎", "olds": ("太常丞", "秘书丞", "殿中丞", "著作郎"), "grade": "正八品", "ordinal": "第二十四",
        "quote": "寄禄官名。北宋元丰三年九月，由太常、秘书、殿中丞、著作郎阶改。为文臣寄禄官三十阶之第二十四阶。正八品",
    },
    180: {
        "new": "通直郎", "olds": ("太子中允", "太子左赞善大夫", "太子右赞善大夫", "太子中舍", "太子洗马"), "grade": "正八品", "ordinal": "第二十五",
        "quote": "寄禄官名。北宋神宗元丰三年九月，由太子中允、赞善大夫、中舍、洗马阶改。为文臣京朝官寄禄官三十阶之第二十五阶。正八品。自此阶以上为升朝官",
    },
}


def extract_yuanfeng_ranks():
    for entry_id, spec in RANK_SPECS.items():
        writer = W(entry_id)
        quote = Q(entry_id, spec["quote"])
        old_summary = "、".join(spec["olds"])
        _, new_tp = state(
            writer,
            entry_id,
            spec["new"],
            "北宋神宗元丰三年九月",
            f"由{old_summary}改名，为寄禄官三十阶之{spec['ordinal']}阶",
            quote,
            f"据原文建立或复用{spec['new']}元丰寄禄官节点。",
            category="文臣京朝官寄禄官三十阶",
            officer="寄禄官",
            grade=spec["grade"],
            sort_order=108001800,
        )
        stipend_member(
            writer, entry_id, "北宋神宗元丰三年九月", new_tp,
            quote, spec["new"], 108001800,
        )
        for old_title in spec["olds"]:
            _, old_tp = state(
                writer,
                entry_id,
                old_title,
                "北宋神宗元丰三年九月",
                f"改名为{spec['new']}",
                quote,
                f"据原文建立或复用{old_title}元丰改名节点。",
                category="北宋前期本官阶终结",
                sort_order=108001800,
            )
            relation(
                writer, entry_id, old_tp, new_tp, "前后演变", quote,
                f"元丰三年{old_title}本官阶改名为{spec['new']}寄禄官阶。",
            )
        writer.commit()


PAIR_SPECS = {
    162: (
        "朝请大夫", "左朝请大夫", "右朝请大夫",
        (
            ("split", "北宋哲宗元祐四年十一月", "朝请大夫于北宋哲宗元祐四年十一月分左、右", 108902200),
            ("merge", "北宋哲宗绍圣二年四月", "绍圣二年四月罢分", 109500800),
            ("split", "南宋高宗绍兴元年十二月", "南宋绍兴元年十二月又分左、右", 113102400),
            ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月复罢分左、右", 117400600),
        ),
    ),
    164: (
        "朝散大夫", "左朝散大夫", "右朝散大夫",
        (
            ("split", "北宋哲宗元祐四年十一月", "朝散大夫于哲宗元祐四年十一月分左、右", 108902200),
            ("merge", "北宋哲宗绍圣二年四月", "绍圣二年四月罢分", 109500800),
            ("split", "南宋高宗绍兴元年十二月", "南宋绍兴元年十二月又分左、右", 113102400),
            ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月复罢左、右之分", 117400600),
        ),
    ),
    166: (
        "朝奉大夫", "左朝奉大夫", "右朝奉大夫",
        (
            ("split", "北宋哲宗元祐四年十一月", "朝奉大夫于北宋哲宗元祐四年十一月分左、右", 108902200),
            ("merge", "北宋哲宗绍圣二年四月", "绍圣二年四月罢分", 109500800),
            ("split", "南宋高宗绍兴元年十二月", "南宋绍兴元年十二月又分左、右", 113102400),
        ),
    ),
    170: (
        "朝请郎", "左朝请郎", "右朝请郎",
        (
            ("split", "北宋哲宗元祐四年十一月", "朝请郎于北宋哲宗元祐四年十一月分左、右", 108902200),
            ("merge", "北宋哲宗绍圣二年四月", "绍圣二年四月罢分", 109500800),
            ("split", "南宋高宗绍兴元年十二月", "南宋绍兴元年十二月又分左、右", 113102400),
            ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月复罢分", 117400600),
        ),
    ),
    172: (
        "朝散郎", "左朝散郎", "右朝散郎",
        (
            ("split", "北宋哲宗元祐四年十一月", "朝散郎于北宋哲宗元祐四年十一月分左、右", 108902200),
            ("merge", "北宋哲宗绍圣二年四月", "绍圣二年四月罢分", 109500800),
            ("split", "南宋高宗绍兴元年十二月", "南宋绍兴元年十二月又分左、右", 113102400),
            ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月复罢左、右之分", 117400600),
        ),
    ),
    174: (
        "朝奉郎", "左朝奉郎", "右朝奉郎",
        (
            ("split", "北宋哲宗元祐四年十一月", "朝奉郎于北宋哲宗元祐四年十一月分左右", 108902200),
            ("merge", "北宋徽宗大观二年六月", "徽宗大观二年六月罢分", 110801200),
            ("split", "南宋高宗绍兴元年十二月", "南宋绍兴元年十二月又分左、右", 113102400),
            ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月复罢左、右之分", 117400600),
        ),
    ),
    177: (
        "承议郎", "左承议郎", "右承议郎",
        (
            ("split", "北宋哲宗元祐四年十一月", "承议郎于北宋元祐四年十一月分左、右", 108902200),
            ("merge", "北宋哲宗绍圣二年四月", "绍圣二年四月罢分", 109500800),
            ("split", "南宋高宗绍兴元年十二月", "南宋绍兴元年十二月又分左、右", 113102400),
            ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月复罢左右之分", 117400600),
        ),
    ),
    179: (
        "奉议郎", "左奉议郎", "右奉议郎",
        (
            ("split", "北宋哲宗元祐四年十一月", "奉议郎于北宋哲宗元祐四年十一月分左、右", 108902200),
            ("merge", "北宋哲宗绍圣二年四月", "绍圣二年四月罢分", 109500800),
            ("split", "南宋高宗绍兴元年十二月", "南宋绍兴元年十二月又分左、右", 113102400),
            ("merge", "南宋孝宗淳熙元年四月", "淳熙元年四月复罢左、右之分", 117400800),
        ),
    ),
    181: (
        "通直郎", "左通直郎", "右通直郎",
        (
            ("split", "北宋哲宗元祐四年十一月", "通直郎于北宋哲宗元祐四年十一月分左、右", 108902200),
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

    # #166 只明载绍兴再次分左右；总制条明载淳熙元年二月罢全部左右之分。
    writer = W(128)
    quote = Q(128, "⑦孝宗淳熙元年二月，罢寄禄官分左右")
    add_merge(
        writer, 128, "朝奉大夫", "左朝奉大夫", "右朝奉大夫",
        "南宋孝宗淳熙元年二月", quote, 117400400,
    )
    writer.commit()


RANK_ACTIVATIONS = [
    ("开府仪同三司", "北宋神宗元丰三年九月"),
    ("特进", "北宋神宗元丰三年九月"),
    ("金紫光禄大夫", "北宋神宗元丰三年九月"),
    ("银青光禄大夫", "北宋神宗元丰三年九月"),
    ("光禄大夫", "北宋神宗元丰三年九月"),
    ("宣奉大夫", "北宋徽宗大观二年六月二十七日"),
    ("正奉大夫", "北宋徽宗大观二年六月二十七日"),
    ("正议大夫", "北宋神宗元丰三年九月"),
    ("通奉大夫", "北宋徽宗大观二年六月二十七日"),
    ("通议大夫", "北宋神宗元丰三年九月"),
    ("太中大夫", "北宋神宗元丰三年九月"),
    ("中大夫", "北宋神宗元丰三年九月"),
    ("中奉大夫", "北宋徽宗大观二年六月二十七日"),
    ("中散大夫", "北宋神宗元丰三年九月"),
    ("朝议大夫", "北宋神宗元丰三年九月"),
    ("奉直大夫", "北宋徽宗大观二年六月"),
    ("朝请大夫", "北宋神宗元丰三年九月"),
    ("朝散大夫", "北宋神宗元丰三年九月"),
    ("朝奉大夫", "北宋神宗元丰三年九月"),
    ("朝请郎", "北宋神宗元丰三年九月"),
    ("朝散郎", "北宋神宗元丰三年九月"),
    ("朝奉郎", "北宋神宗元丰三年九月"),
    ("承议郎", "北宋神宗元丰三年九月"),
    ("奉议郎", "北宋神宗元丰三年九月"),
    ("通直郎", "北宋神宗元丰三年九月"),
]


def existing_timepoint(writer, title, time):
    rows = writer.conn.execute(
        "SELECT t.id FROM Timepoints t JOIN Entities e ON e.id=t.entity_id "
        "WHERE e.title=? AND t.time=?",
        (title, time),
    ).fetchall()
    assert len(rows) == 1, (title, time, rows)
    return rows[0][0]


def classification(entry_id, title, event, quote, member_indexes):
    writer = W(entry_id)
    _, group_tp = state(
        writer,
        entry_id,
        title,
        "宋代",
        event,
        quote,
        f"据原文建立{title}统称节点。",
        category="寄禄官合称",
        officer="职官总名",
    )
    for index in member_indexes:
        member_title, time = RANK_ACTIVATIONS[index - 1]
        member_tp = existing_timepoint(writer, member_title, time)
        relation(
            writer,
            entry_id,
            group_tp,
            member_tp,
            "统称与实例",
            quote,
            f"原文明示{title}包括{member_title}。",
        )
    writer.commit()


def extract_classifications():
    quote = Q(167, "文臣寄禄官自朝奉大夫以上至金紫光禄大夫十七阶之通称。")
    classification(
        167, "大夫", "朝奉大夫以上至金紫光禄大夫十七阶的通称",
        quote, range(3, 20),
    )

    quote = Q(
        168,
        "寄禄官朝请、朝散、朝奉大夫三阶，皆于元丰三年九月，由六部二十四司郎中（后行礼、工部郎中，中行户、刑部郎中，前行吏、兵部郎中）阶改，郎中别称正郎，故元丰改制后，或以正郎别称此三阶寄禄官。",
    )
    classification(
        168, "正郎", "朝请大夫、朝散大夫、朝奉大夫三阶的别称",
        quote, range(17, 20),
    )

    quote = Q(175, "文臣寄禄官朝请郎、朝散郎、朝奉郎之合称，取三郎中共有一“朝”字之义。")
    classification(
        175, "三朝郎", "朝请郎、朝散郎、朝奉郎的合称",
        quote, range(20, 23),
    )

    quote = Q(
        178,
        "③大朝官。《群书考索·后集》卷19《寄禄官》：“宋朝元丰新制，改太常、秘书、殿中丞为奉议郎。……以上皆号大朝官。”",
    )
    classification(
        178, "大朝官", "奉议郎及以上寄禄官的通称",
        quote, range(1, 25),
    )

    quote = Q(180, "自此阶以上为升朝官")
    classification(
        180, "升朝官", "通直郎及以上寄禄官的通称",
        quote, range(1, 26),
    )


def main():
    expected = [
        "左、右朝请大夫", "朝散大夫", "左、右朝散大夫", "朝奉大夫",
        "左、右朝奉大夫", "大夫", "正郎", "朝请郎", "左、右朝请郎",
        "朝散郎", "左、右朝散郎", "朝奉郎", "左、右朝奉郎", "三朝郎",
        "承议郎", "左、右承议郎", "奉议郎", "左、右奉议郎", "通直郎",
        "左、右通直郎",
    ]
    assert [F[i]["title"] for i in range(162, 182)] == expected
    assert F[169]["text"] and not F[169]["fields"].get("__status__")
    extract_yuanfeng_ranks()
    extract_left_right_entries()
    extract_classifications()


if __name__ == "__main__":
    main()
