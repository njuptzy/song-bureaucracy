#!/usr/bin/env python3
"""提取 chapter5t7 第201-220条：大宗正司丞属、六案、吏额及南宋两司。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter
import extract_5t7_181_200 as previous


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


F = {i: load(i) for i in range(196, 221)}


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


def entity_id(w, title, type_=None):
    eid = w.find_entity(title, type_)
    assert eid, (title, type_)
    return eid


def upsert_state(w, i, title, type_, time, event, quotation, category, decision,
                 field_name=None, *, officer=None, grade=None, note=None):
    eid = w.entity(title, type_, decision, quotation=quotation)
    tid = w.find_timepoint(eid, time)
    if tid is None:
        tid = w.timepoint(
            eid, time, event, decision, quotation,
            attr_category=category, attr_officer_type=officer,
            attr_grade=grade, chain="none",
        )
    else:
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
                f"据第{i}条校订 {title} 的 {time} 节点：{decision}",
            )
    cite(w, "Timepoints", tid, i, quotation, decision, field_name, note=note)
    return eid, tid


def relationship(w, i, subject_id, object_id, relation_type, quotation,
                 decision, field_name=None, **kwargs):
    rid = w.relationship(
        subject_id, object_id, relation_type, decision, quotation, **kwargs
    )
    cite(w, "Relationships", rid, i, quotation, decision, field_name)
    return rid


def staff(w, i, parent_tp, post_tp, quotation, decision, field_name=None,
          *, quota=None, staff_type="官"):
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
    if staff_type and not row[1]:
        updates.append("staff_type=?")
        params.append(staff_type)
    if updates:
        params.append(rid)
        w.conn.execute(
            f"update Relationships set {', '.join(updates)} where id=?", params
        )
        w._br("Relationships", rid, f"补充编制属性：{decision}")
    return rid


TIME_HINTS = {
    "晋朝": 265, "宋代": 960,
    "北宋景祐三年七月十九日": 1036.55,
    "北宋熙宁三年二月十二日": 1070.12,
    "南宋": 1127,
    "南宋建炎、绍兴初": 1128,
    "南宋绍兴元年十月九日": 1131.77,
    "南宋绍兴二年正月十四日": 1132.04,
    "南宋绍兴二年六月": 1132.45,
    "南宋乾道七年十月十六日": 1171.78,
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


def tp(w, title, type_, time):
    eid = entity_id(w, title, type_)
    tid = w.find_timepoint(eid, time)
    assert tid, (title, time)
    return tid


def alias_note(w, i, tid, quotation, field_name):
    cite(
        w, "Timepoints", tid, i, quotation,
        f"{F[i]['title']}的简称、别名只作名称证据，不另建实体。",
        field_name, note="纯简称、别名不另建实体",
    )


def parent_state(w, i, time, event, quotation, field_name=None):
    title = "大宗正司"
    eid = entity_id(w, title, "机构")
    tid = w.find_timepoint(eid, time)
    if tid is None:
        eid, tid = upsert_state(
            w, i, title, "机构", time, event, quotation,
            "中央宗室管理机构", f"为本条官职或下级机构建立 {title} 同期节点。",
            field_name,
        )
    else:
        cite(
            w, "Timepoints", tid, i, quotation,
            f"为 {title} 既有同期节点补充本条证据，不覆盖综合事件。", field_name,
        )
    rechain(w, eid, f"将大宗正司 {time} 节点纳入完整全局时间链。")
    return eid, tid


CLERKS = (
    ("大宗正司主押官", 1), ("大宗正司押司官", 1),
    ("大宗正司前行", 1), ("大宗正司后行", 12),
    ("大宗正司正名贴司", 10), ("大宗正司守阙正名贴司", 4),
    ("大宗正司私名贴司", 11),
)


def ensure_clerk_roster():
    """用第196条编制原文补齐本批七种吏额；既有专条节点不回写宽泛事件。"""
    i, roster = 196, field(196, "编制")
    w = W(i)
    parent = tp(w, "大宗正司", "机构", "宋代")
    touched = set()
    for title, quota in CLERKS:
        eid = w.find_entity(title, "官职")
        tid = w.find_timepoint(eid, "宋代") if eid else None
        if tid is None:
            eid, tid = upsert_state(
                w, i, title, "官职", "宋代", "大宗正司吏额之一", roster,
                "大宗正司吏", f"据大宗正司编制建立{title}及定额。", "编制",
                officer="吏",
            )
        else:
            cite(
                w, "Timepoints", tid, i, roster,
                f"为{title}既有专条节点补充第196条编制定额，不覆盖专条事件。", "编制",
            )
        staff(
            w, i, parent, tid, roster, f"大宗正司置{title.removeprefix('大宗正司')}{quota}人。",
            "编制", quota=quota, staff_type="吏",
        )
        touched.add(eid)
    for eid in touched:
        rechain(w, eid, "确认大宗正司吏额时间链。")
    w.commit()


def entry202():
    i = 202
    main, history, duty, rank, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    specs = (
        ("北宋熙宁三年二月十二日", "始置，参领大宗正司事并兼掌撰写笺奏", 2),
        ("南宋", "沿置一员，参领本司事并兼掌撰写笺奏", 1),
    )
    tids = {}
    for time, event, quota in specs:
        eid, tids[time] = upsert_state(
            w, i, "知大宗正司丞事", "官职", time, event, history,
            "大宗正司属官", f"据专条建立知大宗正司丞事 {time} 节点。", "职源与沿革",
            officer="职事官", grade="文臣升朝官以上充",
        )
        _, parent = parent_state(w, i, time, "置知大宗正司丞事", history, "职源与沿革")
        relation_quote = aliases if time.startswith("北宋") else roster
        relation_field = "简称与别名" if time.startswith("北宋") else "编制"
        staff(
            w, i, parent, tids[time], relation_quote,
            f"{time}知大宗正司丞事定额；北宋丞官二人是知、同知各一员。",
            relation_field, quota=1, staff_type="职事官",
        )
    cite(w, "Timepoints", tids["北宋熙宁三年二月十二日"], i, duty, "记录知丞事参领本司并掌笺奏的职掌。", "职掌")
    cite(w, "Timepoints", tids["北宋熙宁三年二月十二日"], i, rank, "记录知丞事由文臣升朝官以上充，不误作固定官品。", "品位")
    cite(w, "Timepoints", tids["北宋熙宁三年二月十二日"], i, roster, "记录北宋丞官合计二人、南宋知丞事一员。", "编制")
    alias_note(w, i, tids["北宋熙宁三年二月十二日"], aliases, "简称与别名")
    rechain(w, eid, "整理知大宗正司丞事北宋至南宋时间链。")
    w.commit()


def entry201():
    i = 201
    main, history, duty, rank, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    specs = (
        ("晋朝", "记室参军之官始置", "记室官源流", None),
        ("北宋景祐三年七月十九日", "随大宗正司建立而始置，掌撰写笺奏", "大宗正司属官", "职事官"),
        ("北宋熙宁三年二月十二日", "罢置，职事由知大宗正司丞事接替", "大宗正司属官", "职事官"),
    )
    tids = {}
    for time, event, category, officer in specs:
        eid, tids[time] = upsert_state(
            w, i, "大宗正司记室参军", "官职", time, event, history,
            category, f"据专条建立大宗正司记室参军 {time} 节点。", "职源与沿革",
            officer=officer,
        )
    _, parent = parent_state(w, i, "北宋景祐三年七月十九日", "置记室参军", history, "职源与沿革")
    staff(w, i, parent, tids["北宋景祐三年七月十九日"], roster, "大宗正司记室参军一人。", "编制", quota=1, staff_type="职事官")
    cite(w, "Timepoints", tids["北宋景祐三年七月十九日"], i, duty, "记录记室参军掌撰写笺奏。", "职掌")
    cite(w, "Timepoints", tids["北宋景祐三年七月十九日"], i, rank, "王府记室参军从八品只作同名官参照，不设为本官固定品级。", "品位", note="品位材料指王府同名官，仅作参照")
    alias_note(w, i, tids["北宋景祐三年七月十九日"], aliases, "简称")
    relationship(
        w, i, tids["北宋熙宁三年二月十二日"],
        tp(w, "知大宗正司丞事", "官职", "北宋熙宁三年二月十二日"),
        "前后演变", history, "记室参军罢后，其职事由知大宗正司丞事接替。", "职源与沿革",
    )
    rechain(w, eid, "连接大宗正司记室参军始置、罢置与晋朝源流。")
    w.commit()


def entry203():
    i = 203
    main, history, duty, rank, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "简称"),
    )
    w = W(i)
    eid, start = upsert_state(
        w, i, "同知大宗正司丞事", "官职", "北宋熙宁三年二月十二日",
        "始置，职掌同知大宗正司丞事，位次于知丞事", history,
        "大宗正司属官", "建立同知大宗正司丞事始置节点。", "职源与沿革",
        officer="职事官", grade="文臣朝官（通直郎）以上充",
    )
    _, south = upsert_state(
        w, i, "同知大宗正司丞事", "官职", "南宋", "未置", history,
        "大宗正司属官", "建立南宋未置节点。", "职源与沿革", officer="职事官",
    )
    _, parent = parent_state(w, i, "北宋熙宁三年二月十二日", "置同知大宗正司丞事", history, "职源与沿革")
    staff(w, i, parent, start, aliases, "同知大宗正司丞事一员。", "简称", quota=1, staff_type="职事官")
    cite(w, "Timepoints", start, i, duty, "记录同知丞事与知丞事职掌相同。", "职掌")
    cite(w, "Timepoints", start, i, rank, "记录同知丞事充任资格及位次。", "品位")
    alias_note(w, i, start, aliases, "简称")
    rechain(w, eid, "连接同知大宗正司丞事北宋始置与南宋未置节点。")
    w.commit()


def entry204():
    i, main = 204, F[204]["text"]
    w = W(i)
    eid, tid = upsert_state(
        w, i, "大宗正司讲书", "官职", "宋代",
        "掌教三十岁以上皇族成员，分赴睦亲宅等处讲授", main,
        "宗学官", "建立大宗正司讲书的归隶、对象与职掌。", officer="职事官",
    )
    _, parent = parent_state(w, i, "宋代", "置讲书", main)
    staff(w, i, parent, tid, main, "讲书隶大宗正司。", staff_type="职事官")
    rechain(w, eid, "确认大宗正司讲书时间链。")
    w.commit()


def entry205():
    i, main = 205, F[205]["text"]
    w = W(i)
    generic_eid, generic = upsert_state(
        w, i, "大宗正司教授", "官职", "宋代",
        "分大学教授与小学教授，分别教授十五岁以上至二十九岁及十五岁以下宗室", main,
        "宗学官", "建立大宗正司教授统称、分工与品级。", officer="职事官", grade="正八品",
    )
    _, parent = parent_state(w, i, "宋代", "置教授", main)
    staff(w, i, parent, generic, main, "教授隶大宗正司。", staff_type="职事官")
    touched = {generic_eid}
    for title, event in (
        ("大宗正司大学教授", "在大学教授十五岁以上至二十九岁宗室成员"),
        ("大宗正司小学教授", "在小学教授十五岁以下宗室成员"),
    ):
        eid, tid = upsert_state(
            w, i, title, "官职", "宋代", event, main,
            "宗学官", f"据专条建立{title}实例。", officer="职事官", grade="正八品",
        )
        relationship(w, i, generic, tid, "统称与实例", main, f"{title}为大宗正司教授实例。")
        touched.add(eid)
    for eid in touched:
        rechain(w, eid, "整理大宗正司教授及大学、小学教授时间链。")
    w.commit()


CASE_TITLES = {
    206: "大宗正司士案", 207: "大宗正司户案", 208: "大宗正司仪案",
    209: "大宗正司兵案", 210: "大宗正司刑案", 211: "大宗正司工案",
}


def entries206_211():
    for i, title in CASE_TITLES.items():
        main = F[i]["text"]
        w = W(i)
        eid, tid = upsert_state(
            w, i, title, "机构", "宋代", main, main,
            "大宗正司办事机构", f"据专条补足{title}职掌。",
        )
        relationship(
            w, i, tp(w, "大宗正司", "机构", "宋代"), tid,
            "上下级机构", main, f"{title}为大宗正司六案之一。",
        )
        rechain(w, eid, f"确认{title}时间链。")
        w.commit()


CLERK_ENTRY_TITLES = {
    212: "大宗正司主押官", 213: "大宗正司押司官",
    214: "大宗正司前行", 215: "大宗正司后行",
    216: "大宗正司正名贴司", 217: "大宗正司守阙正名贴司",
    218: "大宗正司私名贴司",
}


def entries212_218():
    quota_by_title = dict(CLERKS)
    for i, title in CLERK_ENTRY_TITLES.items():
        main = F[i]["text"]
        w = W(i)
        eid, tid = upsert_state(
            w, i, title, "官职", "宋代", main, main,
            "大宗正司吏", f"据专条补足{title}归隶、位次或职掌。", officer="吏",
        )
        staff(
            w, i, tp(w, "大宗正司", "机构", "宋代"), tid, main,
            f"{F[i]['title']}隶大宗正司。", quota=quota_by_title[title], staff_type="吏",
        )
        rechain(w, eid, f"确认{title}时间链。")
        w.commit()


def entry219():
    i, main, aliases = 219, F[219]["text"], field(219, "简称")
    w = W(i)
    specs = (
        ("南宋绍兴二年六月", "由广州返回临安行在所置司，与绍兴府大宗正行司并存"),
        ("南宋乾道七年十月十六日", "绍兴府大宗正行司并入，两司合一，成为南宋驻京师大宗正司"),
    )
    tids = {}
    for time, event in specs:
        eid, tids[time] = upsert_state(
            w, i, "行在大宗正司", "机构", time, event, main,
            "南宋宗室管理机构", f"据专条建立或校订行在大宗正司 {time} 节点。",
        )
        parent_eid, parent = parent_state(w, i, time, "行在大宗正司在此运行", main)
        relationship(w, i, parent, tids[time], "统称与实例", main, "行在大宗正司为南宋大宗正司的驻京分支。")
    alias_note(w, i, tids["南宋绍兴二年六月"], aliases, "简称")
    rechain(w, eid, "整理行在大宗正司南宋迁徙、并存与合并时间链。")
    rechain(w, parent_eid, "整理大宗正司南宋分支时间链。")
    w.commit()


def canonicalize_shaoxing_branch(w, quotation):
    eid = entity_id(w, "绍兴府大宗正行司", "机构")
    broad = w.find_timepoint(eid, "南宋建炎、绍兴初")
    exact = w.find_timepoint(eid, "南宋绍兴二年正月十四日")
    if broad and not exact:
        w.conn.execute(
            "update Timepoints set time=?,event=?,quotation=?,attr_category=? where id=?",
            (
                "南宋绍兴二年正月十四日",
                "行在所由绍兴府迁临安后，留在绍兴府的行在大宗正司改称绍兴府大宗正行司",
                quotation, "南宋宗室管理机构", broad,
            ),
        )
        w._br(
            "Timepoints", broad,
            "据专条将宽泛‘南宋建炎、绍兴初’节点规范为绍兴二年正月十四日改称节点。",
        )
        exact = broad
    assert exact
    return eid, exact


def entry220():
    i, main, aliases = 220, F[220]["text"], field(220, "简称")
    w = W(i)
    branch_eid, branch = canonicalize_shaoxing_branch(w, main)
    cite(w, "Timepoints", branch, i, main, "记录绍兴府大宗正行司的形成过程。")
    in_capital_eid, move = upsert_state(
        w, i, "行在大宗正司", "机构", "南宋绍兴二年正月十四日",
        "行在所由绍兴府迁至临安府；留在绍兴府者改称绍兴府大宗正行司", main,
        "南宋宗室管理机构", "建立行在大宗正司迁临安及绍兴分支形成节点。",
    )
    relationship(
        w, i, tp(w, "行在大宗正司", "机构", "南宋绍兴元年十月九日"),
        branch, "前后演变", main, "行在所迁临安后，留在绍兴府的机构改称绍兴府大宗正行司。",
    )
    merged = tp(w, "行在大宗正司", "机构", "南宋乾道七年十月十六日")
    relationship(w, i, branch, merged, "前后演变", main, "绍兴府大宗正行司于乾道七年并入临安行在大宗正司。")
    alias_note(w, i, branch, aliases, "简称")
    rechain(w, branch_eid, "整理绍兴府大宗正行司形成与并入时间链。")
    rechain(w, in_capital_eid, "整理行在大宗正司绍兴至临安时间链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(201, 221)] == [
        "记室参军", "知大宗正司丞事", "同知大宗正司丞事", "讲书", "教授",
        "士案", "户案", "仪案", "兵案", "刑案", "工案", "主押官",
        "押司官", "前行", "后行", "正名贴司", "守阙正名贴司", "私名贴司",
        "行在大宗正司", "绍兴府大宗正行司",
    ]
    ensure_clerk_roster()
    entry202()
    entry201()
    entry203()
    entry204()
    entry205()
    entries206_211()
    entries212_218()
    entry219()
    entry220()


if __name__ == "__main__":
    main()
