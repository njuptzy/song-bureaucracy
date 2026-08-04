#!/usr/bin/env python3
"""提取 chapter5t7 第1401-1420条：四方馆续条、引进司、客省与三卫府。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_5t7_1381_1400 as previous


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


F = {i: load(i) for i in range(1401, 1421)}
base = previous.base
base.F = F
base.ENTRY_DB = ENTRY_DB

W = base.W
field = base.field
relation = base.relation
staff = base.staff
cite = base.cite
alias_note = base.alias_note

node = previous.node
office_staff = previous.office_staff
group_instances = previous.group_instances


TIME_HINTS = {
    **previous.TIME_HINTS,
    "唐朝": 700,
    "唐代": 700.1,
    "唐永泰间": 765,
    "唐天祐元年四月": 904.3,
    "五代后梁": 910,
    "宋初": 960,
    "北宋": 970,
    "北宋前期": 1000,
    "北宋雍熙四年七月": 987.55,
    "北宋淳化二年": 991,
    "北宋大中祥符四年四月二十三日": 1011.31,
    "北宋嘉祐三年八月三日": 1058.6,
    "北宋元丰新制": 1080,
    "北宋崇宁四年二月十日": 1105.10,
    "北宋崇宁四年二月二十六日": 1105.15,
    "北宋崇宁五年正月三十日": 1106.08,
    "北宋政和二年九月二十五日": 1112.72,
    "北宋政和二年十一月六日": 1112.84,
    "北宋政和二年十一月十九日": 1112.87,
    "南宋建炎初": 1127.1,
    "南宋建炎元年十二月": 1127.95,
    "南宋建炎元年十二月二十一日": 1127.96,
    "南宋绍兴初": 1131,
    "宋代": 1100,
    "宋代（具体年月未载）": 1100.1,
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


def evolution(w, touched, i, source_title, target_title, time, quotation,
              decision, field_name=None, *, entity_type="官职",
              source_event=None, target_event=None):
    source = node(
        w, touched, i, source_title, entity_type, time,
        source_event or f"改称{target_title}", quotation, "演变前",
        f"建立或复用{source_title}演变节点。", field_name,
        update_event=True,
    )
    target = node(
        w, touched, i, target_title, entity_type, time,
        target_event or f"由{source_title}改称", quotation, "演变后",
        f"建立或复用{target_title}演变节点。", field_name,
        update_event=True,
    )
    rid = relation(
        w, i, source, target, "前后演变", quotation, decision, field_name
    )
    return source, target, rid


def mark_conflict(w, citation_id, note, decision):
    saved_flag, saved_note = w.conn.execute(
        "select conflict_flag,note from Citations where id=?", (citation_id,)
    ).fetchone()
    if saved_flag == 1 and saved_note == note:
        return
    w.conn.execute(
        "update Citations set conflict_flag=1,note=? where id=?",
        (note, citation_id),
    )
    w._br("Citations", citation_id, decision)


def conflict_targets(w, i, targets, quotation, note, decision, field_name=None):
    for table, target_id in targets:
        citation_id = cite(
            w, table, target_id, i, quotation, decision, field_name,
            conflict_flag=1, note=note,
        )
        mark_conflict(w, citation_id, note, decision)


def canonicalize_guest_bureau(w, quotation):
    old = w.find_entity("客省司", "机构")
    formal = w.find_entity("客省", "机构")
    if old is not None:
        assert formal is None or formal == old, (old, formal)
        w.conn.execute(
            "update Entities set title='客省',quotation=? where id=?",
            (quotation, old),
        )
        w._br(
            "Entities", old,
            "据正式辞典词头‘客省’规范横行五司条先建的‘客省司’，"
            "保留原时间点、关系和引文。",
        )
        formal = old
    assert formal is not None
    return formal


def refine_time(w, touched, title, type_, old_time, new_time, decision):
    eid = w.find_entity(title, type_)
    assert eid is not None, (title, type_)
    old = w.find_timepoint(eid, old_time)
    new = w.find_timepoint(eid, new_time)
    if old is not None and new is None:
        w.conn.execute("update Timepoints set time=? where id=?", (new_time, old))
        w._br("Timepoints", old, decision)
        new = old
    assert new is not None, (title, old_time, new_time)
    touched.add(eid)
    return new


def entry1401():
    i, main = 1401, F[1401]["text"]
    w, touched = W(i), set()
    source, target, reform = evolution(
        w, touched, i, "四方馆使", "拱辰大夫",
        "北宋政和二年九月二十五日", main,
        "本条明确记四方馆使易为拱辰大夫。",
        source_event="辞典两条分别记武阶易为拱卫大夫、拱辰大夫",
        target_event="承接四方馆使武阶",
    )
    office, post, staffing = office_staff(
        w, touched, i, "四方馆", F[i]["title"],
        "北宋政和二年十一月十九日", main,
        "本条记十一月十九日置知馆事二员。",
        quota="二员", staff_type="知馆事",
        office_event="置知四方馆事二员", post_event="始置二员，领本馆职事",
    )
    reform_note = "与第1400条所载四方馆使易为拱卫大夫冲突，保留原书两说。"
    conflict_targets(
        w, i,
        (("Timepoints", source), ("Timepoints", target), ("Relationships", reform)),
        main, reform_note, "标记拱辰大夫与拱卫大夫的原书冲突。",
    )
    date_note = "与第1398条所载政和二年十一月六日置知四方馆事二员冲突，保留两日。"
    conflict_targets(
        w, i,
        (("Timepoints", office), ("Timepoints", post), ("Relationships", staffing)),
        main, date_note, "标记知四方馆事十一月十九日与十一月六日的日期冲突。",
    )
    finish(w, touched, "整理知四方馆事政和设置及两组辞典内部冲突。")


def combined_gate_post(i, source_title):
    main = F[i]["text"]
    w, touched = W(i), set()
    canonicalize_guest_bureau(w, main)
    source = node(
        w, touched, i, "四方馆官", "官职", "南宋建炎初",
        "废罢四方馆官", main, "演变前",
        "建立四方馆官建炎初罢置节点。", update_event=True,
    )
    post = node(
        w, touched, i, F[i]["title"], "官职", "南宋建炎初",
        "四方馆官罢后由知阁官兼领客省、四方馆事", main, "兼领职事官",
        f"建立{F[i]['title']}正式职事官节点。", update_event=True,
    )
    relation(
        w, i, source, post, "前后演变", main,
        f"四方馆官罢后，馆事改由{source_title}兼领。",
    )
    for office_title in ("阁门", "客省", "四方馆"):
        office = node(
            w, touched, i, office_title, "机构", "南宋建炎初",
            f"由{F[i]['title']}兼领相关公事", main, "横行机构",
            f"建立{office_title}建炎初兼领节点。",
        )
        relation(
            w, i, office, post, "编制隶属", main,
            f"{F[i]['title']}兼领{office_title}相关公事。",
            staff_type="兼领官",
        )
    finish(w, touched, f"恢复{F[i]['title']}正式词头并整理建炎兼领关系。")


def entry1402():
    combined_gate_post(1402, "知阁门事")


def entry1403():
    combined_gate_post(1403, "同知阁门事")


def entry1404():
    assert not F[1404]["text"] and F[1404]["fields"].get("__status__") == "placeholder"


def entry1405():
    assert not F[1405]["text"] and F[1405]["fields"].get("__status__") == "placeholder"


def entry1406():
    i, main = 1406, F[1406]["text"]
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    roster, aliases = field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    office = node(
        w, touched, i, F[i]["title"], "机构", "北宋",
        "宋沿置，仍以司称", origin, "内诸司",
        "建立引进司北宋沿置节点。", "职源与沿革", update_event=True,
    )
    cite(w, "Timepoints", office, i, duty, "保存进奉贡品及礼物收受职掌。", "职掌")
    for superior in ("台察", "中书省"):
        parent = node(
            w, touched, i, superior, "机构", "宋代（具体年月未载）",
            "先后统辖引进司", main, "上级机构",
            f"建立{superior}无具体年月承载节点。",
        )
        child = node(
            w, touched, i, F[i]["title"], "机构", "宋代（具体年月未载）",
            "先后隶台察、中书省", main, "内诸司",
            "建立引进司无具体年月隶属节点。", update_event=True,
        )
        relation(w, i, parent, child, "上下级机构", main,
                 f"正文记引进司先后隶{superior}。")
    for post_title, quota, staff_type in (
        ("引进司使", "二人", "正使"),
        ("引进司副使", "二人", "副使"),
    ):
        office_staff(
            w, touched, i, F[i]["title"], post_title, "北宋元丰新制", roster,
            f"元丰新制{post_title}{quota}。", "编制",
            quota=quota, staff_type=staff_type,
            office_event=f"编制{post_title}{quota}", post_event="列入元丰引进司编制",
        )
    evolution(
        w, touched, i, "引进司使", "中卫大夫",
        "北宋政和二年九月二十五日", roster,
        "政和二年引进司使武阶易为中卫大夫。", "编制",
        source_event="武阶易为中卫大夫", target_event="承接引进司使武阶",
    )
    evolution(
        w, touched, i, "引进司副使", "中卫郎",
        "北宋政和二年九月二十五日", roster,
        "政和二年引进司副使武阶易为中卫郎。", "编制",
        source_event="武阶易为中卫郎", target_event="承接引进司副使武阶",
    )
    office_staff(
        w, touched, i, F[i]["title"], "知引进司公事",
        "北宋政和二年九月二十五日", roster,
        "政和二年设知引进司公事二员。", "编制",
        quota="二员", staff_type="知司公事",
        office_event="置知引进司公事二员", post_event="由内外官掌领引进司公事",
    )
    merger_time = "南宋建炎元年十二月"
    source_eid = w.find_entity(F[i]["title"], "机构")
    target_eid = w.find_entity("客省", "机构")
    if (
        source_eid is not None and target_eid is not None
        and w.find_timepoint(source_eid, "南宋建炎元年十二月二十一日") is not None
        and w.find_timepoint(target_eid, "南宋建炎元年十二月二十一日") is not None
    ):
        merger_time = "南宋建炎元年十二月二十一日"
    evolution(
        w, touched, i, F[i]["title"], "客省", merger_time,
        origin, "建炎元年十二月引进司并入客省。", "职源与沿革",
        entity_type="机构", source_event="并入客省", target_event="接收引进司",
    )
    alias_note(w, i, office, aliases, "简称")
    finish(w, touched, "整理引进司沿革、层级、职掌、元丰编制、政和改制与建炎并省。")


def horizontal_post(i, group_title, reform_title, source_time, source_event,
                    reform_event, staff_type):
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    rank, roster, aliases = field(i, "品位"), field(i, "编制"), field(i, "简称")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "引进司", F[i]["title"], source_time, origin,
        f"{F[i]['title']}在引进司供职。", "职源与沿革",
        staff_type=staff_type, office_event=f"设置{F[i]['title']}",
        post_event=source_event,
    )
    cite(w, "Timepoints", post, i, duty, "保存领本司公事及横行武阶职能。", "职掌")
    cite(w, "Timepoints", post, i, rank, "保存品位与迁转班序。", "品位")
    office, north, staffing = office_staff(
        w, touched, i, "引进司", F[i]["title"], "北宋", roster,
        f"北宋{F[i]['title']}编制二员。", "编制",
        quota="二员", staff_type=staff_type,
        office_event=f"编制{F[i]['title']}二员", post_event="北宋沿置，编制二员",
    )
    group = node(
        w, touched, i, group_title, "官职", "北宋",
        f"{group_title}统称", duty, "横行武阶统称",
        f"建立或复用{group_title}北宋统称节点。", "职掌",
    )
    member = node(
        w, touched, i, F[i]["title"], "官职", "北宋",
        f"{group_title}之一", duty, "横行武阶",
        f"建立{F[i]['title']}横行武阶节点。", "职掌",
    )
    relation(w, i, group, member, "统称与实例", duty,
             f"正文明确{F[i]['title']}为{group_title}之一。", "职掌")
    evolution(
        w, touched, i, F[i]["title"], reform_title,
        "北宋政和二年九月二十五日", origin,
        f"政和二年{F[i]['title']}易为{reform_title}。", "职源与沿革",
        source_event=reform_event, target_event=f"承接{F[i]['title']}武阶",
    )
    alias_note(w, i, north, aliases, "简称")
    assert office and staffing
    finish(w, touched, f"整理{F[i]['title']}源流、引进司隶属、职掌品位、员额与政和改阶。")


def entry1407():
    horizontal_post(
        1407, "横行五使", "中卫大夫", "五代后梁", "后梁始置，宋沿置",
        "武阶易为中卫大夫", "正使",
    )


def entry1408():
    horizontal_post(
        1408, "横行副使", "中卫郎", "五代后梁", "五代后梁已有，北宋沿置",
        "武阶易为中卫郎", "副使",
    )


def entry1409():
    i, main = 1409, F[1409]["text"]
    w, touched = W(i), set()
    evolution(
        w, touched, i, "引进司使", "中卫大夫",
        "北宋政和二年九月二十五日", main,
        "本条再次证明引进司使易为中卫大夫。",
        source_event="武阶易为中卫大夫", target_event="承接引进司使武阶",
    )
    evolution(
        w, touched, i, "引进司副使", "中卫郎",
        "北宋政和二年九月二十五日", main,
        "本条再次证明引进司副使易为中卫郎。",
        source_event="武阶易为中卫郎", target_event="承接引进司副使武阶",
    )
    office_staff(
        w, touched, i, "引进司", F[i]["title"],
        "北宋政和二年九月二十五日", main,
        "政和二年置知引进司公事二员，由内外官掌领。",
        quota="二员", staff_type="知司公事",
        office_event="置知引进司公事二员", post_event="由内外官掌领引进司公事",
    )
    finish(w, touched, "补充知引进司公事政和设置、员额及两项武阶改名证据。")


def entry1410():
    i, main = 1410, F[1410]["text"]
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    roster, aliases = field(i, "编制"), field(i, "别名")
    w, touched = W(i), set()
    canonicalize_guest_bureau(w, main)
    for time, event in (
        ("北宋", "在开封宫内阁门之西"),
        ("南宋", "在临安东华门北"),
    ):
        tid = node(
            w, touched, i, F[i]["title"], "机构", time, event, main,
            "内诸司", f"保存客省{time}位置。", update_event=True,
        )
        cite(w, "Timepoints", tid, i, duty, "保存宾客接伴、进奉与回诏职掌。", "职掌")
    parent, child = previous.office_child(
        w, touched, i, "鸿胪寺", F[i]["title"], "唐永泰间", origin,
        "唐永泰间客省置于右银台门，隶鸿胪寺。", "职源与沿革",
        parent_event="统辖右银台门客省", child_event="置于右银台门，隶鸿胪寺",
    )
    assert parent and child
    for superior in ("台察", "中书省"):
        superior_tid = node(
            w, touched, i, superior, "机构", "宋代（具体年月未载）",
            "先后统辖客省", main, "上级机构",
            f"建立{superior}无具体年月承载节点。",
        )
        guest_tid = node(
            w, touched, i, F[i]["title"], "机构", "宋代（具体年月未载）",
            "先后隶台察、中书省", main, "内诸司",
            "建立客省无具体年月隶属节点。", update_event=True,
        )
        relation(w, i, superior_tid, guest_tid, "上下级机构", main,
                 f"正文记客省先后隶{superior}。")
    source = refine_time(
        w, touched, "引进司", "机构", "南宋建炎元年十二月",
        "南宋建炎元年十二月二十一日",
        "据本条精确日期将引进司并省节点由十二月细化为十二月二十一日。",
    )
    target = refine_time(
        w, touched, F[i]["title"], "机构", "南宋建炎元年十二月",
        "南宋建炎元年十二月二十一日",
        "据本条精确日期将客省接收节点由十二月细化为十二月二十一日。",
    )
    relation(w, i, source, target, "前后演变", origin,
             "建炎元年十二月二十一日引进司并归客省。", "职源与沿革")
    evolution(
        w, touched, i, F[i]["title"], "东上阁门司", "南宋绍兴初",
        origin, "绍兴初客省官并入东上阁门司。", "职源与沿革",
        entity_type="机构", source_event="客省官并入东上阁门司",
        target_event="接收客省官",
    )
    for post_title, staff_type in (
        ("判客省", "判官"), ("管勾客省公事", "管勾官"),
    ):
        office_staff(
            w, touched, i, F[i]["title"], post_title, "宋初", roster,
            f"宋初客省设{post_title}。", "编制", staff_type=staff_type,
            office_event=f"设置{post_title}", post_event="宋初供职客省",
        )
    for time in ("北宋嘉祐三年八月三日", "北宋元丰新制"):
        for post_title, staff_type in (("客省使", "正使"), ("客省副使", "副使")):
            office_staff(
                w, touched, i, F[i]["title"], post_title, time, roster,
                f"{time}{post_title}定员二。", "编制",
                quota="二员", staff_type=staff_type,
                office_event=f"编制{post_title}二员", post_event="定员二",
            )
    office_staff(
        w, touched, i, F[i]["title"], "客省承受",
        "宋代（具体年月未载）", roster,
        "客省承受十人，旧名承旨。", "编制",
        quota="十人", staff_type="吏人",
        office_event="编制客省承受十人", post_event="承办客省具体事务",
    )
    old, new, old_to_new = evolution(
        w, touched, i, "客省承旨", "客省承受", "宋代（具体年月未载）",
        roster, "本条称客省承受旧名承旨。", "编制",
        source_event="客省承受的旧名", target_event="由客省承旨改名",
    )
    conflict_note = "与第1415条所载淳化二年改名客省承旨方向相反，保留原书两说。"
    conflict_targets(
        w, i,
        (("Timepoints", old), ("Timepoints", new), ("Relationships", old_to_new)),
        roster, conflict_note, "标记客省承旨、承受改名方向冲突。", "编制",
    )
    alias_note(w, i, target, aliases, "别名")
    finish(w, touched, "规范客省词头并整理源流、层级、职掌、位置、编制、并省与旧名冲突。")


def guest_envoy(i, reform_title, group_title, source_time, source_event,
                staff_type, initial_quota=None):
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    rank, roster = field(i, "品位"), field(i, "编制")
    aliases = field(i, "简称") if "简称" in F[i]["fields"] else None
    w, touched = W(i), set()
    _, source, _ = office_staff(
        w, touched, i, "客省", F[i]["title"], source_time, origin,
        f"{source_time}{F[i]['title']}已置。", "职源与沿革",
        staff_type=staff_type, office_event=f"设置{F[i]['title']}",
        post_event=source_event,
    )
    cite(w, "Timepoints", source, i, duty, "保存领客省公事与横行外任职能。", "职掌")
    cite(w, "Timepoints", source, i, rank, "保存品位、班序与迁转。", "品位")
    if initial_quota:
        office_staff(
            w, touched, i, "客省", F[i]["title"], "北宋前期", roster,
            f"北宋前期{F[i]['title']}初为一员。", "编制",
            quota=initial_quota, staff_type=staff_type,
            office_event=f"编制{F[i]['title']}{initial_quota}", post_event="初为一员",
        )
    office, north, staffing = office_staff(
        w, touched, i, "客省", F[i]["title"],
        "北宋嘉祐三年八月三日", roster,
        f"嘉祐三年八月三日{F[i]['title']}定员二。", "编制",
        quota="二员", staff_type=staff_type,
        office_event=f"编制{F[i]['title']}二员", post_event="定员二",
    )
    group = node(
        w, touched, i, group_title, "官职", "北宋",
        f"{group_title}统称", duty, "横行武阶统称",
        f"建立或复用{group_title}北宋节点。", "职掌",
    )
    member = node(
        w, touched, i, F[i]["title"], "官职", "北宋",
        f"{group_title}之一", duty, "横行武阶",
        f"建立{F[i]['title']}横行武阶节点。", "职掌",
    )
    relation(w, i, group, member, "统称与实例", duty,
             f"正文明确{F[i]['title']}为{group_title}之一。", "职掌")
    evolution(
        w, touched, i, F[i]["title"], reform_title,
        "北宋政和二年九月二十五日", origin,
        f"政和二年{F[i]['title']}易为{reform_title}。", "职源与沿革",
        source_event=f"武阶易为{reform_title}", target_event=f"承接{F[i]['title']}武阶",
    )
    if aliases:
        alias_note(w, i, north, aliases, "简称")
    assert office and staffing
    finish(w, touched, f"整理{F[i]['title']}源流、客省隶属、横行实例、品位员额与政和改阶。")


def entry1411():
    guest_envoy(
        1411, "中亮大夫", "横行五使", "唐天祐元年四月",
        "唐代已有，北宋沿置", "正使", initial_quota="一员",
    )


def entry1412():
    i, main = 1412, F[1412]["text"]
    w, touched = W(i), set()
    evolution(
        w, touched, i, "客省使", "中亮大夫",
        "北宋政和二年九月二十五日", main,
        "本条再次证明客省使易为中亮大夫。",
        source_event="武阶易为中亮大夫", target_event="承接客省使武阶",
    )
    evolution(
        w, touched, i, "客省副使", "中亮郎",
        "北宋政和二年九月二十五日", main,
        "本条再次证明客省副使易为中亮郎。",
        source_event="武阶易为中亮郎", target_event="承接客省副使武阶",
    )
    office_staff(
        w, touched, i, "客省", F[i]["title"],
        "北宋政和二年九月二十五日", main,
        "政和二年置知客省司事二员，由内外官掌领。",
        quota="二员", staff_type="知司事",
        office_event="置知客省事二员", post_event="由内外官掌领客省司公事",
    )
    finish(w, touched, "整理知客省事政和设置、员额及两项武阶改名证据。")


def entry1413():
    guest_envoy(
        1413, "中亮郎", "横行副使", "北宋前期",
        "北宋前期已置", "副使",
    )


def entry1414():
    i, main = 1414, F[1414]["text"]
    w, touched = W(i), set()
    office_staff(
        w, touched, i, "客省", F[i]["title"], "宋代（具体年月未载）",
        main, "客省承受承办远程接送、御筵和宾客仪范等具体事务。",
        staff_type="吏人", office_event="设置客省承受",
        post_event="承办客省具体事务",
    )
    finish(w, touched, "补充客省承受吏人身份、客省隶属及具体职掌。")


def entry1415():
    i, main = 1415, F[1415]["text"]
    w, touched = W(i), set()
    source, target, reverse = evolution(
        w, touched, i, "客省承受", F[i]["title"], "北宋淳化二年", main,
        "相邻正式词头与本条改名句表明客省承受改名客省承旨。",
        source_event="改名客省承旨", target_event="由客省承受改名",
    )
    office, post, staffing = office_staff(
        w, touched, i, "客省", F[i]["title"], "北宋淳化二年", main,
        "本条记客省承旨编制十人。", quota="十人", staff_type="吏人",
        office_event="编制客省承旨十人", post_event="改名后编制十人",
    )
    conflict_note = "与第1410条所载客省承受旧名承旨方向相反，保留原书两说。"
    conflict_targets(
        w, i,
        (("Timepoints", source), ("Timepoints", target), ("Relationships", reverse),
         ("Timepoints", office), ("Relationships", staffing)),
        main, conflict_note, "标记客省承受、承旨改名方向冲突。",
    )
    assert post
    finish(w, touched, "整理客省承旨淳化改名、十人编制及与客省条旧名说的冲突。")


def entry1416():
    i = 1416
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    rank = field(i, "品位")
    w, touched = W(i), set()
    post = node(
        w, touched, i, F[i]["title"], "官职", "唐朝",
        "唐朝始置", origin, "横行武阶前身",
        "辞典正式词头作内容省使，正文记唐朝始置。", "职源与沿革",
        update_event=True,
    )
    _, north, _ = office_staff(
        w, touched, i, "内客省使厅事", F[i]["title"], "北宋", duty,
        "北宋内容省使供职本使厅事。", "职掌", staff_type="使",
        office_event="内容省使治所", post_event="北宋沿置，横行武阶序位最高",
    )
    cite(w, "Timepoints", north, i, origin, "保存北宋沿置与政和改阶源流。", "职源与沿革")
    cite(w, "Timepoints", north, i, rank, "保存从五品、恩数与横班最高序位。", "品位")
    evolution(
        w, touched, i, F[i]["title"], "通侍大夫",
        "北宋政和二年九月二十五日", origin,
        "政和二年内容省使武阶易为通侍大夫。", "职源与沿革",
        source_event="武阶易为通侍大夫", target_event="承接内容省使武阶",
    )
    finish(w, touched, "按正式词头整理内容省使唐宋沿置、治所、职掌品位与政和改阶。")


def entry1417():
    i, main = 1417, F[1417]["text"]
    w, touched = W(i), set()
    evolution(
        w, touched, i, F[i]["title"], "三班院", "北宋雍熙四年七月", main,
        "雍熙四年以内客省使厅事置三班院。",
        entity_type="机构", source_event="改置三班院", target_event="由内客省使厅事改置",
    )
    evolution(
        w, touched, i, "三班院", F[i]["title"],
        "北宋大中祥符四年四月二十三日", main,
        "大中祥符四年分三班院，复设内客省使厅事。",
        entity_type="机构", source_event="分院后复设内客省使厅事",
        target_event="分三班院后复设",
    )
    finish(w, touched, "整理内客省使厅事与三班院的雍熙改置及祥符复设。")


def entry1418():
    i = 1418
    origin, duty, roster = field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制")
    w, touched = W(i), set()
    tang_group = node(
        w, touched, i, "三卫五府", "机构", "唐代",
        "亲卫一府、勋卫二府、翊卫二府的合称", origin, "三卫机构统称",
        "建立唐代三卫五府统称。", "职源与沿革", update_event=True,
    )
    for child_title in ("亲卫府", "勋卫府", "翊卫府"):
        child = node(
            w, touched, i, child_title, "机构", "唐代",
            "三卫五府所指府署", origin, "三卫府署",
            f"建立唐代{child_title}节点。", "职源与沿革",
        )
        relation(w, i, tang_group, child, "统称与实例", origin,
                 f"唐代三卫五府包括{child_title}。", "职源与沿革")
    office = node(
        w, touched, i, F[i]["title"], "机构", "北宋崇宁四年二月十日",
        "仿唐制始置，下辖亲卫、勋卫、翊卫府", origin, "宿卫机构",
        "建立三卫府崇宁四年始置节点。", "职源与沿革", update_event=True,
    )
    cite(w, "Timepoints", office, i, duty, "保存统领三卫郎宿卫殿廷职掌。", "职掌")
    cite(w, "Timepoints", office, i, roster, "保存三卫府及三府完整官吏编制。", "编制")
    for child_title in ("亲卫府", "勋卫府", "翊卫府"):
        child = node(
            w, touched, i, child_title, "机构", "北宋崇宁四年二月十日",
            "隶三卫府", origin, "下级府署",
            f"建立宋代{child_title}节点。", "职源与沿革",
        )
        relation(w, i, office, child, "上下级机构", origin,
                 f"崇宁四年三卫府下辖{child_title}。", "职源与沿革")
    for post_title, quota, staff_type in (
        ("三卫郎", "一员", "长官初名"),
        ("三卫中郎", "二员", "中郎"),
        ("三卫博士", "二员", "博士"),
        ("三卫主簿", "一员", "主簿"),
    ):
        post_event = (
            "始置，为三卫府长官"
            if post_title == "三卫郎" else "列入三卫府编制"
        )
        office_staff(
            w, touched, i, F[i]["title"], post_title,
            "北宋崇宁四年二月十日", roster,
            f"三卫府置{post_title}{quota}。", "编制",
            quota=quota, staff_type=staff_type,
            office_event=f"编制{post_title}{quota}", post_event=post_event,
        )
    for child_title, post_title, quota in (
        ("亲卫府", "亲卫郎", "十员"),
        ("亲卫府", "亲卫中郎", "十员"),
        ("勋卫府", "勋卫郎", "十员"),
        ("勋卫府", "勋卫中郎", "十员"),
        ("翊卫府", "翊卫郎", "二十员"),
        ("翊卫府", "翊卫中郎", "二十员"),
    ):
        office_staff(
            w, touched, i, child_title, post_title,
            "北宋崇宁四年二月十日", roster,
            f"{child_title}置{post_title}{quota}。", "编制",
            quota=quota, staff_type="三卫郎",
            office_event=f"编制{post_title}{quota}", post_event="列入三卫府宿卫编制",
        )
    for post_title, quota in (
        ("三卫府令史", "一员"),
        ("三卫府书令史", "二员"),
        ("三卫府贴书", "四员"),
        ("三卫府守阙贴书", "四员"),
    ):
        office_staff(
            w, touched, i, F[i]["title"], post_title,
            "北宋崇宁四年二月十日", roster,
            f"三卫府吏额置{post_title}{quota}。", "编制",
            quota=quota, staff_type="吏员",
            office_event=f"编制{post_title}{quota}", post_event="列入三卫府吏额",
        )
    evolution(
        w, touched, i, "三卫郎", "三卫侍郎",
        "北宋崇宁四年二月二十六日", roster,
        "三卫府长官初称三卫郎，二十六日改称三卫侍郎。", "编制",
        source_event="改为三卫侍郎", target_event="由三卫郎改名",
    )
    ended = node(
        w, touched, i, F[i]["title"], "机构", "北宋崇宁五年正月三十日",
        "罢置", origin, "宿卫机构",
        "建立三卫府崇宁五年罢置节点。", "职源与沿革", update_event=True,
    )
    cite(w, "Timepoints", ended, i, origin, "保存三卫府罢置日期。", "职源与沿革")
    finish(w, touched, "整理三卫府唐制来源、宋代始罢、三级机构、完整官吏编制及长官改名。")


def entry1419():
    i = 1419
    origin, duty = field(i, "职源与沿革"), field(i, "职掌")
    rank, roster = field(i, "品位"), field(i, "编制")
    w, touched = W(i), set()
    _, post, _ = office_staff(
        w, touched, i, "三卫府", F[i]["title"],
        "北宋崇宁四年二月十日", origin,
        "崇宁四年二月十日始置三卫郎一员，为三卫府长官。", "职源与沿革",
        quota="一员", staff_type="长官初名",
        office_event="编制三卫郎一员", post_event="始置，为三卫府长官",
    )
    cite(w, "Timepoints", post, i, duty, "保存总治三卫府事职掌。", "职掌")
    cite(w, "Timepoints", post, i, rank, "保存从四品、朝班与三卫官长品位。", "品位")
    cite(w, "Timepoints", post, i, roster, "保存一员编制。", "编制")
    evolution(
        w, touched, i, F[i]["title"], "三卫侍郎",
        "北宋崇宁四年二月二十六日", origin,
        "崇宁四年二月二十六日三卫郎改为三卫侍郎。", "职源与沿革",
        source_event="改为三卫侍郎", target_event="由三卫郎改名",
    )
    finish(w, touched, "整理三卫郎始置、三卫府长官隶属、职掌品位员额及改名。")


def entry1420():
    i, main = 1420, F[1420]["text"]
    w, touched = W(i), set()
    evolution(
        w, touched, i, "三卫郎", F[i]["title"],
        "北宋崇宁四年二月二十六日", main,
        "崇宁四年二月二十六日三卫郎改名三卫侍郎。",
        source_event="改为三卫侍郎", target_event="由三卫郎改名",
    )
    office_staff(
        w, touched, i, "三卫府", F[i]["title"],
        "北宋崇宁四年二月二十六日", main,
        "改名后三卫侍郎仍为三卫府长官。",
        quota="一员", staff_type="长官",
        office_event="长官改称三卫侍郎", post_event="由三卫郎改名，仍为府长",
    )
    ended = node(
        w, touched, i, F[i]["title"], "官职", "北宋崇宁五年正月三十日",
        "随三卫府罢置", main, "宿卫长官",
        "建立三卫侍郎罢置节点。", update_event=True,
    )
    cite(w, "Timepoints", ended, i, main, "保存三卫侍郎罢置日期。")
    finish(w, touched, "整理三卫侍郎改名、三卫府长官隶属及罢置。")


def main():
    for i in range(1401, 1421):
        globals()[f"entry{i}"]()
        suffix = " placeholder" if not F[i]["text"] else " done"
        print(f"#{i} {F[i]['title']}{suffix}")


if __name__ == "__main__":
    main()
