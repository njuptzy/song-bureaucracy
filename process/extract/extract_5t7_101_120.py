#!/usr/bin/env python3
"""提取 chapter5t7 第101-120条：大晟府乐官、乐工与吏属。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter
import extract_5t7_081_100 as previous


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


F = {i: load(i) for i in range(101, 121)}


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def Q(i, needle, field_name=None):
    source = F[i]["fields"][field_name] if field_name else F[i]["text"]
    assert needle in source, (i, field_name, needle)
    return needle


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def C(i, field_name=None):
    base = f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
    return base + (f"（{field_name}字段）" if field_name else "")


def cite(w, table, target_id, i, quotation, decision, field_name=None, **kwargs):
    return w.citation(
        table, target_id, C(i, field_name), quotation, decision, **kwargs
    )


def state(w, i, title, type_, time, event, quotation, category, decision,
          field_name=None, *, officer=None, grade=None, note=None):
    eid = w.entity(title, type_, decision, quotation=quotation)
    tid = w.timepoint(
        eid, time, event, decision, quotation,
        attr_category=category, attr_officer_type=officer, attr_grade=grade,
        chain="none",
    )
    cite(w, "Timepoints", tid, i, quotation, decision, field_name, note=note)
    return eid, tid


def refine(w, i, eid, time, event, quotation, category, decision,
           field_name=None, *, officer=None, grade=None, note=None):
    tid = w.find_timepoint(eid, time)
    if tid is None:
        title, type_ = w.conn.execute(
            "select title,type from Entities where id=?", (eid,)
        ).fetchone()
        return state(
            w, i, title, type_, time, event, quotation, category, decision,
            field_name, officer=officer, grade=grade, note=note,
        )[1]
    row = w.conn.execute(
        "select event,attr_category,attr_officer_type,attr_grade,quotation "
        "from Timepoints where id=?", (tid,)
    ).fetchone()
    new = (event, category, officer, grade, quotation)
    if tuple(row) != new:
        w.conn.execute(
            "update Timepoints set event=?,attr_category=?,attr_officer_type=?,"
            "attr_grade=?,quotation=? where id=?", (*new, tid)
        )
        w._br(
            "Timepoints", tid,
            f"据专条细化既有 {time} 节点：event {row[0]}->{event}、"
            f"category {row[1]}->{category}：{decision}",
        )
    cite(w, "Timepoints", tid, i, quotation, decision, field_name, note=note)
    return tid


def relationship(w, i, subject_id, object_id, relation_type, quotation,
                 decision, field_name=None, **kwargs):
    rid = w.relationship(
        subject_id, object_id, relation_type, decision, quotation, **kwargs
    )
    cite(w, "Relationships", rid, i, quotation, decision, field_name)
    return rid


def staff(w, i, parent_tp, post_tp, quotation, decision, field_name=None,
          *, quota=None, staff_type="官", force_type=False):
    rid = relationship(
        w, i, parent_tp, post_tp, "编制隶属", quotation, decision,
        field_name, staff_quota=quota, staff_type=staff_type,
    )
    row = w.conn.execute(
        "select staff_quota,staff_type from Relationships where id=?", (rid,)
    ).fetchone()
    updates, params = [], []
    if quota is not None and row[0] is None:
        updates.append("staff_quota=?")
        params.append(quota)
    if staff_type and (not row[1] or (force_type and row[1] != staff_type)):
        updates.append("staff_type=?")
        params.append(staff_type)
    if updates:
        params.append(rid)
        w.conn.execute(
            f"update Relationships set {', '.join(updates)} where id=?", params
        )
        w._br("Relationships", rid, f"补充编制属性：{decision}")
    return rid


def entity_id(w, title, type_="官职"):
    eid = w.find_entity(title, type_)
    assert eid, (title, type_)
    return eid


def timepoint_id(w, title, type_, time):
    eid = entity_id(w, title, type_)
    tid = w.find_timepoint(eid, time)
    assert tid, (title, time)
    return tid


TIME_HINTS = {
    "周代": -1046,
    "北宋崇宁四年八月二十六日": 1105.8,
    "北宋宣和二年七月": 1120.5,
    "北宋宣和二年七月十六日": 1120.55,
    "北宋宣和二年八月十五日": 1120.7,
    "北宋宣和二年八月": 1120.7,
    "北宋宣和七年十二月二十二日": 1125.9,
}


def time_key(time, row_id):
    if time in TIME_HINTS:
        return (TIME_HINTS[time], 0, row_id)
    m = re.search(r"(\d{3,4})", time or "")
    if m:
        return (int(m.group(1)), 0, row_id)
    return previous.time_key(time, row_id)


def rechain(w, eid, decision):
    rows = w.conn.execute(
        "select id,time from Timepoints where entity_id=?", (eid,)
    ).fetchall()
    ordered = [r[0] for r in sorted(rows, key=lambda r: time_key(r[1], r[0]))]
    for n, tid in enumerate(ordered):
        w.relink(
            tid, decision,
            prev_id=ordered[n - 1] if n else None,
            succ_id=ordered[n + 1] if n + 1 < len(ordered) else None,
        )


def alias_note(w, i, tid, field_name):
    cite(
        w, "Timepoints", tid, i, field(i, field_name),
        f"{F[i]['title']}简称、别名只作名称证据，不另建实体。",
        field_name, note="纯简称、别名不另建实体",
    )


def dacheng_parent(w, i, time, event, quotation, field_name=None):
    eid = entity_id(w, "大晟府", "机构")
    tid = w.find_timepoint(eid, time)
    if tid is None:
        tid = state(
            w, i, "大晟府", "机构", time, event, quotation, "中央音乐机构",
            f"为第{i}条编制建立大晟府同期节点。", field_name,
        )[1]
    else:
        cite(
            w, "Timepoints", tid, i, quotation,
            f"第{i}条为大晟府既有{time}节点补充同期编制证据。", field_name,
        )
    return eid, tid


def entry101():
    i = 101
    main, history, duty, rank = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"),
    )
    w = W(i)
    eid = entity_id(w, "大晟府按协声律")
    start = refine(
        w, i, eid, "北宋崇宁四年八月二十六日",
        "随大晟府创建始设，按谱协调声律", history,
        "大晟府乐官", "据专条细化按协声律始置与职掌。", "职源与沿革",
        officer="乐官", grade="选人或白身（满一年迁从九品迪功郎）",
    )
    end = refine(
        w, i, eid, "北宋宣和二年七月十六日", "罢置", history,
        "大晟府乐官", "建立按协声律宣和二年罢置节点。", "职源与沿革",
        officer="乐官", grade="选人或白身（满一年迁从九品迪功郎）",
    )
    cite(w, "Timepoints", start, i, duty, "记录按协声律职掌。", "职掌")
    cite(w, "Timepoints", start, i, rank, "记录选任资格与满年迁转。", "品位")
    cite(w, "Timepoints", start, i, main, "正文明确按协声律隶大晟府。")
    staff(w, i, timepoint_id(w, "大晟府", "机构", "北宋崇宁四年八月二十六日"),
          start, main, "按协声律隶大晟府。", staff_type="乐官")
    rechain(w, eid, "整理按协声律始置与罢置链。")
    assert end
    w.commit()


def entry102():
    i = 102
    main, history, duty, rank, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "简称与别名"),
    )
    w = W(i)
    eid = entity_id(w, "大晟府制撰文字")
    start = refine(
        w, i, eid, "北宋崇宁四年八月二十六日",
        "随大晟府创建始设，创作乐曲", history,
        "大晟府乐官", "据专条细化大晟府制撰文字始置节点。", "职源与沿革",
        officer="乐官", grade="选人或白身（满一年迁从九品迪功郎）",
    )
    end = refine(
        w, i, eid, "北宋宣和二年七月十六日", "罢置", history,
        "大晟府乐官", "建立大晟府制撰文字罢置节点。", "职源与沿革",
        officer="乐官", grade="选人或白身（满一年迁从九品迪功郎）",
    )
    cite(w, "Timepoints", start, i, duty, "记录制撰文字创作乐曲。", "职掌")
    cite(w, "Timepoints", start, i, rank, "记录选任资格与满年迁转。", "品位")
    cite(w, "Timepoints", start, i, main, "正文明确制撰文字隶大晟府。")
    alias_note(w, i, start, "简称与别名")
    staff(w, i, timepoint_id(w, "大晟府", "机构", "北宋崇宁四年八月二十六日"),
          start, main, "专条明确大晟府制撰文字为乐官，纠正概括编制分类。",
          staff_type="乐官", force_type=True)
    rechain(w, eid, "整理大晟府制撰文字始置与罢置链。")
    assert end and aliases
    w.commit()


def entry103():
    i = 103
    main = F[i]["text"]
    w = W(i)
    eid = entity_id(w, "大晟府掌事")
    start = refine(
        w, i, eid, "北宋崇宁四年八月二十六日", "执麾押乐", main,
        "大晟府乐官", "据掌事专条细化职掌。", officer="乐官",
    )
    staff(w, i, timepoint_id(w, "大晟府", "机构", "北宋崇宁四年八月二十六日"),
          start, main, "专条明确掌事为乐官，纠正概括编制分类。",
          staff_type="乐官", force_type=True)
    rechain(w, eid, "确认大晟府掌事始置节点。")
    w.commit()


def entry104():
    i = 104
    main, history, duty, rank, roster = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品秩"), field(i, "编制"),
    )
    w = W(i)
    eid = entity_id(w, "大晟府运谱")
    start = refine(
        w, i, eid, "北宋崇宁四年八月二十六日",
        "随大晟府置，击鼓指挥乐工定谱、换谱", history,
        "大晟府乐官", "据运谱专条细化始置与职掌。", "职源与沿革",
        officer="乐官", grade="与色长同序，着绿公服",
    )
    quota = refine(
        w, i, eid, "北宋宣和二年八月十五日",
        "定员；运谱与色长合计四十四人", roster,
        "大晟府乐官", "记录运谱与色长合计员额，不拆分伪造单项人数。", "编制",
        officer="乐官", grade="与色长同序，着绿公服",
        note="四十四人为运谱与色长合计，并非运谱单项员额",
    )
    end = refine(
        w, i, eid, "北宋宣和七年十二月二十二日", "随大晟府罢置", history,
        "大晟府乐官", "建立运谱随府罢置节点。", "职源与沿革",
        officer="乐官", grade="与色长同序，着绿公服",
    )
    cite(w, "Timepoints", start, i, duty, "记录运谱击鼓定谱、换谱职掌。", "职掌")
    cite(w, "Timepoints", start, i, rank, "记录运谱班序与公服。", "品秩")
    cite(w, "Timepoints", start, i, main, "正文明确运谱隶大晟府。")
    parent_eid, parent_quota = dacheng_parent(
        w, i, "北宋宣和二年八月十五日", "运谱与色长合计定员四十四人",
        roster, "编制",
    )
    color_eid = entity_id(w, "大晟府色长")
    color_quota = refine(
        w, i, color_eid, "北宋宣和二年八月十五日",
        "与运谱合计定员四十四人", roster, "大晟府乐工",
        "记录大晟府色长与运谱合计员额。", "编制", officer="乐工",
        note="四十四人为运谱与色长合计，并非色长单项员额",
    )
    staff(w, i, parent_quota, quota, roster, "大晟府运谱在宣和二年定员。",
          "编制", staff_type="乐官")
    staff(w, i, parent_quota, color_quota, roster, "大晟府色长与运谱合计定员。",
          "编制", staff_type="乐工")
    staff(w, i, timepoint_id(w, "大晟府", "机构", "北宋崇宁四年八月二十六日"),
          start, main, "专条明确运谱为乐官，纠正概括编制分类。",
          staff_type="乐官", force_type=True)
    for touched in (eid, color_eid, parent_eid):
        rechain(w, touched, "补入运谱与色长宣和二年合计员额节点。")
    assert end
    w.commit()


def entry105():
    i = 105
    main = F[i]["text"]
    w = W(i)
    eid, generic = state(
        w, i, "大晟府乐工", "官职", "北宋",
        "大晟府乐师、色长、上工、中工、下工、舞师等总名", main,
        "大晟府乐工统称", "建立大晟府乐工总称节点。", officer="乐工统称",
        note="原文首项“乐工”与本统称同名，不制造自身指向自身的实例关系",
    )
    members = (
        "大晟府乐师", "大晟府色长", "大晟府上工",
        "大晟府中工", "大晟府下工", "大晟府舞师",
    )
    for title in members:
        relationship(
            w, i, generic,
            timepoint_id(w, title, "官职", "北宋崇宁四年八月二十六日"),
            "统称与实例", main, f"大晟府乐工是{title}等的总名。",
        )
    rechain(w, eid, "确认大晟府乐工北宋统称节点。")
    w.commit()


def entry106():
    i = 106
    main = F[i]["text"]
    w = W(i)
    eid = entity_id(w, "大晟府舞师")
    start = refine(
        w, i, eid, "北宋崇宁四年八月二十六日",
        "文、武二舞舞人；文舞执籥翟，武舞执干戚", main,
        "大晟府乐工", "据舞师专条细化文武二舞职掌。", officer="乐工",
    )
    quota = refine(
        w, i, eid, "北宋宣和二年八月",
        "定员一百五十人；参赴登歌每日特支食钱二百文", main,
        "大晟府乐工", "建立舞师宣和二年员额节点。", officer="乐工",
    )
    parent_eid, parent = dacheng_parent(
        w, i, "北宋宣和二年八月", "舞师定员一百五十人", main,
    )
    staff(w, i, parent, quota, main, "宣和二年大晟府舞师一百五十人。",
          quota=150, staff_type="乐工")
    for title, event in (
        ("大晟府文舞舞师", "文舞舞人，执籥翟"),
        ("大晟府武舞舞师", "武舞舞人，执干戚"),
    ):
        child_eid, child = state(
            w, i, title, "官职", "北宋", event, main, "大晟府舞师实例",
            f"建立{title}这一明确实例。", officer="乐工",
        )
        relationship(w, i, start, child, "统称与实例", main,
                     f"大晟府舞师包括{title}。")
        rechain(w, child_eid, f"确认{title}北宋节点。")
    rechain(w, eid, "整理大晟府舞师始置与宣和员额节点。")
    rechain(w, parent_eid, "补入舞师宣和二年定员节点。")
    w.commit()


def entry107():
    i = 107
    main, aliases = F[i]["text"], field(i, "简称")
    w = W(i)
    eid, generic = state(
        w, i, "大晟府二舞色长", "官职", "北宋",
        "文舞、武舞舞师领队，文武舞色长各司其职", main,
        "大晟府乐工", "建立大晟府二舞色长节点。", officer="乐工",
    )
    staff(w, i, timepoint_id(w, "大晟府", "机构", "北宋崇宁四年八月二十六日"),
          generic, main, "二舞色长隶大晟府。", staff_type="乐工")
    relationship(
        w, i, timepoint_id(w, "大晟府色长", "官职", "北宋崇宁四年八月二十六日"),
        generic, "统称与实例", aliases, "大晟府色长的实例包括二舞色长。", "简称",
    )
    relationship(
        w, i, timepoint_id(w, "色长", "官职", "宋代"),
        timepoint_id(w, "大晟府色长", "官职", "北宋崇宁四年八月二十六日"),
        "统称与实例", aliases, "色长为诸乐司色长通称，大晟府色长是实例。", "简称",
    )
    for title, event in (
        ("大晟府文舞色长", "文舞舞师领队"),
        ("大晟府武舞色长", "武舞舞师领队"),
    ):
        child_eid, child = state(
            w, i, title, "官职", "北宋", event, main, "大晟府二舞色长实例",
            f"建立{title}。", officer="乐工",
        )
        relationship(w, i, generic, child, "统称与实例", main,
                     f"大晟府二舞色长包括{title}。")
        rechain(w, child_eid, f"确认{title}北宋节点。")
    alias_note(w, i, generic, "简称")
    rechain(w, eid, "确认大晟府二舞色长北宋节点。")
    w.commit()


def explicit_pair(i, generic_title, event, children):
    main = F[i]["text"]
    w = W(i)
    eid = entity_id(w, generic_title)
    generic = refine(
        w, i, eid, "北宋崇宁四年八月二十六日", event, main,
        "大晟府乐工", f"据{F[i]['title']}专条细化职掌、次序。", officer="乐工",
    )
    for title, child_event in children:
        child_eid, child = state(
            w, i, title, "官职", "北宋", child_event, main,
            f"{F[i]['title']}实例", f"建立{title}这一明确实例。", officer="乐工",
        )
        relationship(w, i, generic, child, "统称与实例", main,
                     f"{generic_title}包括{title}。")
        rechain(w, child_eid, f"确认{title}北宋节点。")
    rechain(w, eid, f"细化{generic_title}大晟府节点。")
    w.commit()


def entry108_110():
    explicit_pair(
        108, "大晟府引舞", "执旌旗在舞队之前",
        (("大晟府文引舞", "文舞引舞"), ("大晟府武引舞", "武舞引舞")),
    )
    explicit_pair(
        109, "大晟府舞头", "位于舞色长之后、舞郎之前",
        (("大晟府文舞舞头", "文舞舞头"), ("大晟府武舞舞头", "武舞舞头")),
    )
    explicit_pair(
        110, "大晟府舞郎", "登歌献舞时位于舞头之后、舞人之前",
        (("大晟府文舞舞郎", "文舞舞郎"), ("大晟府武舞舞郎", "武舞舞郎")),
    )


def entry111():
    i = 111
    main, aliases = F[i]["text"], field(i, "简称")
    w = W(i)
    eid = entity_id(w, "大晟府乐正")
    start = refine(
        w, i, eid, "北宋崇宁四年八月二十六日",
        "指挥登歌乐人；乐工中位最高，着紫公服", main,
        "大晟府高级乐工", "据乐正专条细化职掌与序位。", officer="乐工",
    )
    quota = refine(
        w, i, eid, "北宋宣和二年七月", "定员二人", main,
        "大晟府高级乐工", "建立乐正宣和二年定员节点。", officer="乐工",
    )
    end = refine(
        w, i, eid, "北宋宣和七年十二月二十二日", "随大晟府罢置", main,
        "大晟府高级乐工", "建立乐正随府罢置节点。", officer="乐工",
    )
    parent_eid, parent = dacheng_parent(
        w, i, "北宋宣和二年七月", "核定大晟府各等乐工员额", main,
    )
    staff(w, i, parent, quota, main, "宣和二年大晟府乐正二人。",
          quota=2, staff_type="乐工")
    staff(w, i, timepoint_id(w, "大晟府", "机构", "北宋崇宁四年八月二十六日"),
          start, main, "大晟府乐正隶大晟府。", staff_type="乐工")
    alias_note(w, i, start, "简称")
    rechain(w, eid, "整理大晟府乐正始置、定员及罢置链。")
    rechain(w, parent_eid, "补入乐正宣和二年定员节点。")
    assert end and aliases
    w.commit()


def entry112():
    i = 112
    main = F[i]["text"]
    w = W(i)
    eid, start = state(
        w, i, "大晟府副乐正", "官职", "北宋崇宁四年八月二十六日",
        "随大晟府置；次于乐正，登歌着紫公服", main,
        "大晟府高级乐工", "建立大晟府副乐正始置节点。", officer="乐工",
    )
    _, quota = state(
        w, i, "大晟府副乐正", "官职", "北宋宣和二年七月",
        "与乐师合计定员六人", main, "大晟府高级乐工",
        "记录副乐正与乐师合计员额，不拆分伪造。", officer="乐工",
        note="六人为副乐正与乐师合计，并非副乐正单项员额",
    )
    _, end = state(
        w, i, "大晟府副乐正", "官职", "北宋宣和七年十二月二十二日",
        "随大晟府罢置", main, "大晟府高级乐工",
        "建立副乐正随府罢置节点。", officer="乐工",
    )
    parent_eid, parent = dacheng_parent(
        w, i, "北宋宣和二年七月", "核定大晟府各等乐工员额", main,
    )
    staff(w, i, parent, quota, main, "副乐正与乐师合计定员六人。", staff_type="乐工")
    staff(w, i, timepoint_id(w, "大晟府", "机构", "北宋崇宁四年八月二十六日"),
          start, main, "副乐正隶大晟府。", staff_type="乐工")
    rechain(w, eid, "整理大晟府副乐正始置、定员及罢置链。")
    rechain(w, parent_eid, "补充副乐正与乐师合计定员事实。")
    assert end
    w.commit()


def entry113():
    i = 113
    main = F[i]["text"]
    w = W(i)
    old_eid, old = state(
        w, i, "乐师", "官职", "周代", "《周礼》已有乐师属官", main,
        "前代乐官", "提取《周礼》乐师职源，不与大晟府乐师混同。", officer="前代乐官",
    )
    eid = entity_id(w, "大晟府乐师")
    start = refine(
        w, i, eid, "北宋崇宁四年八月二十六日",
        "次于乐正、副乐正，高于上中下乐工；乐工资深者递迁", main,
        "大晟府高级乐工", "据乐师专条细化序位与迁转。", officer="乐工",
    )
    quota = refine(
        w, i, eid, "北宋宣和二年七月", "定员四人", main,
        "大晟府高级乐工", "建立乐师宣和二年定员节点。", officer="乐工",
    )
    parent_eid, parent = dacheng_parent(
        w, i, "北宋宣和二年七月", "核定大晟府各等乐工员额", main,
    )
    staff(w, i, parent, quota, main, "宣和二年大晟府乐师四人。",
          quota=4, staff_type="乐工")
    staff(w, i, timepoint_id(w, "大晟府", "机构", "北宋崇宁四年八月二十六日"),
          start, main, "大晟府乐师隶大晟府。", staff_type="乐工")
    for touched in (old_eid, eid, parent_eid):
        rechain(w, touched, "补入乐师职源、序位及宣和定员节点。")
    assert old
    w.commit()


def entry114_116():
    i = 114
    main = F[i]["text"]
    w = W(i)
    parent_eid, parent = dacheng_parent(
        w, i, "北宋宣和二年七月", "核定大晟府各等乐工员额", main,
    )
    touched = {parent_eid}
    specs = (
        ("大晟府上工", "执各色乐器演奏；位次于乐师、高于中乐工"),
        ("大晟府中工", "位次于上乐工、高于下乐工"),
        ("大晟府下工", "乐工最低等，依次递迁为中、上乐工"),
    )
    for title, event in specs:
        eid = entity_id(w, title)
        if title == "大晟府上工":
            start = refine(
                w, i, eid, "北宋崇宁四年八月二十六日", event, main,
                "大晟府乐工", "据上乐工专条细化大晟府上工职掌与序位。",
                officer="乐工",
            )
        else:
            start = timepoint_id(w, title, "官职", "北宋崇宁四年八月二十六日")
        quota = refine(
            w, i, eid, "北宋宣和二年七月",
            "上、中、下乐工合计定员六百三十五人", main,
            "大晟府乐工", f"记录{title}参与三等乐工合计员额。", officer="乐工",
            note="六百三十五人为上、中、下乐工合计，并非单项员额",
        )
        staff(w, i, parent, quota, main, f"{title}参与三等乐工合计定员。",
              staff_type="乐工")
        staff(w, i, timepoint_id(w, "大晟府", "机构", "北宋崇宁四年八月二十六日"),
              start, main, f"{title}隶大晟府。", staff_type="乐工")
        touched.add(eid)
    for touched_eid in touched:
        rechain(w, touched_eid, "补入上中下乐工序位与宣和合计员额节点。")
    w.commit()

    for i, title, event in (
        (115, "大晟府中工", "位次于上乐工、高于下乐工"),
        (116, "大晟府下工", "乐工最低等，依次递迁为中、上乐工"),
    ):
        main = F[i]["text"]
        w = W(i)
        eid = entity_id(w, title)
        start = refine(
            w, i, eid, "北宋崇宁四年八月二十六日", event, main,
            "大晟府乐工", f"据{F[i]['title']}专条确认序位。", officer="乐工",
            note="原文显式详参第114条；合计员额事实由第114条保存",
        )
        rechain(w, eid, f"确认{title}始置节点。")
        w.commit()


def entry117():
    i = 117
    main = F[i]["text"]
    w = W(i)
    eid, generic = state(
        w, i, "执色乐工", "官职", "宋代",
        "具体承演某种乐器的乐工总称，有别于乐正、乐师", main,
        "乐工统称", "建立执色乐工统称节点。", officer="乐工统称",
    )
    for title, event in (
        ("筝色乐工", "承演筝"), ("琵琶色乐工", "承演琵琶"),
        ("笙色乐工", "承演笙"),
    ):
        child_eid, child = state(
            w, i, title, "官职", "宋代", event, main, "执色乐工实例",
            f"建立{title}这一原文明确举例。", officer="乐工",
        )
        relationship(w, i, generic, child, "统称与实例", main,
                     f"执色乐工包括{title}等具体乐器乐工。")
        rechain(w, child_eid, f"确认{title}宋代节点。")
    rechain(w, eid, "确认执色乐工宋代统称节点。")
    w.commit()


def entry118():
    i = 118
    main = F[i]["text"]
    w = W(i)
    eid, all_clerks = state(
        w, i, "大晟府吏", "官职", "北宋", "大晟府吏属统称", main,
        "大晟府吏属统称", "建立大晟府吏总称节点。", officer="吏属统称",
    )
    groups = (
        ("大晟府文书吏", "掌文书", ("大晟府胥长", "大晟府胥史", "大晟府胥佐", "大晟府贴书")),
        ("大晟府公物吏", "掌本府公物", ("大晟府专知", "大晟府副知", "大晟府库子")),
    )
    for group_title, event, members in groups:
        group_eid, group = state(
            w, i, group_title, "官职", "北宋", event, main,
            "大晟府吏属分类", f"建立{group_title}分类。", officer="吏属统称",
        )
        relationship(w, i, all_clerks, group, "统称与实例", main,
                     f"大晟府吏包括{group_title}。")
        for title in members:
            relationship(
                w, i, group,
                timepoint_id(w, title, "官职", "北宋崇宁四年八月二十六日"),
                "统称与实例", main, f"{group_title}包括{title}。",
            )
        rechain(w, group_eid, f"确认{group_title}北宋节点。")
    rechain(w, eid, "确认大晟府吏北宋统称节点。")
    w.commit()


def entry119_120():
    specs = (
        (119, "大晟府胥长", "大晟府文书吏四等中年劳最久者，位在胥史之上"),
        (120, "大晟府胥史", "大晟府文书吏，次于胥长"),
    )
    for i, title, event in specs:
        main = F[i]["text"]
        w = W(i)
        eid = entity_id(w, title)
        start = refine(
            w, i, eid, "北宋崇宁四年八月二十六日", event, main,
            "大晟府文书吏", f"据{F[i]['title']}专条细化序位。", officer="书吏",
        )
        staff(w, i, timepoint_id(w, "大晟府", "机构", "北宋崇宁四年八月二十六日"),
              start, main, f"{title}属于大晟府文书吏。", staff_type="书吏")
        rechain(w, eid, f"确认{title}始置节点。")
        w.commit()


def main():
    assert [F[i]["title"] for i in range(101, 121)] == [
        "按协声律", "制撰文字", "掌事", "运谱", "大晟府乐工", "舞师",
        "二舞色长", "引舞", "舞头", "舞郎", "乐正", "副乐正", "乐师",
        "上乐工", "中乐工", "下乐工", "执色乐工", "大晟府吏", "胥长", "胥史",
    ]
    entry101()
    entry102()
    entry103()
    entry104()
    entry105()
    entry106()
    entry107()
    entry108_110()
    entry111()
    entry112()
    entry113()
    entry114_116()
    entry117()
    entry118()
    entry119_120()


if __name__ == "__main__":
    main()
