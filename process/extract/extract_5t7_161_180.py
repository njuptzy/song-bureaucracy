#!/usr/bin/env python3
"""提取 chapter5t7 第161–180条：宗正寺官吏、太庙令与西京诸陵。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter
import extract_5t7_141_160 as previous


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


F = {i: load(i) for i in range(161, 181)}


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
    "秦汉": -200, "东汉": 25, "西晋": 265, "北齐": 550,
    "宋代": 960, "宋前期": 970, "北宋": 960, "北宋前期": 970,
    "北宋大中祥符九年二月": 1016.12,
    "北宋天禧元年": 1017, "北宋仁宗嘉祐六年十月十四日": 1061.79,
    "北宋元丰新制": 1082.5, "北宋元丰五年新制": 1082.5,
    "北宋元丰改制后": 1082.5, "北宋元丰八年六月": 1085.42,
    "北宋徽宗朝": 1100, "南宋": 1127, "南宋初": 1127.1,
    "南宋建炎三年": 1129, "南宋绍兴三年后": 1133.1,
    "南宋绍兴五年": 1135, "南宋绍兴十年": 1140,
    "南宋绍兴以后": 1140.1, "南宋隆兴元年七月": 1163.5,
    "南宋隆兴二年闰十一月": 1164.9,
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


def parent_state(w, i, title, time, event, quotation, field_name=None):
    eid = entity_id(w, title, "机构")
    tid = w.find_timepoint(eid, time)
    if tid is None:
        eid, tid = upsert_state(
            w, i, title, "机构", time, event, quotation,
            "中央机构" if title in {"宗正寺", "太常寺"} else "陵寝管理机构",
            f"为本条官职或下级机构建立 {title} 同期节点。", field_name,
        )
    else:
        cite(w, "Timepoints", tid, i, quotation,
             f"为 {title} 既有同期节点补充本条证据，不覆盖机构综合事件。", field_name)
    rechain(w, eid, f"将 {title} 的 {time} 节点纳入完整全局时间链。")
    return eid, tid


def ensure_instance_state(w, i, title, type_, time, event, quotation, category,
                          decision, field_name=None, *, officer=None):
    """统称条只补建缺失实例；既有节点保留专条更细的事件文本。"""
    eid = w.find_entity(title, type_)
    tid = w.find_timepoint(eid, time) if eid else None
    if tid is not None:
        cite(w, "Timepoints", tid, i, quotation, decision, field_name)
        return eid, tid
    return upsert_state(
        w, i, title, type_, time, event, quotation, category, decision,
        field_name, officer=officer,
    )


def entry161():
    i, main, aliases = 161, F[161]["text"], field(161, "简称")
    w = W(i)
    parent_eid, parent = parent_state(
        w, i, "宗正寺", "北宋大中祥符九年二月",
        "置权知宗正寺事为副贰", main,
    )
    eid, tid = upsert_state(
        w, i, "权知宗正寺事", "官职", "北宋大中祥符九年二月",
        "见置，以朝官充，为宗正寺副贰", main, "宗正寺差遣官",
        "建立权知宗正寺事的初见、充任与序位节点。", officer="差遣官",
    )
    staff(w, i, parent, tid, main, "权知宗正寺事为本寺副贰。", staff_type="差遣官")
    alias_note(w, i, tid, aliases, "简称")
    rechain(w, parent_eid, "整理宗正寺大中祥符时间链。")
    rechain(w, eid, "确认权知宗正寺事时间链。")
    w.commit()


def entry162():
    i = 162
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    specs = (
        ("东汉", "已有宗正卿之名", history, "古代宗室官源流", None, None),
        ("北齐", "始称宗正寺卿", history, "宗正寺长官", None, None),
        ("宋前期", "为兼官，多以它官兼，祭祀用作行事官；无知、判官时过问寺事", duty,
         "宗正寺长官", "行事官、兼官", "正四品"),
        ("北宋元丰新制", "新制定员一人，但虚长贰不除；掌牒谱图籍、宗室派别昭穆与大小学政令", duty,
         "宗正寺长官", "职事官", "正四品"),
        ("北宋徽宗朝", "元丰新制后至此方除人", roster, "宗正寺长官", "职事官", "正四品"),
        ("南宋", "不置宗正寺卿", history, "宗正寺长官", "职事官", "正四品"),
    )
    eid = None
    tids = {}
    for time, event, quotation, category, officer, grade in specs:
        eid, tids[time] = upsert_state(
            w, i, "宗正寺卿", "官职", time, event, quotation, category,
            f"据专条建立或校订宗正寺卿 {time} 节点。",
            "职掌" if quotation == duty else ("编制" if quotation == roster else "职源与沿革"),
            officer=officer, grade=grade,
        )
    cite(w, "Timepoints", tids["宋前期"], i, rank, "记录宗正寺卿正四品及在九寺中的高位次。", "品位")
    cite(w, "Timepoints", tids["北宋元丰新制"], i, roster, "记录元丰定员一人而虚位至徽宗朝始除的编制。", "编制")
    alias_note(w, i, tids["宋前期"], aliases, "简称与别名")
    for time, quota in (("宋前期", None), ("北宋元丰新制", 1)):
        _, parent = parent_state(w, i, "宗正寺", time, "置宗正寺卿", roster, "编制")
        staff(w, i, parent, tids[time], roster, f"{time}宗正寺卿隶本寺。", "编制", quota=quota, staff_type="兼官" if quota is None else "职事官")
    rechain(w, eid, "重建宗正寺卿全局历史时间链。")
    w.commit()


def entry163():
    i = 163
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    specs = (
        ("北齐", "始置宗正寺少卿", history, "宗正寺副长官", None),
        ("北宋前期", "由它官兼领，为祭祀行事官二人；无知、判官时过问寺事", duty, "宗正寺副长官", "行事官、兼官"),
        ("北宋元丰五年新制", "正式除授，为本寺副长官，佐卿领寺事，定员一人", duty, "宗正寺副长官", "职事官"),
        ("南宋初", "由太常少卿兼", roster, "宗正寺副长官", "兼官"),
        ("南宋绍兴三年后", "复置宗正寺少卿", roster, "宗正寺副长官", "职事官"),
    )
    tids = {}
    for time, event, quotation, category, officer in specs:
        eid, tids[time] = upsert_state(
            w, i, "宗正寺少卿", "官职", time, event, quotation, category,
            f"据专条建立或校订宗正寺少卿 {time} 节点。",
            "职掌" if quotation == duty else ("编制" if quotation == roster else "职源与沿革"),
            officer=officer, grade="从五品" if time != "北齐" else None,
        )
    cite(w, "Timepoints", tids["北宋前期"], i, rank, "记录宗正寺少卿从五品及与七寺少卿的位次差别。", "品位")
    alias_note(w, i, tids["北宋前期"], aliases, "简称与别名")
    for time, quota in (("北宋前期", 2), ("北宋元丰五年新制", 1)):
        parent_time = "宋前期" if time == "北宋前期" else "北宋元丰新制"
        _, parent = parent_state(w, i, "宗正寺", parent_time, "置宗正寺少卿", roster, "编制")
        staff(w, i, parent, tids[time], roster, f"{time}宗正寺少卿隶本寺。", "编制", quota=quota, staff_type="行事官" if quota == 2 else "职事官")
    rechain(w, eid, "重建宗正寺少卿全局历史时间链。")
    w.commit()


def entry164():
    i = 164
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    specs = (
        ("秦汉", "已有宗正丞", history, "宗正官源流", None, None),
        ("北齐", "始有宗正寺丞", history, "宗正寺属官", None, None),
        ("宋前期", "无职事，为文臣寄禄官阶；祭祀行事官曾置二员", duty, "宗正寺属官", "寄禄官、行事官", None),
        ("北宋元丰新制", "为职事官，参领寺事；长贰不除时专听寺事，定员一人", duty, "宗正寺属官", "职事官", "从七品"),
        ("南宋建炎三年", "罢宗正寺丞", history, "宗正寺属官", "职事官", "从七品"),
        ("南宋绍兴五年", "复置宗正寺丞", history, "宗正寺属官", "职事官", "从七品"),
    )
    tids = {}
    for time, event, quotation, category, officer, grade in specs:
        eid, tids[time] = upsert_state(
            w, i, "宗正寺丞", "官职", time, event, quotation, category,
            f"据专条建立或校订宗正寺丞 {time} 节点。",
            "职掌" if quotation == duty else "职源与沿革", officer=officer, grade=grade,
        )
    cite(w, "Timepoints", tids["北宋元丰新制"], i, rank, "记录元丰后宗正丞从七品及三丞位次。", "品位")
    cite(w, "Timepoints", tids["宋前期"], i, roster, "记录宋前期祭祀行事官二员。", "编制")
    alias_note(w, i, tids["宋前期"], aliases, "简称与别名")
    for time, quota in (("宋前期", 2), ("北宋元丰新制", 1)):
        _, parent = parent_state(w, i, "宗正寺", time, "置宗正寺丞", roster, "编制")
        staff(w, i, parent, tids[time], roster, f"{time}宗正寺丞隶本寺。", "编制", quota=quota, staff_type="行事官" if quota == 2 else "职事官")
    rechain(w, eid, "重建宗正寺丞全局历史时间链。")
    w.commit()


def entry165():
    i, main, aliases = 165, F[165]["text"], field(165, "简称")
    w = W(i)
    eid, tid = upsert_state(
        w, i, "知宗正丞事", "官职", "宋前期",
        "判寺官阙时以宗姓朝官以上充，掌宗庙、诸陵荐享及皇族之籍", main,
        "宗正寺差遣官", "据专条细化判寺阙时的充任与职掌。", officer="差遣官",
    )
    _, parent = parent_state(w, i, "宗正寺", "宋前期", "判寺阙时置知宗正丞事", main)
    staff(w, i, parent, tid, main, "知宗正丞事在判寺官阙时领寺事。", staff_type="差遣官")
    alias_note(w, i, tid, aliases, "简称")
    rechain(w, eid, "确认知宗正丞事时间链。")
    w.commit()


def entry166():
    i = 166
    history, duty, rank, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称"),
    )
    assert aliases.endswith("宗正并省一员。”")
    w = W(i)
    specs = (
        ("西晋", "始置宗正主簿", history, "宗正主簿源流", None, None),
        ("北齐", "始设宗正寺主簿", history, "宗正寺属官", None, None),
        ("北宋天禧元年", "始以卫尉寺丞赵鼎兼宗正寺主簿", history, "宗正寺属官", "兼官", None),
        ("宋前期", "为文臣迁转官阶，偶作职事官", duty, "宗正寺属官", "寄禄官、偶作职事官", None),
        ("北宋元丰新制", "为职事官，掌勾稽本寺簿书及杂务，定员一人", duty, "宗正寺属官", "职事官", "从八品"),
        ("南宋建炎三年", "罢宗正寺主簿", history, "宗正寺属官", "职事官", "从八品"),
        ("南宋绍兴十年", "复置宗正寺主簿", history, "宗正寺属官", "职事官", "从八品"),
        ("南宋隆兴元年七月", "省宗正寺主簿", history, "宗正寺属官", "职事官", "从八品"),
        ("南宋隆兴二年闰十一月", "复置宗正寺主簿", history, "宗正寺属官", "职事官", "从八品"),
    )
    tids = {}
    for time, event, quotation, category, officer, grade in specs:
        eid, tids[time] = upsert_state(
            w, i, "宗正寺主簿", "官职", time, event, quotation, category,
            f"据专条建立或校订宗正寺主簿 {time} 节点。",
            "职掌" if quotation == duty else "职源与沿革", officer=officer, grade=grade,
        )
    cite(w, "Timepoints", tids["北宋元丰新制"], i, rank, "记录元丰正名后为从八品。", "品位")
    cite(w, "Timepoints", tids["北宋元丰新制"], i, roster, "记录宗正寺主簿一员。", "编制")
    alias_note(w, i, tids["北宋元丰新制"], aliases, "简称")
    _, parent = parent_state(w, i, "宗正寺", "北宋元丰新制", "置宗正寺主簿", roster, "编制")
    staff(w, i, parent, tids["北宋元丰新制"], roster, "元丰新制宗正寺主簿一员隶本寺。", "编制", quota=1, staff_type="职事官")
    rechain(w, eid, "重建宗正寺主簿全局历史时间链。")
    w.commit()


def entry167():
    assert F[167]["title"] == "主簿"
    assert F[167]["text"] == ""
    assert F[167]["fields"] == {"_placeholder": True, "__status__": "placeholder"}


def entry168():
    i, main = 168, F[168]["text"]
    w = W(i)
    parent_eid, parent = parent_state(
        w, i, "宗正寺", "北宋仁宗嘉祐六年十月十四日",
        "特置宗正寺伴读", main,
    )
    eid, tid = upsert_state(
        w, i, "宗正寺伴读", "官职", "北宋仁宗嘉祐六年十月十四日",
        "特以诸王宫大小学侍讲王猎为之，教授宗室子弟，带馆职；其后未见除人", main,
        "宗正寺差遣官", "建立宗正寺伴读的特置、职掌及后续除授情况。", officer="差遣官、馆职",
    )
    staff(w, i, parent, tid, main, "宗正寺伴读教授宗室子弟。", staff_type="差遣官")
    for touched in (parent_eid, eid):
        rechain(w, touched, "整理嘉祐六年宗正寺伴读时间链。")
    w.commit()


def entry169_170():
    i, main, aliases = 169, F[169]["text"], field(169, "简称")
    w = W(i)
    eid, case = upsert_state(
        w, i, "宗正寺属籍案", "机构", "北宋元丰新制",
        "主行编修宗属名册，依三系与亲疏逐年登记宗子宗女等生死官爵赐谥，设手分", main,
        "宗正寺所属案", "将主行编修属籍案归并到既有宗正寺属籍案，不另建纯简称实体。",
    )
    parent_eid, parent = parent_state(w, i, "宗正寺", "北宋元丰新制", "分置属籍案", aliases, "简称")
    relationship(w, i, parent, case, "上下级机构", aliases, "属籍案为宗正寺分案之一。", "简称")
    clerk_eid, clerk = upsert_state(
        w, i, "宗正寺手分", "官职", "北宋元丰新制", "承办宗正寺分案事务", main,
        "宗正寺公吏", "原文明言属籍案吏额有手分。", officer="吏",
    )
    staff(w, i, case, clerk, main, "属籍案设手分。", staff_type="吏")
    alias_note(w, i, case, aliases, "简称")
    for touched in (eid, parent_eid, clerk_eid):
        rechain(w, touched, "整理宗正寺属籍案及手分时间链。")
    w.commit()

    i, main = 170, F[170]["text"]
    w = W(i)
    eid, case = upsert_state(
        w, i, "宗正寺知杂案", "机构", "北宋元丰新制", "承办宗正寺杂务，吏额有手分", main,
        "宗正寺所属案", "保留专条明确的知杂案原文，不静默改为既有知籍案。",
    )
    _, parent = parent_state(w, i, "宗正寺", "北宋元丰新制", "分置知杂案", main)
    relationship(w, i, parent, case, "上下级机构", main, "知杂案为宗正寺办事机构之一。")
    clerk = tp(w, "宗正寺手分", "官职", "北宋元丰新制")
    staff(w, i, case, clerk, main, "知杂案吏额有手分。", staff_type="吏")
    rechain(w, eid, "确认宗正寺知杂案时间链。")
    w.commit()


def entry171_173():
    i, main, aliases = 171, F[171]["text"], field(171, "别称")
    w = W(i)
    collective_eid, collective = upsert_state(
        w, i, "宗正寺职掌", "官职", "宋代", "宗正寺胥吏总名", main,
        "宗正寺胥吏统称", "建立原文明确的胥吏总名。", officer="吏",
    )
    member_eids = set()
    for title in ("宗正寺胥长", "宗正寺胥佐", "宗正寺胥史", "宗正寺贴书", "宗正寺楷书"):
        eid, tid = ensure_instance_state(
            w, i, title, "官职", "宋代", f"宗正寺职掌所包含的{title.removeprefix('宗正寺')}", main,
            "宗正寺胥吏", f"原文明举{title}为宗正寺职掌实例。", officer="吏",
        )
        relationship(w, i, collective, tid, "统称与实例", main, f"宗正寺职掌包括{title}。")
        member_eids.add(eid)
    for title in ("宗正寺府吏", "宗正寺驱使官", "宗正寺庙直官"):
        eid, tid = ensure_instance_state(
            w, i, title, "官职", "宋前期", f"宋前期宗正寺职掌名目：{title.removeprefix('宗正寺')}", main,
            "宗正寺胥吏", f"原文明举{title}为宋前期宗正寺职掌名目。", officer="吏",
        )
        relationship(w, i, collective, tid, "统称与实例", main, f"宋前期宗正寺职掌尚有{title}。")
        member_eids.add(eid)
    alias_note(w, i, collective, aliases, "别称")
    rechain(w, collective_eid, "确认宗正寺职掌统称时间链。")
    for eid in member_eids:
        rechain(w, eid, "整理宗正寺职掌实例的全局时间链。")
    w.commit()

    i, main = 172, F[172]["text"]
    w = W(i)
    eid, tid = upsert_state(
        w, i, "宗正寺胥长", "官职", "宋代",
        "宗正寺胥史中位次最高，由胥佐、胥史递迁；任满五年且入仕三十年可出职补将仕郎", main,
        "宗正寺胥吏", "据胥长专条细化序位、递迁与出职条件。", officer="吏",
    )
    _, parent = parent_state(w, i, "宗正寺", "宋代", "置胥长等胥吏", main)
    staff(w, i, parent, tid, main, "胥长隶宗正寺。", staff_type="吏")
    rechain(w, eid, "整理宗正寺胥长全局时间链。")
    w.commit()

    i, main = 173, F[173]["text"]
    w = W(i)
    eid, tid = upsert_state(
        w, i, "宗正寺府吏", "官职", "宋前期", "即府史，掌宗正寺文书行遣等事，置二人", main,
        "宗正寺公吏", "据府吏专条细化别称、职掌与宋前期定员。", officer="吏",
    )
    _, parent = parent_state(w, i, "宗正寺", "宋前期", "置府吏", main)
    staff(w, i, parent, tid, main, "宋前期宗正寺府吏二人。", quota=2, staff_type="吏")
    rechain(w, eid, "确认宗正寺府吏时间链。")
    w.commit()


def entry174():
    i = 174
    main, history, duty, rank = F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位")
    w = W(i)
    specs = (
        ("东汉", "有太常太庙令", history, "太庙官源流"),
        ("北齐", "为太常寺太庙署令，掌郊祀、太庙、社稷等事", history, "太常寺属官"),
        ("北宋", "沿置，掌宗庙荐新、七祀及功臣从享之礼", duty, "太庙官"),
        ("北宋元丰改制后", "改制后隶宗正寺，掌宗庙荐新、七祀及功臣从享之礼", main, "宗正寺属官"),
    )
    tids = {}
    for time, event, quotation, category in specs:
        eid, tids[time] = upsert_state(
            w, i, "太庙令", "官职", time, event, quotation, category,
            f"据专条建立或校订太庙令 {time} 节点。",
            "职掌" if quotation == duty else (None if quotation == main else "职源与沿革"),
            officer="职事官", grade="正九品" if time in {"北宋", "北宋元丰改制后"} else None,
        )
    cite(w, "Timepoints", tids["北宋"], i, rank, "记录太庙令与太社令、籍田令同为正九品。", "品位")
    _, taichang = parent_state(w, i, "太常寺", "北齐", "置太庙署令", history, "职源与沿革")
    staff(w, i, taichang, tids["北齐"], history, "北齐太庙署令隶太常寺。", "职源与沿革", staff_type="职事官")
    _, zongzheng = parent_state(w, i, "宗正寺", "北宋元丰改制后", "太庙令归隶宗正寺", main)
    staff(w, i, zongzheng, tids["北宋元丰改制后"], main, "本条标明太庙令隶宗正寺。", quota=1, staff_type="职事官")
    rechain(w, eid, "重建太庙令东汉至北宋的全局时间链。")
    w.commit()


EIGHT_TOMBS = (
    "永安陵所", "永昌陵所", "永熙陵所", "永定陵所",
    "永昭陵所", "永厚陵所", "永裕陵所", "永泰陵所",
)


def entry175():
    i, main, duty, roster = 175, F[175]["text"], field(175, "职掌"), field(175, "编制")
    w = W(i)
    collective_eid, collective = upsert_state(
        w, i, "西京诸陵所", "机构", "北宋", "西京七帝八陵各陵所总名，随皇陵数增加而增加", main,
        "皇陵管理机构统称", "建立西京诸陵所统称及七帝八陵范围。",
    )
    tomb_tps = {}
    touched = {collective_eid}
    for title in EIGHT_TOMBS:
        eid, tid = upsert_state(
            w, i, title, "机构", "北宋", "西京诸陵所所指各陵管理官司", main,
            "皇陵管理机构", f"原文将{title}列为西京诸陵所实例。",
        )
        relationship(w, i, collective, tid, "统称与实例", main, f"西京诸陵所包括{title}。")
        tomb_tps[title] = tid
        touched.add(eid)
    triad_eid, triad = upsert_state(
        w, i, "三陵所", "机构", "北宋", "宣祖永安陵、太祖永昌陵、太宗永熙陵三陵管理官司统称", main,
        "皇陵管理机构统称", "为下条明确的三陵体系建立统称节点。",
    )
    touched.add(triad_eid)
    for title in EIGHT_TOMBS[:3]:
        relationship(w, i, triad, tomb_tps[title], "统称与实例", main, f"三陵所包括{title}。")
    post_tps = {}
    for title, category, officer in (
        ("陵使", "诸陵所差遣官", "差遣官"),
        ("宗正寺诸陵副使", "诸陵所差遣官", "差遣官"),
        ("宗正寺诸陵都监", "诸陵所差遣官", "差遣官"),
        ("陵巡检", "诸陵所差遣官", "差遣官"),
        ("诸陵勾当香火内品", "诸陵所内品", "内品"),
    ):
        eid, tid = ensure_instance_state(
            w, i, title, "官职", "北宋", f"各陵所均设{title}", roster, category,
            f"原文明言各陵所编制均有{title}。", "编制", officer=officer,
        )
        post_tps[title] = tid
        touched.add(eid)
    for tomb, tomb_tp in tomb_tps.items():
        for title, post_tp in post_tps.items():
            quota = 2 if title == "陵巡检" else None
            decision = f"{tomb}置{title}" + ("二员，每员统士兵百人。" if quota else "。")
            staff(w, i, tomb_tp, post_tp, roster, decision, "编制", quota=quota,
                  staff_type="内品" if title == "诸陵勾当香火内品" else "差遣官")
    cite(w, "Timepoints", collective, i, duty, "记录西京诸陵所看守、荐献及修补陵寝园庙职掌。", "职掌")
    cite(w, "Timepoints", collective, i, roster, "记录奉先、奉园等指挥合计七千余官兵；不拆分为各指挥或各陵的无据定额。", "编制")
    for eid in touched:
        rechain(w, eid, "整理西京八陵、三陵与陵官的全局时间链。")
    w.commit()


def entry176_177():
    i, main = 176, F[176]["text"]
    w = W(i)
    triad = tp(w, "三陵所", "机构", "北宋")
    touched = set()
    for title, event in (("三陵使", "掌管理三陵所公事"), ("三陵副使", "佐三陵使管理三陵所公事")):
        eid, tid = upsert_state(w, i, title, "官职", "北宋", event, main, "三陵所差遣官", f"将合并标题拆为原文明确的{title}。", officer="差遣官")
        staff(w, i, triad, tid, main, f"{title}掌三陵所公事。", staff_type="差遣官")
        touched.add(eid)
    for eid in touched:
        rechain(w, eid, "确认三陵使、副使时间链。")
    w.commit()

    i, main = 177, F[177]["text"]
    w = W(i)
    eid, tid = upsert_state(w, i, "三陵都监", "官职", "北宋", "监督三陵所公事", main, "三陵所差遣官", "建立三陵都监的管辖范围与职掌。", officer="差遣官")
    staff(w, i, tp(w, "三陵所", "机构", "北宋"), tid, main, "三陵都监监督三陵所公事。", staff_type="差遣官")
    rechain(w, eid, "确认三陵都监时间链。")
    w.commit()


def entry178():
    i, main = 178, F[178]["text"]
    w = W(i)
    generic = {}
    for title, event in (("陵使", "诸陵各设，掌陵所公事"), ("宗正寺诸陵副使", "诸陵各设，由内侍充，佐陵使掌陵所公事")):
        eid, tid = upsert_state(w, i, title, "官职", "北宋", event, main, "诸陵所差遣官", f"据陵使、副使专条细化{title}职掌。", officer="差遣官")
        generic[title] = (eid, tid)
    tomb = tp(w, "永裕陵所", "机构", "北宋")
    for title, parent_title, event in (
        ("永裕陵使", "陵使", "元丰八年六月以石得一为永裕陵使"),
        ("永裕陵副使", "宗正寺诸陵副使", "元丰八年六月以宋用臣为永裕陵副使"),
    ):
        eid, tid = upsert_state(w, i, title, "官职", "北宋元丰八年六月", event, main, "永裕陵所差遣官", f"原文明举{title}的除授实例。", officer="差遣官")
        relationship(w, i, generic[parent_title][1], tid, "统称与实例", main, f"{title}为{parent_title}在永裕陵所的实例。")
        staff(w, i, tomb, tid, main, f"{title}隶永裕陵所。", staff_type="差遣官")
        rechain(w, eid, f"确认{title}时间链。")
    for eid, _ in generic.values():
        rechain(w, eid, "整理陵使、诸陵副使全局时间链。")
    w.commit()


def entry179():
    i, main, aliases = 179, F[179]["text"], field(179, "简称")
    w = W(i)
    generic_eid, generic = upsert_state(
        w, i, "宗正寺诸陵都监", "官职", "北宋", "诸陵所均置，掌奉守陵寝公事的监视、督察", main,
        "诸陵所差遣官", "据陵都监专条细化诸陵都监职掌。", officer="差遣官",
    )
    eid, tid = upsert_state(
        w, i, "永定陵都监", "官职", "北宋元丰二年二月", "张克明任永定陵都监，监守本陵公事", main,
        "永定陵所差遣官", "原文明举永定陵都监实例。", officer="差遣官",
    )
    relationship(w, i, generic, tid, "统称与实例", main, "永定陵都监为诸陵都监实例。")
    staff(w, i, tp(w, "永定陵所", "机构", "北宋"), tid, main, "永定陵都监隶永定陵所。", staff_type="差遣官")
    alias_note(w, i, generic, aliases, "简称")
    rechain(w, generic_eid, "整理诸陵都监全局时间链。")
    rechain(w, eid, "确认永定陵都监时间链。")
    w.commit()


def entry180():
    i, main = 180, F[180]["text"]
    w = W(i)
    eid, tid = upsert_state(
        w, i, "陵巡检", "官职", "北宋", "诸陵各置内外巡检二员，掌陵寝内外警卫巡逻，每员各统士兵百人", main,
        "诸陵所差遣官", "据陵巡检专条细化每陵定员、职掌与统兵数。", officer="差遣官",
    )
    for tomb in EIGHT_TOMBS:
        staff(w, i, tp(w, tomb, "机构", "北宋"), tid, main,
              f"{tomb}内外巡检二员，每员统士兵百人；二员是每陵定额，不是八陵合计。",
              quota=2, staff_type="差遣官")
    rechain(w, eid, "确认陵巡检时间链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(161, 181)] == [
        "权知宗正寺事", "宗正寺卿", "宗正寺少卿", "宗正寺丞", "知宗正丞事",
        "宗正寺主簿", "主簿", "宗正寺伴读", "主行编修属籍案", "知杂案",
        "宗正寺职掌", "胥长", "府吏", "太庙令", "西京诸陵所",
        "三陵使、副使", "三陵都监", "陵使、副陵使", "陵都监", "陵巡检",
    ]
    entry161()
    entry162()
    entry163()
    entry164()
    entry165()
    entry166()
    entry167()
    entry168()
    entry169_170()
    entry171_173()
    entry174()
    entry175()
    entry176_177()
    entry178()
    entry179()
    entry180()


if __name__ == "__main__":
    main()
