#!/usr/bin/env python3
"""提取 chapter5t7 第1281-1300条：禁军指挥、都、将校节级与南宋三衙军职。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1261_1280 as previous


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


F = {i: load(i) for i in range(1281, 1301)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
field = base.field
relation = base.relation
cite = base.cite
alias_note = base.alias_note

node = previous.node
office_staff = previous.office_staff
group_instances = previous.group_instances


TIME_HINTS = {
    **previous.TIME_HINTS,
    "唐仪凤年间（676—679）": 677,
    "晚唐": 880,
    "五代后梁乾德二年（912）": 912,
    "宋代（广义）": 1099.8,
    "宋代（狭义）": 1099.9,
    "南宋绍兴五年十二月一日以前": 1135.94,
    "南宋绍兴五年十二月一日": 1135.95,
    "南宋绍兴五年十二月一日以后": 1135.96,
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


def unit_officer(i, unit, time, event, staff_type, *, aliases_name=None):
    main = F[i]["text"]
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, unit, F[i]["title"], time, main,
        f"{F[i]['title']}为{unit}一级编制官。",
        staff_type=staff_type, office_event=f"设置{F[i]['title']}",
        post_event=event,
    )
    if aliases_name:
        alias_note(w, i, post, field(i, aliases_name), aliases_name)
    finish(w, touched, f"整理{F[i]['title']}的{unit}级编制隶属、职掌与别称。")


def entry1281():
    unit_officer(1281, "军", "宋代", "军一级编制单位副长官", "军级副长官",
                 aliases_name="简称")


def entry1282():
    i, main = 1282, F[1282]["text"]
    w, touched = W(i), set()
    members = (
        "殿前司骑军诸指挥", "殿前司步军诸指挥",
        "侍卫亲军马军司诸军", "侍卫亲军步军司诸军",
    )
    group = group_instances(
        w, touched, i, F[i]["title"], "机构", "宋代",
        "除殿前司诸班诸直外，三衙所属骑军、步军诸军的总称",
        members, main, "正文明确三衙诸军所含四类军队。",
    )
    for office_title, child_title in (
        ("殿前司", "殿前司骑军诸指挥"),
        ("殿前司", "殿前司步军诸指挥"),
        ("侍卫亲军马军司", "侍卫亲军马军司诸军"),
        ("侍卫亲军步军司", "侍卫亲军步军司诸军"),
    ):
        office = node(w, touched, i, office_title, "机构", "宋代",
                      f"统辖{child_title}", main, "三衙机构",
                      f"建立{office_title}同期承载节点。")
        child = node(w, touched, i, child_title, "机构", "宋代",
                     f"隶属{office_title}", main, "三衙所属禁军",
                     f"复用{child_title}同期节点。")
        relation(w, i, office, child, "上下级机构", main,
                 f"正文明确{child_title}为{office_title}所属。")
    assert group
    finish(w, touched, "整理三衙诸军的四类实例及其分别归属的殿前、马军、步军三司。")


def entry1283():
    i, main = 1283, F[1283]["text"]
    w, touched = W(i), set()
    node(w, touched, i, F[i]["title"], "机构", "五代后梁乾德二年（912）",
         "已见一指挥的禁军编制", main, "禁军编制单位源流",
         "记录五代后梁已出现指挥。", update_event=True)
    node(w, touched, i, F[i]["title"], "机构", "宋代",
         "普遍设置的禁军编制和兵力计算单位，通常五百人、下分五都",
         main, "禁军编制单位", "记录宋代指挥编制。", update_event=True)
    finish(w, touched, "整理指挥的五代源流及宋代编制规模。")


def entry1284():
    unit_officer(1284, "指挥", "宋代", "指挥一级编制单位长官",
                 "指挥级长官", aliases_name="简称")


def entry1285():
    unit_officer(1285, "指挥", "宋代", "指挥一级军事编制单位副长官",
                 "指挥级副长官")


def entry1286():
    i, main = 1286, F[1286]["text"]
    w, touched = W(i), set()
    node(w, touched, i, F[i]["title"], "机构", "晚唐",
         "忠武军已见分八都", main, "禁军编制单位源流",
         "记录都编制晚唐源流。", update_event=True)
    node(w, touched, i, F[i]["title"], "机构", "宋代",
         "指挥下属编制，北宋通常一百人，骑军与步兵兵种构成不同",
         main, "禁军编制单位", "记录宋代都编制规模与构成。", update_event=True)
    finish(w, touched, "整理都的晚唐源流、指挥下属层级及宋代兵额构成。")


def entry1287():
    unit_officer(1287, "都", "宋代", "步兵都一级编制单位长官，可递迁副指挥使",
                 "步军都级长官", aliases_name="别名")


def entry1288():
    unit_officer(1288, "都", "宋代", "步兵都一级编制单位副长官，阙则拣十将迁补",
                 "步军都级副长官")


def entry1289():
    i, main = 1289, F[1289]["text"]
    w, touched = W(i), set()
    group_instances(
        w, touched, i, F[i]["title"], "官职", "宋代",
        "都头、副都头的连称", ("都头", "副都头"), main,
        "正文直接定义都副为都头、副都头连称。",
    )
    finish(w, touched, "建立都副统称及都头、副都头两个明确实例。")


def entry1290():
    i, main = 1290, F[1290]["text"]
    w, touched = W(i), set()
    node(w, touched, i, F[i]["title"], "官职", "唐仪凤年间（676—679）",
         "军使职名源流已见", main, "军职源流",
         "只记录军使的唐代职名源流，不反推当时已有宋代禁军都编制。",
         update_event=True)
    office_staff(
        w, touched, i, "都", F[i]["title"], "宋代", main,
        "宋代军使为禁军骑军都一级编制单位长官。",
        staff_type="骑军都级长官", office_event="设置军使",
        post_event="禁军骑军都一级编制单位长官",
    )
    finish(w, touched, "区分军使唐代职名源流与宋代禁军骑军都级长官编制。")


def entry1291():
    unit_officer(1291, "都", "宋代", "禁军骑军都一级编制单位副长官",
                 "骑军都级副长官")


def entry1292():
    i, main = 1292, F[1292]["text"]
    w, touched = W(i), set()
    members = (
        "都指挥使", "副都指挥使", "都虞候", "指挥使", "指挥副使",
        "都头", "副都头", "军使", "副兵马使",
    )
    group_instances(
        w, touched, i, F[i]["title"], "官职", "宋代",
        "禁军各级主要统兵官的总名", members, main,
        "正文逐类列明将校所含军职。",
    )
    finish(w, touched, "建立将校统称及九类明确军职实例。")


def entry1293():
    unit_officer(1293, "都", "宋代",
                 "步骑兵都一级员僚，位在都头等官之下，分左、右十将并分管军士",
                 "都级员僚")


def entry1294():
    unit_officer(1294, "都", "宋代",
                 "骑军都一级员僚，分左、右，位次于十将而在承局之上",
                 "都级员僚", aliases_name="简称")


def entry1295():
    unit_officer(1295, "都", "宋代",
                 "都一级员僚，分左、右，位次于将虞候而在押官之上",
                 "都级员僚")


def entry1296():
    unit_officer(1296, "都", "宋代",
                 "都一级最下等员僚，由长行迁补并分掌都内差官事",
                 "都级员僚")


def entry1297():
    i, main = 1297, F[1297]["text"]
    w, touched = W(i), set()
    node(w, touched, i, F[i]["title"], "官职", "宋代（广义）",
         "厢都指挥使以下至押官诸职次的泛称", main, "军职等级泛称",
         "保存节级广义定义，不据范围词推造穷举实例。", update_event=True)
    group_instances(
        w, touched, i, F[i]["title"], "官职", "宋代（狭义）",
        "不包括将校，专指十将、将虞候、承局、押官",
        ("十将", "将虞候", "承局", "押官"), main,
        "正文明确狭义节级所含四类军职。",
    )
    finish(w, touched, "区分节级广义职次泛称与狭义四类实例，避免推造广义穷举关系。")


def entry1298():
    i, main = 1298, F[1298]["text"]
    w, touched = W(i), set()
    group_instances(
        w, touched, i, F[i]["title"], "官职", "宋代（狭义）",
        "将校与节级的合称，自指挥使以下至押官",
        ("将校", "节级"), main,
        "正文直接定义将级为将校与节级合称。",
    )
    finish(w, touched, "建立将级统称及将校、节级两个明确实例。")


def entry1299():
    i, main = 1299, F[1299]["text"]
    w, touched = W(i), set()
    old = group_instances(
        w, touched, i, "三衙军、指挥、都三级编制", "机构",
        "南宋绍兴五年十二月一日以前", "北宋三衙沿用的三级编制",
        ("军", "指挥", "都"), main,
        "正文明确此为被取代的北宋三衙三级编制。",
    )
    new = group_instances(
        w, touched, i, "三衙军、将、队三级编制", "机构",
        "南宋绍兴五年十二月一日", "神武中军并隶殿前司后采用的三级编制",
        ("军", "将", "队"), main,
        "正文明确绍兴五年十二月一日以后采用军、将、队三级编制。",
    )
    relation(w, i, old, new, "前后演变", main,
             "绍兴五年十二月一日，军、将、队三级编制取代军、指挥、都三级编制。")
    members = (
        "主管殿前司公事", "主管侍卫亲军马军司公事",
        "主管侍卫亲军步军司公事", "统制", "统领", "正将", "副将",
        "准备将", "部将", "队将", "押队", "拥队",
    )
    group_instances(
        w, touched, i, F[i]["title"], "官职",
        "南宋绍兴五年十二月一日以后",
        "主管三衙公事及军、将、队三级统兵职事的总括",
        members, main, "正文逐一列明南宋三衙主要主管官和新制统兵职事。",
    )
    finish(w, touched, "整理南宋三衙主管官、军将队统兵职事及绍兴五年三级编制替代。")


def entry1300():
    i, main = 1300, F[1300]["text"]
    w, touched = W(i), set()
    members = tuple(
        f"{office}{post}"
        for office in ("殿前司", "侍卫亲军马军司", "侍卫亲军步军司")
        for post in ("都指挥使", "副都指挥使", "都虞候")
    )
    group = group_instances(
        w, touched, i, F[i]["title"], "官职", "南宋",
        "三衙九种主帅军职的总名，不常置，资浅者以主管某司公事代之",
        members, main, "正文逐一列明三帅在殿前、马军、步军三司的九种军职。",
    )
    cite(w, "Timepoints", group, i, main,
         "保存三帅不常置及资浅者改以主管某司公事代任的制度变化。")
    finish(w, touched, "建立三帅统称及三司各三种主帅实例，保存主管某司公事代任规则。")


def main():
    for i in range(1281, 1301):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
