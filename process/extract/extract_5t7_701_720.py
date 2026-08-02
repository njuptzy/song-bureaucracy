#!/usr/bin/env python3
"""提取 chapter5t7 第701-720条：蔡河锁、香药库、粮料院与诸军审计司。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_681_700 as previous


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


F = {i: load(i) for i in range(701, 721)}
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
    "唐代": 700,
    "宋初": 960,
    "北宋太平兴国五年正月二十八日": 980.08,
    "北宋太平兴国八年": 983,
    "北宋雍熙四年后": 987.9,
    "北宋景德四年闰五月": 1007.45,
    "北宋天禧五年六月十七日": 1021.46,
    "北宋（先后隶属）": 1050,
    "宋代（未载具体年月）": 1050.2,
    "北宋元丰二年六月九日": 1079.45,
    "北宋元丰末": 1085,
    "北宋元丰改制": 1082.1,
    "南宋初": 1127.05,
    "南宋建炎元年五月十一日": 1127.36,
    "南宋建炎三年": 1129,
    "南宋": 1130,
    "南宋（监官改干办官后）": 1130.2,
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


def mark_conflict(w, i, target_id, quotation, field_name, note):
    citation_label = base.C(i, field_name)
    row = w.conn.execute(
        "select id,conflict_flag,note from Citations where target_table='Timepoints' "
        "and target_id=? and citation=? and quotation=?",
        (target_id, citation_label, quotation),
    ).fetchone()
    assert row, (i, target_id, field_name)
    if row[1] != 1 or row[2] != note:
        w.conn.execute(
            "update Citations set conflict_flag=1,note=? where id=?", (note, row[0])
        )
        w._br("Citations", row[0], f"标记辞典条目间纪年冲突：{note}")


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
    relation(
        w, i, parent_tid, child_tid, "上下级机构", quotation, decision,
        field_name,
    )
    return parent_tid, child_tid


def office_staff(w, touched, i, office, post, time, quotation, decision,
                 field_name=None, *, quota=None, staff_type="官",
                 office_event=None, post_event=None, officer=None):
    office_tid = node(
        w, touched, i, office, "机构", time,
        office_event or f"设置{post}", quotation, "监当或办事机构",
        f"建立或复用{office}{time}编制节点。", field_name,
    )
    post_tid = node(
        w, touched, i, post, "官职", time,
        post_event or f"领{office}事", quotation, "差遣官",
        f"建立或复用{post}{time}节点。", field_name, officer=officer,
    )
    staff(
        w, i, office_tid, post_tid, quotation, decision, field_name,
        quota=quota, staff_type=staff_type,
    )
    return office_tid, post_tid


def entry701():
    i, quote = 701, F[701]["text"]
    w, touched = W(i), set()
    parent_child(
        w, touched, i, "太府寺", "蔡河下锁", "宋代（未载具体年月）",
        quote, "蔡河下锁隶太府寺。",
        parent_event="统辖蔡河下锁税关",
        child_event="为蔡河通京师的税关，职掌与蔡河上锁同",
    )
    finish(w, touched, "整理蔡河下锁及其太府寺隶属链。")


def entry702():
    i, quote = 702, F[702]["text"]
    w, touched = W(i), set()
    group_tid = node(
        w, touched, i, "蔡河锁", "机构", "宋代（未载具体年月）",
        "蔡河上、下二锁的连称", quote, "河运税关统称",
        "建立蔡河锁统称节点。",
    )
    for title in ("蔡河上锁", "蔡河下锁"):
        member_tid = node(
            w, touched, i, title, "机构", "宋代（未载具体年月）",
            "蔡河锁所指税关实例", quote, "河运税关实例",
            f"建立或复用{title}实例节点。",
        )
        relation(
            w, i, group_tid, member_tid, "统称与实例", quote,
            f"{title}是蔡河锁的实例。",
        )
    finish(w, touched, "整理蔡河锁及上下二锁实例链。")


def entry703():
    i = 703
    main, aliases = F[i]["text"], field(i, "别名")
    w, touched = W(i), set()
    early = node(
        w, touched, i, "香药库", "机构", "北宋景德四年闰五月",
        "旧止称香药库，位于宫中，亦称内香药库", aliases,
        "香药宝石监当局", "建立天禧分库前的香药库节点。", "别名",
    )
    split = node(
        w, touched, i, "香药库", "机构", "北宋天禧五年六月十七日",
        "别置内香药库后，香药库有内、外之分", main,
        "香药宝石监当局", "建立香药库分置节点。",
    )
    inner = node(
        w, touched, i, "内香药库", "机构", "北宋天禧五年六月十七日",
        "在东华门内别置，备宫中宣索细色香药", main,
        "宫中香药库", "建立内香药库分置节点。",
    )
    outer = node(
        w, touched, i, "外香药库", "机构", "北宋天禧五年六月十七日",
        "香药库分为内、外后在城南设置", main,
        "外廷香药库", "建立外香药库分置节点。",
    )
    relation(w, i, split, inner, "前后演变", main,
             "天禧五年香药库分置内香药库。")
    relation(w, i, split, outer, "前后演变", main,
             "天禧五年香药库分置外香药库。")
    parent_child(
        w, touched, i, "太府寺", "香药库", "宋代（未载具体年月）",
        main, "香药库隶太府寺。",
        parent_event="统辖香药库", child_event="隶太府寺，掌市舶香药、宝石",
    )
    office_staff(
        w, touched, i, "香药库", "香药库监官", "宋代（未载具体年月）",
        main, "香药库设监官二人。", quota=2, staff_type="监官",
        office_event="设置监官二人",
        post_event="由京朝官、三班使臣充，监领香药库事",
        officer="京朝官、三班使臣",
    )
    cite(w, "Timepoints", early, i, aliases,
         "别名字段证明分库前香药库在宫中。", "别名")
    finish(w, touched, "整理香药库分置内外二库的时间链。")


def entry704():
    i, quote = 704, F[704]["text"]
    w, touched = W(i), set()
    tid = node(
        w, touched, i, "内香药库", "机构", "北宋天禧五年六月十七日",
        "始置于皇宫东华门内东宫南屋，贮藏细色香药备宣索", quote,
        "宫中香药库", "补证内香药库始置与职掌。",
    )
    cite(w, "Timepoints", tid, i, quote, "补证内香药库位置与职掌。")
    finish(w, touched, "补证内香药库始置节点。")


def entry705():
    i = 705
    main, aliases = F[i]["text"], field(i, "简称")
    w, touched = W(i), set()
    office_tid, post_tid = office_staff(
        w, touched, i, "内香药库", "监内香药库",
        "北宋天禧五年六月十七日", main,
        "内香药库置监官二人。", quota=2, staff_type="监官",
        office_event="始置后设置监官二人",
        post_event="掌领内香药库公事，由文臣京朝官、武臣三班使臣充",
        officer="文臣京朝官、武臣三班使臣",
    )
    alias_note(w, i, post_tid, aliases, "简称")
    finish(w, touched, "整理监内香药库编制链。")


def entry706():
    i, quote = 706, F[706]["text"]
    w, touched = W(i), set()
    outer = node(
        w, touched, i, "外香药库", "机构", "北宋天禧五年六月十七日",
        "置于开封城南曹利用故宅，掌香药并拣细色香药入内库", quote,
        "外廷香药库", "补证外香药库始置、位置与职掌。",
    )
    source = node(
        w, touched, i, "香药库", "机构", "北宋天禧五年六月十七日",
        "别置内香药库后另置外香药库", quote,
        "香药宝石监当局", "复用香药库分置节点。",
    )
    relation(w, i, source, outer, "前后演变", quote,
             "天禧五年由原香药库分置外香药库。")
    finish(w, touched, "补证外香药库分置节点。")


def entry707():
    i = 707
    main = F[i]["text"]
    origin, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    early = node(
        w, touched, i, "在京粮料院", "机构", "宋初",
        "在京师安定坊沿置，批勘文武官月俸券历", origin,
        "俸禄发放机构", "复用宋初粮料院节点。", "职源与沿革",
    )
    split = node(
        w, touched, i, "在京粮料院", "机构", "北宋太平兴国五年正月二十八日",
        "分为诸司、马军、步军三粮料院", origin,
        "俸禄发放机构", "复用粮料院一分为三节点。", "职源与沿革",
    )
    for title in ("诸司粮料院", "马军粮料院", "步军粮料院"):
        target = node(
            w, touched, i, title, "机构", "北宋太平兴国五年正月二十八日",
            "由粮料院分出", origin, "俸禄发放机构",
            f"复用{title}分置节点。", "职源与沿革",
        )
        relation(w, i, split, target, "前后演变", origin,
                 f"太平兴国五年粮料院分出{title}。", "职源与沿革")

    horse_merge = node(
        w, touched, i, "马军粮料院", "机构", "北宋太平兴国八年",
        "与步军粮料院合为一院", origin, "俸禄发放机构",
        "复用马军粮料院合并节点。", "职源与沿革",
    )
    foot_merge = node(
        w, touched, i, "步军粮料院", "机构", "北宋太平兴国八年",
        "与马军粮料院合为一院", origin, "俸禄发放机构",
        "复用步军粮料院合并节点。", "职源与沿革",
    )
    merged = node(
        w, touched, i, "马步军粮料院", "机构", "北宋太平兴国八年",
        "由马军、步军粮料院合并", origin, "俸禄发放机构",
        "复用马步军粮料院合并节点。", "职源与沿革",
    )
    relation(w, i, horse_merge, merged, "前后演变", origin,
             "太平兴国八年马军粮料院并入马步军粮料院。", "职源与沿革")
    relation(w, i, foot_merge, merged, "前后演变", origin,
             "太平兴国八年步军粮料院并入马步军粮料院。", "职源与沿革")

    merged_end = node(
        w, touched, i, "马步军粮料院", "机构", "北宋雍熙四年后",
        "复分为马军、步军粮料院", origin, "俸禄发放机构",
        "建立雍熙四年后复分节点。", "职源与沿革",
    )
    for title in ("马军粮料院", "步军粮料院"):
        target = node(
            w, touched, i, title, "机构", "北宋雍熙四年后",
            "由马步军粮料院复分", origin, "俸禄发放机构",
            f"建立{title}雍熙复分节点。", "职源与沿革",
        )
        relation(w, i, merged_end, target, "前后演变", origin,
                 f"雍熙四年后马步军粮料院复分出{title}。", "职源与沿革")

    combined = node(
        w, touched, i, "诸军粮料院", "机构", "北宋元丰末",
        "并马军、步军粮料院而成", origin, "俸禄发放机构",
        "建立本条所载元丰末诸军粮料院节点。", "职源与沿革",
    )
    mark_conflict(
        w, i, combined, origin, "职源与沿革",
        "本条记马、步军粮料院于元丰末并为诸军粮料院；第710条记元丰二年六月九日。",
    )
    for title in ("马军粮料院", "步军粮料院"):
        source = node(
            w, touched, i, title, "机构", "北宋元丰末",
            "并入诸军粮料院", origin, "俸禄发放机构",
            f"建立{title}元丰末并入节点。", "职源与沿革",
        )
        relation(w, i, source, combined, "前后演变", origin,
                 f"元丰末{title}并为诸军粮料院。", "职源与沿革")

    south = node(
        w, touched, i, "在京粮料院", "机构", "南宋",
        "在临安漾沙坑设诸司、诸军二院", main,
        "俸禄发放机构", "建立南宋临安粮料院节点。",
    )
    for title in ("诸司粮料院", "诸军粮料院"):
        member = node(
            w, touched, i, title, "机构", "南宋",
            "南宋在临安沿置", origin, "俸禄发放机构",
            f"建立{title}南宋沿置节点。", "职源与沿革",
        )
        relation(w, i, south, member, "统称与实例", origin,
                 f"南宋粮料院包括{title}。", "职源与沿革")

    for parent in ("三司", "都大提举在京诸司库务司", "太府寺"):
        parent_child(
            w, touched, i, parent, "在京粮料院", "北宋（先后隶属）",
            main, f"在京粮料院先后隶属{parent}。",
            parent_event="先后统辖在京粮料院",
            child_event="先后隶三司、都大提举在京诸司库务司、太府寺",
        )

    office_staff(
        w, touched, i, "在京粮料院", "在京都粮料使", "宋初", roster,
        "宋初在京粮料院设都粮料使。", "编制", staff_type="都粮料使",
        office_event="设置都粮料使", post_event="领在京粮料院事",
    )
    cite(w, "Timepoints", early, i, duty, "补证粮料院批勘券历职掌。", "职掌")
    alias_note(w, i, south, aliases, "简称")
    finish(w, touched, "整理在京粮料院合分、隶属、职掌与南宋沿置链。")


def entry708():
    i, quote = 708, F[708]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "诸司粮料院", "监行在诸司粮料院", "南宋初",
        quote, "南宋初诸司粮料院置监官领院事。", staff_type="监官",
        office_event="南宋初沿置并设监官", post_event="领本院事，后改用干办官",
    )
    finish(w, touched, "整理监行在诸司粮料院编制链。")


def entry709():
    i = 709
    main, aliases = F[i]["text"], field(i, "简称")
    w, touched = W(i), set()
    office_tid, post_tid = office_staff(
        w, touched, i, "诸司粮料院", "干办行在诸司粮料院",
        "南宋（监官改干办官后）", main,
        "南宋诸司粮料院以干办官领事。", staff_type="干办官",
        office_event="改由干办官领院事",
        post_event="由粮料院勾当官改称，属六院官，为储才之地",
    )
    monitor = node(
        w, touched, i, "监行在诸司粮料院", "官职", "南宋初",
        "初置以领诸司粮料院事，后改用干办官", main,
        "粮料院差遣", "复用监行在诸司粮料院前身节点。",
    )
    relation(w, i, monitor, post_tid, "前后演变", main,
             "南宋诸司粮料院监官后改为干办官。")
    alias_note(w, i, post_tid, aliases, "简称")
    finish(w, touched, "整理干办行在诸司粮料院沿革及编制链。")


def entry710():
    i = 710
    main = F[i]["text"]
    origin, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    combined = node(
        w, touched, i, "诸军粮料院", "机构", "北宋元丰二年六月九日",
        "合马军、步军粮料院而置", origin, "俸禄发放机构",
        "建立本条所载元丰二年诸军粮料院节点。", "职源与沿革",
    )
    mark_conflict(
        w, i, combined, origin, "职源与沿革",
        "本条记元丰二年六月九日合为诸军粮料院；第707条记元丰末。",
    )
    for title in ("马军粮料院", "步军粮料院"):
        source = node(
            w, touched, i, title, "机构", "北宋元丰二年六月九日",
            "合并为诸军粮料院", origin, "俸禄发放机构",
            f"建立{title}元丰二年合并节点。", "职源与沿革",
        )
        relation(w, i, source, combined, "前后演变", origin,
                 f"元丰二年{title}并为诸军粮料院。", "职源与沿革")
    parent_child(
        w, touched, i, "太府寺", "诸军粮料院", "宋代（未载具体年月）",
        main, "诸军粮料院隶太府寺。",
        parent_event="统辖诸军粮料院", child_event="隶太府寺",
    )
    south = node(
        w, touched, i, "诸军粮料院", "机构", "南宋",
        "沿置并冠以行在之名", origin, "俸禄发放机构",
        "建立诸军粮料院南宋沿置节点。", "职源与沿革",
    )
    cite(w, "Timepoints", combined, i, duty,
         "补证诸军粮料院批勘俸禄券历职掌。", "职掌")
    office_staff(
        w, touched, i, "诸军粮料院", "勾当诸军粮料院公事",
        "北宋元丰二年六月九日", roster,
        "北宋诸军粮料院置勾当官一员。", "编制", quota=1,
        staff_type="勾当官", office_event="设置勾当官一员",
        post_event="领诸军粮料院事",
    )
    office_staff(
        w, touched, i, "诸军粮料院", "监行在诸军粮料院", "南宋初",
        roster, "南宋初诸军粮料院置监官。", "编制", staff_type="监官",
        office_event="南宋初设置监官", post_event="领诸军粮料院事",
    )
    _, dry_post = office_staff(
        w, touched, i, "诸军粮料院", "干办行在诸军粮料院", "南宋",
        roster, "南宋诸军粮料院改置干办官二员。", "编制", quota=2,
        staff_type="干办官", office_event="改置干办官二员",
        post_event="领诸军粮料院事，一员在临安，一员分差建康",
    )
    for title, quota in (("主押官", 1), ("前行", 4), ("后行", 10), ("贴司", 3)):
        office_staff(
            w, touched, i, "诸军粮料院", title, "南宋建炎三年", roster,
            f"建炎三年诸军粮料院置{title}{quota}名。", "编制",
            quota=quota, staff_type=title,
            office_event="形成建炎三年吏额", post_event="诸军粮料院吏额",
        )
    alias_note(w, i, south, aliases, "简称")
    finish(w, touched, "整理诸军粮料院合并、南宋沿置、职掌与编制链。")


def entry711():
    i, quote = 711, F[711]["text"]
    w, touched = W(i), set()
    office_tid, monitor = office_staff(
        w, touched, i, "诸军粮料院", "监行在诸军粮料院", "南宋初",
        quote, "南宋初诸军粮料院曾置监官领院事。", staff_type="监官",
        office_event="南宋初设置监官", post_event="领院事，后改用干办官",
    )
    dry = node(
        w, touched, i, "干办行在诸军粮料院", "官职",
        "南宋（监官改干办官后）", "由监官改置，领诸军粮料院事", quote,
        "粮料院差遣", "建立后继干办官节点。",
    )
    relation(w, i, monitor, dry, "前后演变", quote,
             "监行在诸军粮料院后改用干办官。")
    finish(w, touched, "整理监行在诸军粮料院改干办官链。")


def entry712():
    i, quote = 712, F[712]["text"]
    w, touched = W(i), set()
    _, north = office_staff(
        w, touched, i, "诸军粮料院", "勾当诸军粮料院公事",
        "北宋元丰二年六月九日", quote,
        "北宋诸军粮料院置勾当公事官。", staff_type="勾当官",
        office_event="设置勾当公事官", post_event="领诸军粮料院事",
    )
    _, south = office_staff(
        w, touched, i, "诸军粮料院", "干办行在诸军粮料院",
        "南宋（监官改干办官后）", quote,
        "南宋诸军粮料院勾当官改称干办官。", staff_type="干办官",
        office_event="改由干办官领事",
        post_event="领诸军粮料院事，属六院官，为储才之地",
    )
    relation(w, i, north, south, "前后演变", quote,
             "北宋勾当诸军粮料院公事至南宋改称干办官。")
    finish(w, touched, "整理干办行在诸军粮料院南北沿革链。")


def local_grain_office(i, office, time="宋代（未载具体年月）"):
    quote = F[i]["text"]
    w, touched = W(i), set()
    office_tid = node(
        w, touched, i, office, "机构", time, quote, quote,
        "分差粮料院", f"建立{office}节点。",
    )
    monitor_title = f"{office}监官"
    monitor_tid = node(
        w, touched, i, monitor_title, "官职", time,
        f"置监官一员，领{office}事", quote, "监当官",
        f"建立{office}监官节点。",
    )
    staff(w, i, office_tid, monitor_tid, quote, f"{office}置监官一员。",
          quota=1, staff_type="监官")
    finish(w, touched, f"整理{office}及监官编制链。")


def entry713():
    i, quote = 713, F[713]["text"]
    w, touched = W(i), set()
    office = "分差建康府诸军粮料院"
    office_tid = node(
        w, touched, i, office, "机构", "南宋", "设于建康府，支拨淮西军钱粮",
        quote, "分差粮料院", "建立建康府诸军粮料院节点。",
    )
    dry = node(
        w, touched, i, "干办行在诸军粮料院", "官职", "南宋",
        "兼领分差建康府诸军粮料院", quote, "粮料院差遣",
        "复用干办行在诸军粮料院兼领节点。",
    )
    staff(w, i, office_tid, dry, quote,
          "分差建康府诸军粮料院由干办行在诸军粮料院官兼领。",
          staff_type="兼领官")
    monitor = node(
        w, touched, i, f"{office}监官", "官职", "南宋",
        "置一员，掌支拨淮西军钱粮", quote, "监当官",
        "建立建康府诸军粮料院监官节点。",
    )
    staff(w, i, office_tid, monitor, quote,
          "分差建康府诸军粮料院置监官一员。", quota=1, staff_type="监官")
    finish(w, touched, "整理建康分差诸军粮料院及兼领、监官编制链。")


def entry714():
    local_grain_office(714, "分差镇江府诸军、诸司粮料院")


def entry715():
    local_grain_office(715, "分差鄂州户部粮料院")


def entry716():
    local_grain_office(716, "总领四川财赋军马钱粮所干办行在分差户部利州粮料院")


def entry717():
    i = 717
    main, aliases = F[i]["text"], field(i, "简称")
    w, touched = W(i), set()
    office = "总领四川财赋军马钱粮所干办行在分差户部鱼关粮料院"
    office_tid = node(
        w, touched, i, office, "机构", "宋代（未载具体年月）",
        "设于鱼关，支拨四川驻扎大军钱粮", main,
        "分差粮料院", "建立鱼关粮料院节点。",
    )
    monitor = node(
        w, touched, i, f"{office}监官", "官职", "宋代（未载具体年月）",
        "置监官一员", main, "监当官", "建立鱼关粮料院监官节点。",
    )
    staff(w, i, office_tid, monitor, main, "鱼关粮料院置监官一员。",
          quota=1, staff_type="监官")
    alias_note(w, i, office_tid, aliases, "简称")
    finish(w, touched, "整理鱼关粮料院、监官与简称证据链。")


def entry718():
    i, quote = 718, F[718]["text"]
    w, touched = W(i), set()
    group = node(
        w, touched, i, "分差粮料院", "机构", "宋代（未载具体年月）",
        "建康、镇江、鄂州、利州、鱼关诸军分差粮料院的通称", quote,
        "分差粮料院统称", "建立分差粮料院统称节点。",
    )
    members = (
        "分差建康府诸军粮料院",
        "分差镇江府诸军、诸司粮料院",
        "分差鄂州户部粮料院",
        "总领四川财赋军马钱粮所干办行在分差户部利州粮料院",
        "总领四川财赋军马钱粮所干办行在分差户部鱼关粮料院",
    )
    for title in members:
        member = node(
            w, touched, i, title, "机构", "宋代（未载具体年月）",
            "分差粮料院实例", quote, "分差粮料院实例",
            f"建立或复用{title}实例节点。",
        )
        relation(w, i, group, member, "统称与实例", quote,
                 f"{title}是分差粮料院实例。")
    finish(w, touched, "整理分差粮料院及五处实例链。")


def entry719():
    i = 719
    main = F[i]["text"]
    origin, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "简称"),
    )
    w, touched = W(i), set()
    combined = node(
        w, touched, i, "诸军专勾司", "机构", "北宋元丰二年六月九日",
        "合马军、步军专勾司而置", origin, "军俸审计机构",
        "建立诸军专勾司始置节点。", "职源与沿革",
    )
    for title in ("马军专勾司", "步军专勾司"):
        source = node(
            w, touched, i, title, "机构", "北宋元丰二年六月九日",
            "合并为诸军专勾司", origin, "军籍审核机构",
            f"建立{title}元丰二年合并节点。", "职源与沿革",
        )
        relation(w, i, source, combined, "前后演变", origin,
                 f"元丰二年{title}合并为诸军专勾司。", "职源与沿革")
    # “提举诸司库务司”是正式词头“都大提举在京诸司库务司”的简称，
    # 不另建别名实体。正式机构1078年已罢，而诸军专勾司1079年始置，
    # 所以原书“先隶提举司”的概括关系保留冲突标记，但不能复活父机构。
    old_parent = node(
        w, touched, i, "都大提举在京诸司库务司", "机构",
        "北宋熙宁六年正月五日", "统辖在京诸司库务",
        main, "在京库务管理机构", "复用正式词头的罢置前节点。",
    )
    conflict_note = (
        "都大提举在京诸司库务司1078年已罢，早于诸军专勾司1079年始置；"
        "原书未给出可落实到具体年份的重叠期。"
    )
    old_relation = w.relationship(
        old_parent, combined, "上下级机构",
        "以正式词头保存原书的先隶关系，但不据此延长已罢机构。", main,
    )
    cite(
        w, "Relationships", old_relation, i, main,
        "保存原书先隶关系及与确切纪年的冲突。",
        note=conflict_note, conflict_flag=1,
    )
    later_parent = node(
        w, touched, i, "太府寺", "机构", "北宋元丰新制",
        "元丰新制后统辖诸军专勾司", main, "中央财赋机构",
        "建立或复用太府寺元丰新制节点。",
    )
    relation(
        w, i, later_parent, combined, "上下级机构", main,
        "原书顺序为后隶太府寺；落实到元丰新制节点。",
    )
    cite(w, "Timepoints", combined, i, duty,
         "补证诸军专勾司审核粮料券历职掌。", "职掌")
    office_staff(
        w, touched, i, "诸军专勾司", "勾当诸军专勾司公事",
        "北宋元丰二年六月九日", roster,
        "诸军专勾司置勾当官二员，分左右厅治事。", "编制",
        quota=2, staff_type="勾当官", office_event="设置勾当官二员分左右厅",
        post_event="分左右厅领诸军专勾司事",
    )
    alias_note(w, i, combined, aliases, "简称")
    finish(w, touched, "整理诸军专勾司始置、隶属、职掌与编制链。")


def entry720():
    i, quote = 720, F[720]["text"]
    w, touched = W(i), set()
    source = node(
        w, touched, i, "诸军专勾司", "机构", "南宋建炎元年五月十一日",
        "因避高宗赵构讳改称诸军审计司", quote, "军俸审计机构",
        "建立诸军专勾司建炎改名节点。",
    )
    target = node(
        w, touched, i, "诸军审计司", "机构", "南宋建炎元年五月十一日",
        "由诸军专勾司改称，冠以行在之名", quote, "军俸审计机构",
        "建立诸军审计司改称节点。",
    )
    relation(w, i, source, target, "前后演变", quote,
             "建炎元年诸军专勾司避讳改称诸军审计司。")
    monitor = node(
        w, touched, i, "监行在诸军审计司", "官职", "南宋初",
        "诸军审计司初设监官领司事", quote, "审计司差遣",
        "建立监行在诸军审计司节点。",
    )
    office = node(
        w, touched, i, "诸军审计司", "机构", "南宋初",
        "初设监官，后设干办审计司官二员", quote, "军俸审计机构",
        "建立诸军审计司南宋初编制节点。",
    )
    staff(w, i, office, monitor, quote, "诸军审计司初设监官。",
          staff_type="监官")
    dry = node(
        w, touched, i, "干办行在诸军审计司", "官职",
        "南宋（监官改干办官后）", "领诸军审计司事，编制二员", quote,
        "审计司差遣", "建立干办行在诸军审计司节点。",
    )
    staff(w, i, office, dry, quote, "诸军审计司后设干办官二员。",
          quota=2, staff_type="干办官")
    relation(w, i, monitor, dry, "前后演变", quote,
             "诸军审计司初设监官，后改置干办官。")
    finish(w, touched, "整理诸军专勾司改诸军审计司及监干办编制链。")


def main():
    for i in range(701, 721):
        globals()[f"entry{i}"]()
        print(f"#{i} {F[i]['title']} done")


if __name__ == "__main__":
    main()
