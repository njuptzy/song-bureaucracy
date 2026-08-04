#!/usr/bin/env python3
"""提取 chapter5t7 第1301-1320条：南宋三衙军、将、队编制及军职。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1281_1300 as previous


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


F = {i: load(i) for i in range(1301, 1321)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
relation = base.relation
cite = base.cite

node = previous.node
office_staff = previous.office_staff
group_instances = previous.group_instances


TIME_HINTS = {
    **previous.TIME_HINTS,
    "南宋建炎以后": 1127.2,
    "南宋绍兴五年十二月一日": 1135.95,
}


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


def unit_officer(i, unit, time, event, staff_type):
    main = F[i]["text"]
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, unit, F[i]["title"], time, main,
        f"{F[i]['title']}为南宋三衙{unit}一级编制职事。",
        staff_type=staff_type, office_event=f"设置{F[i]['title']}",
        post_event=event,
    )
    cite(w, "Timepoints", post, i, main, f"保存{F[i]['title']}的职掌、序位和性质。")
    finish(w, touched, f"整理{F[i]['title']}的{unit}级编制隶属、职掌与序位。")


def entry1301():
    i, main = 1301, F[1301]["text"]
    w, touched = W(i), set()
    group_instances(
        w, touched, i, F[i]["title"], "官职", "南宋建炎以后",
        "南宋三衙主帅都指挥使、副都指挥使的合称",
        ("都指挥使", "副都指挥使"), main,
        "正文直接定义此处指挥为都指挥使、副都指挥使合称。",
    )
    finish(w, touched, "建立南宋军职统称‘指挥’及都指挥使、副都指挥使两个实例。")


def entry1302():
    i, main = 1302, F[1302]["text"]
    w, touched = W(i), set()
    group_instances(
        w, touched, i, F[i]["title"], "官职", "南宋",
        "三衙资浅主帅所充主管公事的泛称",
        ("主管殿前司公事", "主管侍卫亲军马军司公事",
         "主管侍卫亲军步军司公事"), main,
        "正文分别举出殿前、马军、步军三司主管公事实例。",
    )
    finish(w, touched, "建立主管某司公事统称及三衙三种主管公事实例。")


def entry1303():
    i, main = 1303, F[1303]["text"]
    w, touched = W(i), set()
    branches = {
        "殿前司": (
            "前军", "右军", "中军", "左军", "后军", "选锋军", "护圣军",
            "游奕军", "神策选锋军", "摧锋军",
        ),
        "侍卫亲军马军行司": ("前军", "右军", "中军", "左军", "后军"),
        "侍卫亲军步军司": (
            "神勇军", "振华军", "安远军", "奉先园", "武宁军", "威勇军",
            "雄勇军", "必胜军", "前军", "右军", "中军", "左军", "后军",
        ),
    }
    members = tuple(
        f"{office}{name}" for office, names in branches.items() for name in names
    )
    group_instances(
        w, touched, i, F[i]["title"], "机构", "南宋",
        "三衙沿北宋之制设置的大编制单位", members, main,
        "正文分殿前司、马军行司、步军司逐一列出南宋诸军番号。",
    )
    for office_title, names in branches.items():
        office = node(w, touched, i, office_title, "机构", "南宋",
                      "统辖所属诸军", main, "三衙机构",
                      f"建立{office_title}南宋承载节点。")
        for name in names:
            member_title = f"{office_title}{name}"
            member = node(w, touched, i, member_title, "机构", "南宋",
                          f"隶属{office_title}", main, "三衙所属军",
                          f"复用{member_title}南宋节点。")
            relation(w, i, office, member, "上下级机构", main,
                     f"正文明确{member_title}为{office_title}所属军。")
    finish(w, touched, "恢复南宋‘军’正式词条，建立二十八个明确军号及其三司归属。")


def entry1304():
    unit_officer(1304, "军", "南宋",
                 "由军功或高位统制擢任，职事与统制相同", "军级长官")


def entry1305():
    unit_officer(1305, "军", "南宋绍兴五年十二月一日",
                 "三衙军始设，每军皆置，为军一级编制长官", "军级长官")


def entry1306():
    unit_officer(1306, "军", "南宋",
                 "军一级编制长官，位略低于统制而职事相同", "军级长官")


def entry1307():
    unit_officer(1307, "军", "南宋绍兴五年十二月一日",
                 "始设，为军一级编制副长官，位次于统制而在正将之上",
                 "军级副长官")


def entry1308():
    i, main = 1308, F[1308]["text"]
    w, touched = W(i), set()
    group_instances(
        w, touched, i, F[i]["title"], "官职", "南宋建炎以后",
        "统制、统领的连称", ("统制", "统领"), main,
        "正文直接定义制领为统制、统领连称。",
    )
    finish(w, touched, "建立制领统称及统制、统领两个实例。")


def entry1309():
    i, main = 1309, F[1309]["text"]
    w, touched = W(i), set()
    army = node(w, touched, i, "军", "机构", "南宋绍兴五年十二月一日",
                "下辖将", main, "三衙军级编制", "建立军同期节点。")
    general = node(w, touched, i, F[i]["title"], "机构",
                   "南宋绍兴五年十二月一日",
                   "隶属于军，其下为队，随神武中军归殿前司成为三衙编制单位",
                   main, "三衙将级编制", "记录将编制始置与层级。", update_event=True)
    team = node(w, touched, i, "队", "机构", "南宋绍兴五年十二月一日",
                "隶属于将", main, "三衙队级编制", "建立队同期节点。")
    relation(w, i, army, general, "上下级机构", main, "南宋三衙将隶属于军。")
    relation(w, i, general, team, "上下级机构", main, "南宋三衙将之下为队。")
    finish(w, touched, "整理绍兴五年军、将、队三级编制中的将及其上下层级。")


def entry1310():
    unit_officer(1310, "将", "南宋绍兴五年十二月一日",
                 "三衙始置，为将一级编制长官，位在统领之下、副将准备将之上",
                 "将级长官")


def entry1311():
    unit_officer(1311, "将", "南宋绍兴五年十二月一日",
                 "三衙始置，为将一级编制长官，位次于正将",
                 "将级长官")


def entry1312():
    unit_officer(1312, "将", "南宋绍兴五年十二月一日",
                 "三衙始置，为将一级编制佐官，位次于副将而高于训练官",
                 "将级佐官")


def entry1313():
    unit_officer(1313, "将", "南宋",
                 "将一级教阅训练军官，非统兵官，位次于准备将",
                 "将级训练官")


def entry1314():
    i, main = 1314, F[1314]["text"]
    w, touched = W(i), set()
    general = node(w, touched, i, "将", "机构", "南宋绍兴五年十二月一日",
                   "下辖队", main, "三衙将级编制", "建立将同期节点。")
    team = node(w, touched, i, F[i]["title"], "机构",
                "南宋绍兴五年十二月一日",
                "隶属于将，随神武中军归殿前司成为三衙最低一级编制单位",
                main, "三衙队级编制", "记录队编制始置与层级。", update_event=True)
    relation(w, i, general, team, "上下级机构", main, "南宋三衙队隶属于将。")
    finish(w, touched, "整理绍兴五年军、将、队三级编制中的队及其将级归属。")


def entry1315():
    unit_officer(1315, "队", "南宋",
                 "队一级编制长官，不列军官，为一等职事", "队级一等职事")


def entry1316():
    unit_officer(1316, "队", "南宋",
                 "队一级编制长官，次于部将，不列军官，为一等职事",
                 "队级一等职事")


def entry1317():
    unit_officer(1317, "队", "南宋",
                 "队一级编制小头目，不列军官，为一等职事", "队级一等职事")


def entry1318():
    unit_officer(1318, "队", "南宋",
                 "队一级编制小头目，不列军官，为一等职事", "队级一等职事")


def entry1319():
    i, main = 1319, F[1319]["text"]
    w, touched = W(i), set()
    group_instances(
        w, touched, i, F[i]["title"], "官职", "南宋",
        "正将、副将、准备将的合称", ("正将", "副将", "准备将"), main,
        "正文直接定义将佐所含三种将级军职。",
    )
    finish(w, touched, "建立将佐统称及正将、副将、准备将三个实例。")


def entry1320():
    i, main = 1320, F[1320]["text"]
    w, touched = W(i), set()
    group_instances(
        w, touched, i, F[i]["title"], "官职", "南宋",
        "部将、队将的连称", ("部将", "队将"), main,
        "正文直接定义部队将为部将、队将连称。",
    )
    finish(w, touched, "建立部队将统称及部将、队将两个实例。")


def main():
    for i in range(1301, 1321):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
