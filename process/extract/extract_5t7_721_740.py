#!/usr/bin/env python3
"""提取 chapter5t7 第721-740条：审计粮勾六院、省仓与编估打套局。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_701_720 as previous


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


F = {i: load(i) for i in range(721, 741)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
field = base.field
cite = base.cite
state = base.state
relation = base.relation
staff = base.staff
alias_note = base.alias_note


TIME_HINTS = {
    "北宋元丰二年六月九日以前": 1079.44,
    "北宋元丰二年六月九日": 1079.45,
    "北宋元丰二年六月九日以后": 1079.46,
    "北宋绍圣二年": 1095,
    "宋代（未载具体年月）": 1100,
    "南宋初": 1127.05,
    "南宋建炎元年五月十一日": 1127.36,
    "南宋": 1130,
    "南宋（监官改干办官后）": 1130.2,
    "南宋绍兴七年正月二十八日": 1137.08,
    "南宋绍兴八年五月二十六日": 1138.40,
    "南宋绍兴八年后": 1138.5,
    "南宋绍兴九年后": 1139.1,
    "南宋绍兴十一年六月六日": 1141.45,
    "南宋绍兴二十七年": 1157,
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


def node(w, touched, i, title, type_, time, event, quotation, category,
         decision, field_name=None, *, officer=None, grade=None):
    eid, tid = state(
        w, i, title, type_, time, event, quotation, category, decision,
        field_name, officer=officer, grade=grade,
    )
    touched.add(eid)
    return tid


def parent_child(w, touched, i, parent, child, time, quotation, decision,
                 field_name=None, *, parent_event=None, child_event=None):
    parent_tid = node(
        w, touched, i, parent, "机构", time,
        parent_event or f"统辖{child}", quotation, "上级机构",
        f"建立或复用{parent}{time}节点。", field_name,
    )
    child_tid = node(
        w, touched, i, child, "机构", time,
        child_event or f"隶属{parent}", quotation, "所属机构",
        f"建立或复用{child}{time}节点。", field_name,
    )
    relation(w, i, parent_tid, child_tid, "上下级机构", quotation,
             decision, field_name)
    return parent_tid, child_tid


def office_staff(w, touched, i, office, post, time, quotation, decision,
                 field_name=None, *, quota=None, staff_type="官",
                 office_event=None, post_event=None, officer=None):
    office_tid = node(
        w, touched, i, office, "机构", time,
        office_event or f"设置{post}", quotation, "办事机构",
        f"建立或复用{office}{time}编制节点。", field_name,
    )
    post_tid = node(
        w, touched, i, post, "官职", time,
        post_event or f"领{office}事", quotation, "差遣官",
        f"建立或复用{post}{time}节点。", field_name, officer=officer,
    )
    staff(w, i, office_tid, post_tid, quotation, decision, field_name,
          quota=quota, staff_type=staff_type)
    return office_tid, post_tid


def group_members(w, touched, i, group_title, group_type, time, event,
                  members, quotation, decision, field_name=None):
    group_tid = node(
        w, touched, i, group_title, group_type, time, event, quotation,
        f"{group_type}统称", f"建立{group_title}{time}统称节点。", field_name,
    )
    for member_title, member_type in members:
        member_tid = node(
            w, touched, i, member_title, member_type, time,
            f"{group_title}在{time}所指实例", quotation,
            f"{group_title}实例", f"建立或复用{member_title}{time}实例节点。",
            field_name,
        )
        relation(w, i, group_tid, member_tid, "统称与实例", quotation,
                 f"{member_title}是{group_title}的实例。", field_name)
    return group_tid


def entry721():
    i = 721
    main, aliases = F[i]["text"], field(i, "简称")
    w, touched = W(i), set()
    north = node(
        w, touched, i, "勾当诸军专勾司公事", "官职",
        "北宋元丰二年六月九日", "北宋勾当诸军审计司官，领本司事",
        main, "审计司差遣", "复用北宋勾当诸军专勾司公事节点。",
    )
    _, south = office_staff(
        w, touched, i, "诸军审计司", "干办行在诸军审计司",
        "南宋（监官改干办官后）", main,
        "南宋诸军审计司改用干办官领本司事。", staff_type="干办官",
        office_event="改用干办官领司事",
        post_event="由北宋勾当官改称，领本司事，属六院官",
    )
    relation(w, i, north, south, "前后演变", main,
             "北宋诸军专勾司勾当官至南宋改称干办官。")
    alias_note(w, i, south, aliases, "简称")
    finish(w, touched, "整理干办行在诸军审计司南北沿革及简称证据链。")


def entry722():
    i = 722
    main = F[i]["text"]
    origin, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    office = node(
        w, touched, i, "诸司专勾司", "机构", "北宋元丰二年六月九日",
        "始置，审核百官廪禄券历", origin, "百官俸禄审计机构",
        "建立诸司专勾司始置节点。", "职源与沿革",
    )
    # “提举诸司库务司”是正式词头“都大提举在京诸司库务司”的简称，
    # 不另建别名实体。正式机构1078年已罢，而诸司专勾司1079年始置，
    # 所以原书“先隶提举司”的概括关系保留冲突标记，但不能复活父机构。
    old_parent = node(
        w, touched, i, "都大提举在京诸司库务司", "机构",
        "北宋熙宁六年正月五日", "统辖在京诸司库务",
        main, "在京库务管理机构", "复用正式词头的罢置前节点。",
    )
    conflict_note = (
        "都大提举在京诸司库务司1078年已罢，早于诸司专勾司1079年始置；"
        "原书未给出可落实到具体年份的重叠期。"
    )
    old_relation = w.relationship(
        old_parent, office, "上下级机构",
        "以正式词头保存原书的先隶关系，但不据此延长已罢机构。", main,
    )
    cite(
        w, "Relationships", old_relation, i, main,
        "保存原书先隶关系及与确切纪年的冲突。",
        note=conflict_note, conflict_flag=1,
    )
    later_parent = node(
        w, touched, i, "太府寺", "机构", "北宋元丰新制",
        "元丰新制后统辖诸司专勾司", main, "中央财赋机构",
        "建立或复用太府寺元丰新制节点。",
    )
    relation(
        w, i, later_parent, office, "上下级机构", main,
        "原书顺序为后隶太府寺；落实到元丰新制节点。",
    )
    cite(w, "Timepoints", office, i, duty,
         "补证诸司专勾司审核百官廪禄券历职掌。", "职掌")
    office_staff(
        w, touched, i, "诸司专勾司", "勾当诸司专勾司公事",
        "北宋元丰二年六月九日", roster,
        "诸司专勾司置勾当官二员分左右厅。", "编制", quota=2,
        staff_type="勾当官", office_event="设置勾当官二员分左右厅",
        post_event="分左右厅领诸司专勾司事",
    )
    alias_note(w, i, office, aliases, "简称")
    finish(w, touched, "整理诸司专勾司始置、隶属、职掌与编制链。")


def entry723():
    i, quote = 723, F[723]["text"]
    w, touched = W(i), set()
    source = node(
        w, touched, i, "诸司专勾司", "机构", "南宋建炎元年五月十一日",
        "避高宗讳改称诸司审计司", quote, "百官俸禄审计机构",
        "建立诸司专勾司建炎改名节点。",
    )
    target = node(
        w, touched, i, "诸司审计司", "机构", "南宋建炎元年五月十一日",
        "由诸司专勾司改称，冠以行在之名", quote, "百官俸禄审计机构",
        "建立诸司审计司改称节点。",
    )
    relation(w, i, source, target, "前后演变", quote,
             "建炎元年诸司专勾司避讳改称诸司审计司。")
    office_staff(
        w, touched, i, "诸司审计司", "监行在诸司审计司", "南宋初",
        quote, "诸司审计司初设监官。", staff_type="监官",
        office_event="初设监官，后改用干办官二员", post_event="初领本司事",
    )
    _, dry = office_staff(
        w, touched, i, "诸司审计司", "干办行在诸司审计司",
        "南宋（监官改干办官后）", quote,
        "诸司审计司后改用干办官二员。", quota=2, staff_type="干办官",
        office_event="改用干办官二员", post_event="领本司事",
    )
    monitor = node(
        w, touched, i, "监行在诸司审计司", "官职", "南宋初",
        "初设监官领诸司审计司事", quote, "审计司差遣",
        "复用诸司审计司监官节点。",
    )
    relation(w, i, monitor, dry, "前后演变", quote,
             "诸司审计司初设监官，后改用干办官。")
    finish(w, touched, "整理诸司专勾司改诸司审计司及监干办编制链。")


def entry724():
    i = 724
    main, aliases = F[i]["text"], field(i, "简称")
    w, touched = W(i), set()
    _, post = office_staff(
        w, touched, i, "诸司审计司", "监行在诸司审计司", "南宋初",
        main, "南宋初诸司审计司置监官领本司事。", staff_type="监官",
        office_event="南宋初设置监官", post_event="领本司事",
    )
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理监行在诸司审计司编制及简称证据链。")


def entry725():
    i = 725
    main, aliases = F[i]["text"], field(i, "简称")
    w, touched = W(i), set()
    north = node(
        w, touched, i, "勾当诸司专勾司公事", "官职",
        "北宋元丰二年六月九日", "北宋勾当诸司审计司官，领本司事",
        main, "审计司差遣", "复用北宋勾当诸司专勾司公事节点。",
    )
    _, south = office_staff(
        w, touched, i, "诸司审计司", "干办行在诸司审计司",
        "南宋（监官改干办官后）", main,
        "南宋诸司审计司置干办官二员。", quota=2, staff_type="干办官",
        office_event="改置干办官二员",
        post_event="由北宋勾当官改称，领本司事，属六院官",
    )
    relation(w, i, north, south, "前后演变", main,
             "北宋诸司专勾司勾当官至南宋改称干办官。")
    alias_note(w, i, south, aliases, "简称")
    finish(w, touched, "整理干办行在诸司审计司沿革、编制及简称链。")


def entry726():
    i = 726
    main, aliases = F[i]["text"], field(i, "简称与别名")
    w, touched = W(i), set()
    group_members(
        w, touched, i, "专勾司", "机构", "北宋元丰二年六月九日以前",
        "马军专勾司、步军专勾司的通称",
        [(x, "机构") for x in ("马军专勾司", "步军专勾司")],
        main, "建立元丰二年前专勾司所指实例。",
    )
    later = group_members(
        w, touched, i, "专勾司", "机构", "北宋元丰二年六月九日以后",
        "诸司专勾司、诸军专勾司的通称",
        [(x, "机构") for x in ("诸司专勾司", "诸军专勾司")],
        main, "建立元丰二年后专勾司所指实例。",
    )
    alias_note(w, i, later, aliases, "简称与别名")
    finish(w, touched, "整理专勾司前后两组实例及别名证据链。")


def entry727():
    i = 727
    main, aliases = F[i]["text"], field(i, "简称与别名")
    w, touched = W(i), set()
    group = group_members(
        w, touched, i, "审计司", "机构", "南宋",
        "诸司审计司、诸军审计司通称",
        [(x, "机构") for x in ("诸司审计司", "诸军审计司")],
        main, "建立南宋审计司及两司实例。",
    )
    alias_note(w, i, group, aliases, "简称与别名")
    finish(w, touched, "整理审计司统称、实例及别名证据链。")


def entry728():
    i, quote = 728, F[728]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "粮勾院", "机构", "北宋绍圣二年",
        "诸司、诸军粮料院与诸司、诸军专勾司合称",
        [(x, "机构") for x in (
            "诸司粮料院", "诸军粮料院", "诸司专勾司", "诸军专勾司",
        )], quote, "建立粮勾院及四机构实例。",
    )
    finish(w, touched, "整理北宋粮勾院统称与四机构实例链。")


def entry729():
    i = 729
    main, aliases = F[i]["text"], field(i, "简称")
    w, touched = W(i), set()
    group = group_members(
        w, touched, i, "行在粮审院", "机构", "南宋",
        "行在诸司、诸军粮料院与诸军、诸司审计司合称",
        [(x, "机构") for x in (
            "诸司粮料院", "诸军粮料院", "诸军审计司", "诸司审计司",
        )], main, "建立行在粮审院及四机构实例。",
    )
    alias_note(w, i, group, aliases, "简称")
    finish(w, touched, "整理行在粮审院统称、实例及简称证据链。")


def entry730():
    i, quote = 730, F[730]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "干办审计司", "官职", "南宋",
        "干办行在诸司审计司、干办行在诸军审计司官通称",
        [(x, "官职") for x in (
            "干办行在诸司审计司", "干办行在诸军审计司",
        )], quote, "建立干办审计司及两差遣实例。",
    )
    finish(w, touched, "整理干办审计司统称与两差遣实例链。")


def entry731():
    i = 731
    main, aliases = F[i]["text"], field(i, "简称")
    w, touched = W(i), set()
    members = (
        "监登闻鼓院", "监登闻检院", "干办行在诸司粮料院",
        "干办行在诸军粮料院", "干办行在诸军审计司",
        "干办行在诸司审计司", "主管官告院", "监都进奏院",
    )
    group = group_members(
        w, touched, i, "六院官", "官职", "南宋",
        "八类差遣共十三员的总名，为省郎、察官之储",
        [(x, "官职") for x in members], main,
        "建立六院官统称及八类差遣实例。",
    )
    alias_note(w, i, group, aliases, "简称")
    finish(w, touched, "整理六院官统称、十三员构成与简称证据链。")


def entry732():
    i = 732
    main, aliases = F[i]["text"], field(i, "简称")
    w, touched = W(i), set()
    post = node(
        w, touched, i, "干办户部分差审计司", "官职",
        "宋代（未载具体年月）", "领分差审计司，审核诸大军钱粮俸料券历",
        main, "分差审计司差遣", "建立干办户部分差审计司节点。",
    )
    for office in ("鄂州分差审计司", "建康分差审计司", "镇江分差审计司"):
        office_tid = node(
            w, touched, i, office, "机构", "宋代（未载具体年月）",
            "与所在地户部分差粮料院同时设置", main, "分差审计司",
            f"建立{office}节点。",
        )
        staff(w, i, office_tid, post, main, f"{office}设干办官。",
              staff_type="干办官")
    alias_note(w, i, post, aliases, "简称")
    finish(w, touched, "整理三处分差审计司、干办官与简称证据链。")


def entry733():
    i, quote = 733, F[733]["text"]
    w, touched = W(i), set()
    members = (
        "分差鄂州户部粮料院", "分差建康府诸军粮料院",
        "分差镇江府诸军、诸司粮料院", "鄂州分差审计司",
        "建康分差审计司", "镇江分差审计司",
    )
    group_members(
        w, touched, i, "鄂州、建康、镇江分差粮审院", "机构",
        "宋代（未载具体年月）", "三地粮料院与审计司的合称",
        [(x, "机构") for x in members], quote,
        "建立三地分差粮审院统称及六机构实例。",
    )
    finish(w, touched, "整理三地分差粮审院统称与粮料、审计实例链。")


def provincial_warehouse(i, title, event):
    quote = F[i]["text"]
    w, touched = W(i), set()
    source = node(
        w, touched, i, "行在省仓", "机构", "南宋绍兴十一年六月六日",
        "分为上、中、下三界", quote, "行在粮仓",
        "建立或复用行在省仓三分节点。",
    )
    target = node(
        w, touched, i, title, "机构", "南宋绍兴十一年六月六日",
        event, quote, "行在省仓分界", f"建立{title}分置节点。",
    )
    relation(w, i, source, target, "前后演变", quote,
             f"绍兴十一年分行在省仓为三界，置{title}。")
    finish(w, touched, f"整理{title}由行在省仓分置的时间链。")


def entry734():
    provincial_warehouse(
        734, "行在省仓上界",
        "由省仓南仓分置，辖八敖，受白苗米供宫人、百官、宗室、内侍",
    )


def entry735():
    provincial_warehouse(
        735, "行在省仓中界",
        "由省仓北仓分置，辖敖三十七，受次苗米供卫士及五军",
    )


def entry736():
    provincial_warehouse(
        736, "行在省仓下界",
        "由省仓东仓分置，建敖屋八十，受粮米备诸军月粮",
    )


def entry737():
    i, quote = 737, F[737]["text"]
    w, touched = W(i), set()
    source = node(
        w, touched, i, "北省仓", "机构", "南宋初",
        "南宋初设置，储诸路上供岁余粮", quote, "行在粮仓",
        "建立丰储仓前身北省仓节点。",
    )
    target = node(
        w, touched, i, "丰储仓", "机构", "南宋绍兴二十七年",
        "北省仓始易丰储之名，储额百万石备水旱军粮", quote,
        "行在粮仓", "建立丰储仓改名节点。",
    )
    relation(w, i, source, target, "前后演变", quote,
             "绍兴二十七年北省仓改称丰储仓。")
    finish(w, touched, "整理北省仓改丰储仓及其储粮职掌链。")


def entry738():
    i, quote = 738, F[738]["text"]
    w, touched = W(i), set()
    group_members(
        w, touched, i, "编套二局", "机构", "南宋",
        "编估局、打套局的合称",
        [(x, "机构") for x in ("编估局", "打套局")], quote,
        "建立编套二局及编估、打套两局实例。",
    )
    finish(w, touched, "整理编套二局统称与两局实例链。")


def entry739():
    i = 739
    main = F[i]["text"]
    origin, duty, roster, aliases = (
        field(i, "职源"), field(i, "职掌"), field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "太府寺", "编估局", "南宋绍兴八年五月二十六日",
        main, "编估局隶太府寺。",
        parent_event="统辖编估局", child_event="已见编估局之称，隶太府寺",
    )
    early = node(
        w, touched, i, "编估局", "机构", "南宋绍兴七年正月二十八日",
        "始见编估职事", origin, "市舶杂物编估机构",
        "建立编估职事始见节点。", "职源",
    )
    named = node(
        w, touched, i, "编估局", "机构", "南宋绍兴八年五月二十六日",
        "已见编估局之称", origin, "市舶杂物编估机构",
        "建立编估局得名节点。", "职源",
    )
    cite(w, "Timepoints", named, i, duty,
         "补证编估局编类、分拣、定等估价并送复估职掌。", "职掌")
    left_post = node(
        w, touched, i, "左藏库都中门官", "官职",
        "南宋绍兴八年五月二十六日", "初兼编估局监官", roster,
        "左藏库官", "建立左藏库都中门官兼编估节点。", "编制",
    )
    staff(w, i, named, left_post, roster, "编估局初由左藏库监中门官兼领。",
          "编制", staff_type="兼监官")
    office_staff(
        w, touched, i, "编估局", "监编估局", "南宋绍兴九年后", roster,
        "绍兴九年后编估局专设监官一员。", "编制", quota=1,
        staff_type="监官", office_event="专设监官一员",
        post_event="专监编估局事",
    )
    office_staff(
        w, touched, i, "编估局", "手分", "南宋绍兴九年后", roster,
        "编估局置手分二人。", "编制", quota=2, staff_type="吏",
        office_event="设置监官一员、手分二人", post_event="编估局吏额",
    )
    alias_note(w, i, named, aliases, "简称")
    finish(w, touched, "整理编估局始见、隶属、职掌、监官与吏额链。")


def entry740():
    i = 740
    main = F[i]["text"]
    origin, duty, roster, aliases = (
        field(i, "职源"), field(i, "职掌"), field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "太府寺", "打套局", "南宋绍兴八年五月二十六日",
        main, "打套局隶太府寺。",
        parent_event="统辖打套局", child_event="已见打套局之名，隶太府寺",
    )
    node(
        w, touched, i, "打套局", "机构", "南宋绍兴七年正月二十八日",
        "始见打套职事", origin, "市舶杂物拍卖机构",
        "建立打套职事始见节点。", "职源",
    )
    named = node(
        w, touched, i, "打套局", "机构", "南宋绍兴八年五月二十六日",
        "已见打套局之名", origin, "市舶杂物拍卖机构",
        "建立打套局得名节点。", "职源",
    )
    cite(w, "Timepoints", named, i, duty,
         "补证打套局登记、编排并拍卖编估杂物职掌。", "职掌")
    for post, staff_type in (("交引库监官", "兼监官"), ("太府寺丞", "兼监官")):
        post_tid = node(
            w, touched, i, post, "官职", "南宋绍兴八年五月二十六日",
            "初兼打套局监官", roster, "太府寺或库务官",
            f"建立或复用{post}兼监打套局节点。", "编制",
        )
        staff(w, i, named, post_tid, roster, f"打套局初由{post}兼监。",
              "编制", staff_type=staff_type)
    office_staff(
        w, touched, i, "打套局", "监打套局", "南宋绍兴八年后", roster,
        "绍兴八年后专设监打套局官一员。", "编制", quota=1,
        staff_type="监官", office_event="专设监官一员",
        post_event="专监打套局事",
    )
    for post, staff_type in (("库经司", "吏"), ("监编估、打套局门官", "门官")):
        office_staff(
            w, touched, i, "打套局", post, "南宋绍兴八年后", roster,
            f"打套局置{post}一人。", "编制", quota=1, staff_type=staff_type,
            office_event="形成监官与吏额", post_event="打套局吏额",
        )
    alias_note(w, i, named, aliases, "简称")
    finish(w, touched, "整理打套局始见、隶属、职掌、兼监与专监吏额链。")


def main():
    for i in range(721, 741):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
