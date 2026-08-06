#!/usr/bin/env python3
"""提取 chapter11t12 第142-161条：元丰寄禄官第八至十七阶及左右分合。"""

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
    "extract_11t12_122_141_helpers", HERE / "extract_11t12_122_141.py"
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


F = {128: load(128), **{entry_id: load(entry_id) for entry_id in range(142, 162)}}
prior.F = F
prior.helpers.F = F
prior.helpers.ENTRY_DB = ENTRY_DB
prior.helpers.NEW_SORT = {}

W = prior.W
Q = prior.Q
state = prior.state
relation = prior.relation
stipend_member = prior.stipend_member
add_split = prior.add_split
add_merge = prior.add_merge
split_or_merge_state = prior.split_or_merge_state


RANK_SPECS = {
    142: {
        "new": "正议大夫",
        "olds": ("吏部侍郎", "户部侍郎", "礼部侍郎", "兵部侍郎", "刑部侍郎", "工部侍郎"),
        "grade": "从三品",
        "ordinal": "第八",
        "quote": "寄禄官名。北宋元丰三年九月，由六部侍郎阶改名。为文臣京朝官三十阶之第八阶。从三品",
    },
    146: {
        "new": "通议大夫", "olds": ("给事中",), "grade": "正四品", "ordinal": "第十",
        "quote": "寄禄官名。北宋神宗元丰三年九月，由给事中改名。为文臣寄禄官三十阶之第十阶。正四品。",
    },
    148: {
        "new": "太中大夫", "olds": ("左谏议大夫", "右谏议大夫"), "grade": "从四品", "ordinal": "第十一",
        "quote": "寄禄官名。北宋神宗元丰三年九月，由左、右谏议大夫阶改。为文臣京朝官寄禄官三十阶之第十一阶。太中大夫以上为宰相所带阶官。待制以上文臣六年迁两官，至太中大夫止。元祐元年六月，重定待制以上文臣磨勘许至通议大夫（太中大夫之上一阶）止。从四品",
    },
    150: {
        "new": "中大夫", "olds": ("秘书监",), "grade": "正五品", "ordinal": "第十二",
        "quote": "寄禄官名。北宋神宗元丰三年九月，由秘书监改。为文臣京朝官寄禄官三十阶之第十二阶。正五品。",
    },
    154: {
        "new": "中散大夫", "olds": ("光禄卿", "卫尉卿", "少府监"), "grade": "从五品", "ordinal": "第十四",
        "quote": "寄禄官名。北宋神宗元丰三年九月由光禄卿、卫尉卿、少府监阶改。为文臣京朝官三十阶之第十四阶。从五品。",
    },
    157: {
        "new": "朝议大夫", "olds": ("太常少卿", "卫尉少卿", "司农少卿", "左司郎中", "右司郎中"), "grade": "正六品", "ordinal": "第十五",
        "quote": "寄禄官名。北宋神宗元丰三年九月，由太常少卿、卫尉少卿、司农少卿、尚书左右司郎中改。为文臣京朝官寄禄官三十阶之第十五阶。正六品。",
    },
    161: {
        "new": "朝请大夫", "olds": ("前行郎中",), "grade": "从六品", "ordinal": "第十七",
        "quote": "寄禄官名。北宋神宗元丰三年九月，由前行郎中改。为文臣寄禄官三十阶之第十七阶。从六品。",
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


def extract_dated_policies():
    policies = (
        (146, "通议大夫", "北宋哲宗元祐元年六月", "重定待制以上文臣磨勘，最高至通议大夫", "元祐元年六月重定文臣待制以上磨勘至通议大夫止", 108601200),
        (148, "太中大夫", "北宋哲宗元祐元年六月", "待制以上文臣磨勘上限改至通议大夫，不再以太中大夫为止", "元祐元年六月，重定待制以上文臣磨勘许至通议大夫（太中大夫之上一阶）止。", 108601200),
        (154, "中散大夫", "北宋哲宗元祐元年六月十四日", "定非侍从官磨勘最高至中散大夫", "哲宗元祐元年六月十四日，定文臣非侍从官磨勘至中散大夫阶止。", 108601214),
        (154, "中散大夫", "北宋哲宗元祐三年十一月", "左、右中散大夫以二十员为额，候阙除授", "元祐三年十一月，左、右中散大夫以二十员为额，候有阙方许除授", 108802200),
        (157, "朝议大夫", "北宋哲宗元祐三年十一月十四日", "重定左、右朝议大夫以五十员为额", "元祐三年十一月十四日，重定左、右朝议大夫以五十员为额", 108802214),
    )
    for entry_id, title, time, event, needle, sort_order in policies:
        writer = W(entry_id)
        quote = Q(entry_id, needle)
        state(
            writer,
            entry_id,
            title,
            time,
            event,
            quote,
            f"据原文建立{title}{time}制度规则节点。",
            category="寄禄官磨勘与员额制度",
            officer="寄禄官",
            sort_order=sort_order,
        )
        writer.commit()


PAIR_SPECS = {
    143: (
        "正议大夫", "左正议大夫", "右正议大夫",
        (
            ("split", "北宋哲宗元祐三年二月六日", "正议大夫于北宋哲宗元祐三年二月六日分左、右", 108800406),
            ("merge", "北宋徽宗大观二年六月", "徽宗大观二年六月罢分", 110801200),
            ("split", "南宋高宗绍兴元年十二月", "南宋绍兴元年十二月又分左、右", 113102400),
            ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月复罢分", 117400600),
        ),
    ),
    145: (
        "通奉大夫", "左通奉大夫", "右通奉大夫",
        (
            ("split", "南宋高宗绍兴元年十二月", "通奉大夫于南宋绍兴元年十二月分左、右", 113102400),
            ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月罢分", 117400600),
        ),
    ),
    147: (
        "通议大夫", "左通议大夫", "右通议大夫",
        (("split", "南宋高宗绍兴元年十二月", "通议大夫于南宋绍兴元年十二月分左、右", 113102400),),
    ),
    149: (
        "太中大夫", "左太中大夫", "右太中大夫",
        (
            ("split", "南宋高宗绍兴元年十二月", "太中大夫于南宋绍兴元年十二月分左、右", 113102400),
            ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月复罢分左、右", 117400600),
        ),
    ),
    151: (
        "中大夫", "左中大夫", "右中大夫",
        (
            ("split", "南宋高宗绍兴元年十二月", "中大夫于南宋绍兴元年十二月分左、右", 113102400),
            ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月复罢分左、右", 117400600),
        ),
    ),
    153: (
        "中奉大夫", "左中奉大夫", "右中奉大夫",
        (("split", "南宋高宗绍兴元年十二月", "中奉大夫于南宋绍兴元年十二月分左、右", 113102400),),
    ),
    155: (
        "中散大夫", "左中散大夫", "右中散大夫",
        (
            ("split", "北宋哲宗元祐三年二月六日", "中散大夫于北宋哲宗元祐三年二月六日分左、右", 108800406),
            ("merge", "北宋徽宗大观二年六月二十七日", "徽宗大观二年六月二十七日罢分", 110801227),
            ("split", "南宋高宗绍兴元年十二月", "南宋绍兴元年十二月又分左、右", 113102400),
            ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月复罢", 117400600),
        ),
    ),
    158: (
        "朝议大夫", "左朝议大夫", "右朝议大夫",
        (
            ("split", "北宋哲宗元祐三年二月", "朝议大夫于北宋哲宗元祐三年二月分左、右", 108800400),
            ("merge", "北宋徽宗大观二年六月", "徽宗大观二年六月罢分", 110801200),
            ("split", "南宋高宗绍兴元年十二月", "南宋绍兴元年十二月又分左、右", 113102400),
            ("merge", "南宋孝宗淳熙元年三月", "淳熙元年三月复罢分", 117400600),
        ),
    ),
    160: (
        "奉直大夫", "左奉直大夫", "右奉直大夫",
        (
            ("split", "南宋高宗绍兴元年十二月", "奉直大夫于南宋绍兴元年十二月分左、右", 113102400),
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

    # #147、#153 本条只明载绍兴分左右；总制条另明载淳熙元年二月
    # 罢全部寄禄官左右之分，故用总制条证据补齐两组收束关系。
    general_entry = 128
    general_quote = Q(general_entry, "⑦孝宗淳熙元年二月，罢寄禄官分左右")
    for base, left, right in (
        ("通议大夫", "左通议大夫", "右通议大夫"),
        ("中奉大夫", "左中奉大夫", "右中奉大夫"),
    ):
        writer = W(general_entry)
        add_merge(
            writer,
            general_entry,
            base,
            left,
            right,
            "南宋孝宗淳熙元年二月",
            general_quote,
            117400400,
        )
        writer.commit()


DAGUAN_SPECS = {
    144: {
        "new": "通奉大夫", "old": "右正议大夫", "ordinal": "第九", "grade": "从三品",
        "time": "北宋徽宗大观二年六月二十七日", "sort": 110801227,
        "quote": "寄禄官名。北宋徽宗大观二年六月二十七日新置阶名，换右正议大夫阶。为文臣京朝官寄禄官三十阶之第九阶。从三品",
    },
    152: {
        "new": "中奉大夫", "old": "左中散大夫", "ordinal": "第十三", "grade": "从五品",
        "time": "北宋徽宗大观二年六月二十七日", "sort": 110801227,
        "quote": "寄禄官名。北宋徽宗大观二年六月二十七日新增阶名，换左中散大夫阶。为文臣京朝官寄禄官阶三十阶之第十三阶。从五品",
    },
    159: {
        "new": "奉直大夫", "old": "右朝议大夫", "ordinal": "第十六", "grade": "正六品",
        "time": "北宋徽宗大观二年六月", "sort": 110801200,
        "quote": "寄禄官名。北宋徽宗大观二年六月增创新阶名，换右朝议大夫阶。为文臣京朝官寄禄官三十阶之第十六阶。正六品",
    },
}


def extract_daguan_ranks():
    for entry_id, spec in DAGUAN_SPECS.items():
        writer = W(entry_id)
        quote = Q(entry_id, spec["quote"])
        old_tp = split_or_merge_state(
            writer,
            entry_id,
            spec["old"],
            spec["time"],
            f"罢分，阶名换为{spec['new']}",
            quote,
            spec["sort"],
        )
        _, new_tp = state(
            writer,
            entry_id,
            spec["new"],
            spec["time"],
            f"新增寄禄官阶，换{spec['old']}阶，为三十阶之{spec['ordinal']}阶",
            quote,
            f"据原文建立{spec['new']}大观新增节点。",
            category="文臣京朝官寄禄官三十阶",
            officer="寄禄官",
            grade=spec["grade"],
            sort_order=spec["sort"],
        )
        relation(
            writer, entry_id, old_tp, new_tp, "前后演变", quote,
            f"大观年间新增{spec['new']}，换{spec['old']}阶。",
        )
        stipend_member(
            writer, entry_id, spec["time"], new_tp,
            quote, spec["new"], spec["sort"],
        )
        writer.commit()


def main():
    expected = [
        "正议大夫", "左、右正议大夫", "通奉大夫", "左、右通奉大夫",
        "通议大夫", "左、右通议大夫", "太中大夫", "左、右太中大夫",
        "中大夫", "左、右中大夫", "中奉大夫", "左、右中奉大夫",
        "中散大夫", "左、右中散大夫", "左、右中散", "朝议大夫",
        "左、右朝议大夫", "奉直大夫", "左、右奉直大夫", "朝请大夫",
    ]
    assert [F[i]["title"] for i in range(142, 162)] == expected
    assert F[156]["fields"].get("__status__") == "placeholder" and not F[156]["text"]
    extract_yuanfeng_ranks()
    extract_dated_policies()
    extract_left_right_entries()
    extract_daguan_ranks()


if __name__ == "__main__":
    main()
