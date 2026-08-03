#!/usr/bin/env python3
"""提取 chapter5t7 第1181-1200条：殿前司管军、六案与殿前诸班。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1161_1180 as previous


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


F = {i: load(i) for i in range(1181, 1201)}
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
parent_child = previous.parent_child
group_instances = previous.group_instances


TIME_HINTS = {
    **previous.TIME_HINTS,
    "后周显德元年十月": 954.8,
    "后周显德五年三月二十三日": 958.23,
    "后周显德六年七月至十月": 959.7,
    "宋代": 1100,
    "北宋熙宁五年": 1072,
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


def group_relation(w, i, group_tid, member_tid, quotation, decision,
                   field_name=None):
    relation(w, i, group_tid, member_tid, "统称与实例", quotation,
             decision, field_name)


def entry1181():
    i = 1181
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    rank, roster, aliases = field(i, "品位"), field(i, "编制"), field(i, "简称与别名")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "殿前司", "殿前司副都指挥使",
        "后周显德五年三月二十三日", origin,
        "后周始置，定员一人，两宋沿置。", "职源与沿革",
        quota=1, staff_type="殿前司副统领",
        office_event="设置副都指挥使",
        post_event="始置，两宋沿置，佐都指挥使领本司公事",
        grade="正四品",
    )
    cite(w, "Timepoints", post, i, duty, "保存副统领职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "保存正四品及三衙管军位次。", "品位")
    cite(w, "Timepoints", post, i, roster, "保存一人员额。", "编制")
    alias_note(w, i, post, aliases, "简称与别名")
    finish(w, touched, "整理殿前司副都指挥使始置沿置、隶属、职掌、品位、员额与别称。")


def entry1182():
    i = 1182
    origin, duty, rank, aliases = (
        field(i, x) for x in ("职源与沿革", "职掌", "品位", "简称与别名")
    )
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "殿前司", "殿前司都虞候", "后周显德六年七月至十月",
        origin, "后周始置，两宋沿置。", "职源与沿革",
        staff_type="殿前司统领官", office_event="设置都虞候",
        post_event="始置，两宋沿置，仅次于殿前都、副都指挥使",
        grade="从五品",
    )
    cite(w, "Timepoints", post, i, duty, "保存统领职掌与位次。", "职掌")
    cite(w, "Timepoints", post, i, rank, "保存从五品及南宋三衙军职序列。", "品位")
    alias_note(w, i, post, aliases, "简称与别名")
    finish(w, touched, "整理殿前司都虞候始置沿置、隶属、职掌、品位与别称。")


def entry1183():
    i, main = 1183, F[1183]["text"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "殿前司", "殿前司都虞候司", "宋代", main,
        "殿前司都虞候司为殿前司所属治所。",
        parent_event="下设都虞候司治所",
        child_event="殿前都虞候治所，置勾押官、前后行、通引官各一人",
    )
    finish(w, touched, "建立殿前司都虞候司的殿前司隶属、治所性质与吏额。")


OFFICE_EVENTS = {
    1184: "掌诸军、直、班功赏、教阅转资、内外转补与拍试换官",
    1185: "掌殿侍年满出职、驿殿侍和宫院祗应差派及磨勘奏补",
    1186: "掌诸军、直、班俸给请受、斋筵及到阙使人祗应差派",
    1187: "掌教阅训练、鞍马收支、兵器衣甲请发及将校朱记",
    1188: "掌本司狱讼追呼取索、巡防兵级差替及逃兵捉验",
    1189: "掌检阅、引证条例法令",
    1190: "掌收接投拆词状及诸处发到殿前司文书",
}


def office_entry(i):
    main, title = F[i]["text"], F[i]["title"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "殿前司", title, "宋代", main,
        f"{title}是殿前司所属事务机构。",
        parent_event=f"下设{title}", child_event=OFFICE_EVENTS[i],
    )
    finish(w, touched, f"建立{title}的殿前司隶属及职掌。")


def entry1184(): office_entry(1184)
def entry1185(): office_entry(1185)
def entry1186(): office_entry(1186)
def entry1187(): office_entry(1187)
def entry1188(): office_entry(1188)
def entry1189(): office_entry(1189)
def entry1190(): office_entry(1190)


def entry1191():
    i = 1191
    main, origin, duty = F[i]["text"], field(i, "职源"), field(i, "职掌")
    roster, aliases = field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    _, group = parent_child(
        w, touched, i, "殿前司", "殿前诸班", "后周显德元年十月", origin,
        "后周始置殿前诸班，隶殿前司。", "职源",
        parent_event="设置殿前诸班", child_event="始置，为皇帝近卫骑兵编制",
    )
    cite(w, "Timepoints", group, i, main, "补证殿前诸班隶殿前司。")
    cite(w, "Timepoints", group, i, duty, "保存扈从乘舆、侍卫殿陛职掌。", "职掌")
    cite(w, "Timepoints", group, i, roster,
         "保存诸班主要班次、指挥官与诸班诸直合计兵额。", "编制")
    alias_note(w, i, group, aliases, "简称")
    finish(w, touched, "整理殿前诸班始置、殿前司隶属、宿卫职掌、编制与简称。")


def class_entry(i, event, aliases_field=None):
    main, title = F[i]["text"], F[i]["title"]
    w, touched = W(i), set()
    parent = node(w, touched, i, "殿前司", "机构", "宋代",
                  "统辖殿前诸班", main, "禁军指挥机构",
                  "建立殿前司同期承载节点。")
    group = node(w, touched, i, "殿前诸班", "机构", "宋代",
                 "皇帝近卫骑兵诸班总称", main, "禁军班直统称",
                 "建立殿前诸班同期承载节点。")
    member = node(w, touched, i, title, "机构", "宋代", event, main,
                  "殿前诸班班直", f"建立{title}正式词条节点。", update_event=True)
    relation(w, i, parent, member, "上下级机构", main,
             f"{title}隶殿前司。")
    group_relation(w, i, group, member, main, f"{title}是殿前诸班之一。")
    if aliases_field:
        aliases = field(i, aliases_field)
        alias_note(w, i, member, aliases, aliases_field)
    finish(w, touched, f"整理{title}的殿前司隶属、殿前诸班实例关系与近卫性质。")


def entry1192():
    class_entry(1192, "殿前诸班左班，皇宫近卫禁旅", "简称")


def entry1193():
    class_entry(1193, "殿前诸班右班，皇宫近卫禁旅", "简称")


def entry1194():
    i, main = 1194, F[1194]["text"]
    w, touched = W(i), set()
    post = node(w, touched, i, "殿前指挥使都虞候", "官职", "宋代",
                "殿前指挥使班长官，左、右班均置", main,
                "殿前诸班军职", "建立殿前指挥使都虞候。", update_event=True)
    for office in ("殿前指挥使左班", "殿前指挥使右班"):
        office_tid = node(w, touched, i, office, "机构", "宋代",
                          "设置都虞候", main, "殿前诸班班直",
                          f"建立{office}同期承载节点。")
        relation(w, i, office_tid, post, "编制隶属", main,
                 f"{office}均置殿前指挥使都虞候。", staff_quota=1,
                 staff_type="班长官")
    finish(w, touched, "建立殿前指挥使都虞候及其在左、右班的双重编制隶属。")


PAIRED_MEMBERS = {
    1195: ("内殿直左第一班", "内殿直左第二班", "内殿直右第一班", "内殿直右第二班"),
    1196: ("散员左第一班", "散员左第二班", "散员右第一班", "散员右第二班"),
    1197: ("散指挥左第一班", "散指挥左第二班", "散指挥右第一班", "散指挥右第二班"),
    1198: ("散都头左班", "散都头右班"),
    1200: ("散祗候左班", "散祗候右班"),
}


def paired_class_entry(i, aliases_field=None):
    main, title = F[i]["text"], F[i]["title"]
    w, touched = W(i), set()
    parent = node(w, touched, i, "殿前司", "机构", "宋代",
                  "统辖殿前诸班", main, "禁军指挥机构",
                  "建立殿前司同期承载节点。")
    all_classes = node(w, touched, i, "殿前诸班", "机构", "宋代",
                       "皇帝近卫骑兵诸班总称", main, "禁军班直统称",
                       "建立殿前诸班同期承载节点。")
    grouped = group_instances(
        w, touched, i, title, "机构", "宋代",
        "左右班合列词头，均为殿前诸班近卫禁旅",
        PAIRED_MEMBERS[i], main, "正式词头明确列出各班实例。",
    )
    relation(w, i, parent, grouped, "上下级机构", main,
             f"{title}隶殿前司。")
    group_relation(w, i, all_classes, grouped, main,
                   f"{title}是殿前诸班所含班次。")
    if aliases_field:
        alias_note(w, i, grouped, field(i, aliases_field), aliases_field)
    finish(w, touched, f"整理{title}合列词头、明确实例、殿前司隶属及殿前诸班关系。")


def entry1195(): paired_class_entry(1195, "简称")
def entry1196(): paired_class_entry(1196)
def entry1197(): paired_class_entry(1197)
def entry1198(): paired_class_entry(1198)


def entry1199():
    i, main = 1199, F[1199]["text"]
    w, touched = W(i), set()
    parent = node(w, touched, i, "殿前司", "机构", "宋代", "统辖殿前诸班",
                  main, "禁军指挥机构", "建立殿前司同期承载节点。")
    group = node(w, touched, i, "殿前诸班", "机构", "宋代",
                 "皇帝近卫骑兵诸班总称", main, "禁军班直统称",
                 "建立殿前诸班同期承载节点。")
    active = node(w, touched, i, "外殿直", "机构", "宋代",
                  "殿前诸班之一，皇宫近卫禁旅", main, "殿前诸班班直",
                  "建立外殿直宋代节点。", update_event=True)
    relation(w, i, parent, active, "上下级机构", main, "外殿直隶殿前司。")
    group_relation(w, i, group, active, main, "外殿直是殿前诸班之一。")
    node(w, touched, i, "外殿直", "机构", "北宋熙宁五年", "废罢", main,
         "废罢班直", "记录熙宁五年废罢。", update_event=True)
    finish(w, touched, "整理外殿直的殿前司隶属、殿前诸班实例关系与熙宁废罢。")


def entry1200(): paired_class_entry(1200)


def main():
    for i in range(1181, 1201):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
