#!/usr/bin/env python3
"""提取 chapter5t7 第1461-1480条：武卫将军至千牛卫大将军。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1441_1460 as previous


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch5t7.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB",
    os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t7.db"),
)


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "select title,page,text,fields from chapter5t7 where id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0], "page": row[1], "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(1461, 1481)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB
previous.F = F

W = base.W
field = base.field
relation = base.relation
cite = base.cite
alias_note = base.alias_note
node = previous.node
pair_title = previous.pair_title
member_titles = previous.member_titles


TIME_HINTS = {
    **previous.TIME_HINTS,
    "曹魏": 220,
    "隋朝": 590,
    "唐朝": 650,
    "唐初": 620,
    "唐前期": 650.1,
    "唐龙朔二年": 662,
    "唐神龙元年": 705,
    "唐德宗朝": 790,
    "北宋初": 960,
    "南宋乾道二年": 1166,
    "南宋淳熙九年": 1182,
    "南宋绍熙二年": 1191,
}
previous.TIME_HINTS = TIME_HINTS


def time_key(time, row_id):
    if time in TIME_HINTS:
        return (TIME_HINTS[time], 0, row_id)
    match = re.search(r"(-?\d{3,4})", time or "")
    if match:
        return (int(match.group(1)), 0, row_id)
    return previous.time_key(time, row_id)


def rechain(w, eid, decision):
    rows = w.conn.execute(
        "select id,time from Timepoints where entity_id=?", (eid,)
    ).fetchall()
    ordered = [row[0] for row in sorted(rows, key=lambda row: time_key(row[1], row[0]))]
    for index, tid in enumerate(ordered):
        w.relink(
            tid, decision,
            prev_id=ordered[index - 1] if index else None,
            succ_id=ordered[index + 1] if index + 1 < len(ordered) else None,
        )


def finish(w, touched, decision):
    for eid in touched:
        rechain(w, eid, decision)
    w.commit()


def institution_members(grouped_title):
    assert grouped_title.startswith("左、右")
    stem = grouped_title[3:]
    return f"左{stem}", f"右{stem}"


def institution_rename(i, old_title, new_title, old_time, new_time, quotation):
    w, touched = W(i), set()
    old_group = node(
        w, touched, i, old_title, "机构", old_time,
        f"{new_title}的前身", quotation, "前代禁卫机构合称",
        f"建立或复用{old_title}{old_time}节点。", "职源",
    )
    new_group = node(
        w, touched, i, new_title, "机构", new_time,
        f"由{old_title}改称", quotation, "前代禁卫机构合称",
        f"建立或复用{new_title}{new_time}节点。", "职源",
    )
    relation(
        w, i, old_group, new_group, "前后演变", quotation,
        f"{old_title}改称{new_title}。", "职源",
    )
    for old_member, new_member in zip(
        institution_members(old_title), institution_members(new_title)
    ):
        old_tid = node(
            w, touched, i, old_member, "机构", old_time,
            f"{old_title}所指实例", quotation, "前代禁卫机构",
            f"建立或复用{old_member}{old_time}节点。", "职源",
        )
        new_tid = node(
            w, touched, i, new_member, "机构", new_time,
            f"由{old_member}改称", quotation, "前代禁卫机构",
            f"建立或复用{new_member}{new_time}节点。", "职源",
        )
        relation(
            w, i, old_group, old_tid, "统称与实例", quotation,
            f"{old_member}是{old_title}实例。", "职源",
        )
        relation(
            w, i, new_group, new_tid, "统称与实例", quotation,
            f"{new_member}是{new_title}实例。", "职源",
        )
        relation(
            w, i, old_tid, new_tid, "前后演变", quotation,
            f"{old_member}改称{new_member}。", "职源",
        )
    finish(w, touched, f"整理{old_title}改称{new_title}的合称及左右实例演变。")


def appointment(i, family, rank, time, member_title, event):
    quotation = F[i]["text"]
    grouped_title = pair_title(family, rank)
    assert member_title in member_titles(family, rank)
    w, touched = W(i), set()
    grouped = node(
        w, touched, i, grouped_title, "官职", time,
        f"{event}；见具体左右实例", quotation, "环卫官左右合称",
        f"建立或复用{grouped_title}{time}实例节点。",
        officer=rank,
    )
    member = node(
        w, touched, i, member_title, "官职", time, event, quotation,
        "环卫官", f"建立或复用{member_title}{time}任官例节点。",
        officer=rank, update_event=True,
    )
    relation(
        w, i, grouped, member, "统称与实例", quotation,
        f"{member_title}是{grouped_title}在{time}的具体实例。",
    )
    finish(w, touched, f"保存{member_title}{time}任官实例。")


def add_alias(i, family, rank, time):
    aliases = field(i, "简称")
    w, touched = W(i), set()
    grouped = node(
        w, touched, i, pair_title(family, rank), "官职", time,
        "环卫官左右合称", F[i]["text"], "环卫官左右合称",
        f"复用{pair_title(family, rank)}{time}节点保存简称。",
        officer=rank,
    )
    alias_note(w, i, grouped, aliases, "简称")
    finish(w, touched, f"保存{pair_title(family, rank)}简称及引例。")


def entry1461():
    previous.pair_entry(1461, "武卫", "将军", (), "北宋初", "从四品")


def entry1462():
    i, origin = 1462, field(1462, "职源")
    w, touched = W(i), set()
    node(
        w, touched, i, "武卫中郎将", "官职", "曹魏",
        "武卫中郎将之名始见", origin, "前代武职",
        "建立曹魏武卫中郎将名称源流节点。", "职源",
        officer="中郎将",
    )
    finish(w, touched, "保存武卫中郎将名称始见于曹魏，不反推左右武卫中郎将已设。")
    previous.pair_entry(1462, "武卫", "中郎将", (), "南宋乾道二年")


def entry1463():
    previous.main_only_pair_entry(1463, "武卫", "郎将")
    appointment(
        1463, "武卫", "郎将", "南宋绍熙二年", "左武卫郎将",
        "盛雄飞获除左武卫郎将",
    )


def entry1464():
    origin = field(1464, "职源")
    previous.pair_entry(
        1464, "屯卫", "上将军",
        (("北宋初", "北宋始置；隋唐屯卫未设上将军"),),
        "北宋初", "从三品",
    )
    institution_rename(
        1464, "左、右屯卫", "左、右威卫", "隋朝", "唐朝", origin
    )


def entry1465():
    origin = field(1465, "职源")
    previous.pair_entry(
        1465, "屯卫", "大将军",
        (("隋朝", "隋朝左、右屯卫置大将军"),
         ("唐初", "唐初沿置左、右屯卫大将军")),
        "北宋初", "正四品",
    )
    institution_rename(
        1465, "左、右屯卫", "左、右威卫", "隋朝", "唐朝", origin
    )


def entry1466():
    previous.pair_entry(
        1466, "屯卫", "将军", (("隋朝", "隋朝始置"),),
        "北宋初", "从四品",
    )


def entry1467():
    previous.main_only_pair_entry(1467, "屯卫", "中郎将")


def entry1468():
    previous.main_only_pair_entry(1468, "屯卫", "郎将")


def entry1469():
    previous.pair_entry(
        1469, "领军卫", "上将军",
        (("唐德宗朝", "唐德宗朝始置"),), "北宋初", "从三品",
    )


def entry1470():
    previous.pair_entry(
        1470, "领军卫", "大将军",
        (("隋朝", "隋左、右领军卫府置大将军"),
         ("唐朝", "唐左、右领军卫置大将军")),
        "北宋初", "正四品",
    )


def entry1471():
    previous.pair_entry(
        1471, "领军卫", "将军", (("唐朝", "唐朝始置"),),
        "北宋初", "从四品",
    )


def entry1472():
    previous.main_only_pair_entry(1472, "领军卫", "中郎将")
    add_alias(1472, "领军卫", "中郎将", "南宋乾道二年")


def entry1473():
    previous.main_only_pair_entry(1473, "领军卫", "郎将")
    appointment(
        1473, "领军卫", "郎将", "南宋淳熙九年", "右领军卫郎将",
        "镇江都统制翟安道获除右领军卫郎将",
    )


def entry1474():
    origin = field(1474, "职源")
    previous.pair_entry(
        1474, "监门卫", "上将军",
        (("唐德宗朝", "唐德宗朝始置"),), "北宋初", "从三品",
    )
    institution_rename(
        1474, "左、右监门府", "左、右监门卫",
        "隋朝", "唐龙朔二年", origin,
    )


def entry1475():
    previous.pair_entry(
        1475, "监门卫", "大将军", (("唐朝", "唐朝始置"),),
        "北宋初", "正四品",
    )


def entry1476():
    previous.pair_entry(
        1476, "监门卫", "将军", (("唐朝", "唐朝始置"),),
        "北宋初", "从四品",
    )


def entry1477():
    previous.pair_entry(
        1477, "监门卫", "中郎将",
        (("唐前期", "唐前期始置"),), "南宋乾道二年",
    )


def entry1478():
    previous.main_only_pair_entry(1478, "监门卫", "郎将")
    add_alias(1478, "监门卫", "郎将", "南宋乾道二年")


def entry1479():
    origin = field(1479, "职源")
    previous.pair_entry(
        1479, "千牛卫", "上将军",
        (("唐德宗朝", "唐德宗朝始置"),), "北宋初", "从三品",
    )
    institution_rename(
        1479, "左、右奉宸卫", "左、右千牛卫",
        "唐神龙元年", "唐神龙元年", origin,
    )


def entry1480():
    previous.pair_entry(
        1480, "千牛卫", "大将军",
        (("唐神龙元年", "唐神龙元年始置"),), "北宋初", "正四品",
    )


def main():
    expected = [
        "左、右武卫将军", "左、右武卫中郎将", "左、右武卫郎将",
        "左、右屯卫上将军", "左、右屯卫大将军", "左、右屯卫将军",
        "左、右屯卫中郎将", "左、右屯卫郎将", "左、右领军卫上将军",
        "左、右领军卫大将军", "左、右领军卫将军",
        "左、右领军卫中郎将", "左、右领军卫郎将",
        "左、右监门卫上将军", "左、右监门卫大将军",
        "左、右监门卫将军", "左、右监门卫中郎将",
        "左、右监门卫郎将", "左、右千牛卫上将军",
        "左、右千牛卫大将军",
    ]
    assert [F[i]["title"] for i in range(1461, 1481)] == expected
    for i in range(1461, 1481):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
