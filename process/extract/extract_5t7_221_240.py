#!/usr/bin/env python3
"""提取 chapter5t7 第221-240条：外宗正司、财用司与敦宗院。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter
import extract_5t7_201_220 as previous


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


F = {i: load(i) for i in range(221, 241)}


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
    tid = w.find_timepoint(eid, time)
    if tid is None:
        tid = w.timepoint(
            eid, time, event, decision, quotation,
            attr_category=category, attr_officer_type=officer,
            attr_grade=grade, chain="none",
        )
    else:
        row = w.conn.execute(
            "select attr_category,attr_officer_type,attr_grade from Timepoints "
            "where id=?", (tid,)
        ).fetchone()
        updates, params = [], []
        for col, old, new in (
            ("attr_category", row[0], category),
            ("attr_officer_type", row[1], officer),
            ("attr_grade", row[2], grade),
        ):
            if new and not old:
                updates.append(f"{col}=?")
                params.append(new)
        if updates:
            params.append(tid)
            w.conn.execute(
                f"update Timepoints set {', '.join(updates)} where id=?", params
            )
            w._br("Timepoints", tid, f"复用既有节点并补属性：{decision}")
    cite(w, "Timepoints", tid, i, quotation, decision, field_name, note=note)
    return eid, tid


def relation(w, i, subject, object_, relation_type, quotation, decision,
             field_name=None, **kwargs):
    rid = w.relationship(
        subject, object_, relation_type, decision, quotation, **kwargs
    )
    cite(w, "Relationships", rid, i, quotation, decision, field_name)
    return rid


def staff(w, i, parent, post, quotation, decision, field_name=None,
          *, quota=None, staff_type="职事官"):
    rid = relation(
        w, i, parent, post, "编制隶属", quotation, decision, field_name,
        staff_quota=quota, staff_type=staff_type,
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
    "宋代": 960, "北宋": 960, "南宋": 1127,
    "北宋崇宁元年十一月十二日": 1102.86,
    "北宋大观三年三月二十三日": 1109.22,
    "北宋政和二年七月八日": 1112.52,
    "南宋初": 1127.1,
    "南宋建炎三年十二月": 1129.95,
    "南宋绍兴元年": 1131.1,
    "南宋绍兴元年九月十九日": 1131.70,
    "南宋绍兴二年正月十四日": 1132.04,
    "南宋绍兴年间": 1132.20,
    "南宋裁减后": 1132.30,
    "南宋绍兴五年": 1135,
    "南宋乾道七年十月十六日": 1171.78,
    "南宋淳熙十六年二月": 1189.12,
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
    eid = w.find_entity(title, type_)
    assert eid, (title, type_)
    tid = w.find_timepoint(eid, time)
    assert tid, (title, time)
    return tid


def alias_note(w, i, tid, quotation, field_name):
    cite(
        w, "Timepoints", tid, i, quotation,
        f"{F[i]['title']}的简称、别名只作名称证据，不另建实体。",
        field_name, note="纯简称、别名不另建实体",
    )


def parent_tp(w, i, title, time, quotation, category, field_name=None):
    eid = w.find_entity(title, "机构")
    assert eid, title
    tid = w.find_timepoint(eid, time)
    if tid is None:
        eid, tid = state(
            w, i, title, "机构", time, "本条所见运行节点", quotation,
            category, f"为本条建立{title}同期承载节点。", field_name,
        )
    else:
        cite(
            w, "Timepoints", tid, i, quotation,
            f"为{title}既有同期节点补充本条证据。", field_name,
        )
    rechain(w, eid, f"将{title}的{time}节点纳入完整全局时间链。")
    return tid


def entry221():
    i, main, aliases = 221, F[221]["text"], field(221, "简称")
    w = W(i)
    eid, post = state(
        w, i, "绍兴府大宗正行司主管财用", "官职", "南宋绍兴年间",
        "掌检察帮书，管领本司官吏及南班宗室请给钱粮、衣物等财用事",
        main, "外宗正司财用官", "按全称消歧建立绍兴府大宗正行司主管财用。",
        officer="职事官",
    )
    parent = parent_tp(
        w, i, "绍兴府大宗正行司", "南宋绍兴二年正月十四日", main,
        "南宋宗室管理机构",
    )
    staff(w, i, parent, post, aliases, "绍兴府大宗正行司置财用一员。", "简称", quota=1)
    alias_note(w, i, post, aliases, "简称")
    rechain(w, eid, "整理绍兴府大宗正行司主管财用时间链。")
    w.commit()


def entry222():
    i, main, aliases = 222, F[222]["text"], field(222, "别称")
    w = W(i)
    eid, initial = state(
        w, i, "绍兴府大宗正行司教授", "官职", "南宋绍兴年间",
        "教导本司南班宗子，初置二员", main,
        "宗学官", "按所隶机构消歧建立绍兴府大宗正行司教授。",
        officer="职事官",
    )
    _, reduced = state(
        w, i, "绍兴府大宗正行司教授", "官职", "南宋裁减后",
        "宫教裁减一员后留一员", aliases,
        "宗学官", "记录教授由二员裁减一员后的编制。", "别称",
        officer="职事官",
    )
    parent1 = parent_tp(w, i, "绍兴府大宗正行司", "南宋绍兴二年正月十四日", main, "南宋宗室管理机构")
    parent2 = parent_tp(w, i, "绍兴府大宗正行司", "南宋裁减后", aliases, "南宋宗室管理机构", "别称")
    staff(w, i, parent1, initial, aliases, "绍兴府大宗正行司原置宫教二员。", "别称", quota=2)
    staff(w, i, parent2, reduced, aliases, "裁减宫教一员后留一员。", "别称", quota=1)
    alias_note(w, i, initial, aliases, "别称")
    rechain(w, eid, "连接绍兴府大宗正行司教授初置与裁减节点。")
    w.commit()


def entry223():
    i, main = 223, F[223]["text"]
    history, roster, aliases = field(i, "职源与沿革"), field(i, "编制"), field(i, "简称与别名")
    w = W(i)
    north_eid, north = state(
        w, i, "南京外宗正司", "机构", "北宋崇宁元年十一月十二日",
        "始置于南京应天府", history, "外宗正司",
        "建立南京外宗正司始置节点。", "职源与沿革",
    )
    south_eid, south = state(
        w, i, "南外宗正司", "机构", "南宋建炎三年十二月",
        "经镇江南迁，移司泉州", history, "外宗正司",
        "按南宋通行正称建立南外宗正司泉州节点。", "职源与沿革",
    )
    relation(w, i, north, south, "前后演变", aliases, "北宋南京外宗正司南迁后称南外宗正司。", "简称与别名")
    posts = (
        ("知南外宗正事", "职事官", 1),
        ("南外宗正丞", "兼官", 1),
        ("南外宗正司主簿", "兼官", 1),
        ("南外宗正司教授", "职事官", 1),
        ("南外宗正司书吏", "吏", 1),
        ("南外宗正司副书吏", "吏", 1),
        ("南外宗正司贴司", "吏", 1),
    )
    touched = {north_eid, south_eid}
    for title, officer, quota in posts:
        eid, post = state(
            w, i, title, "官职", "南宋", "南外宗正司官额之一", roster,
            "外宗正司官", f"据南外宗正司编制建立{title}。", "编制", officer=officer,
        )
        staff(w, i, south, post, roster, f"南外宗正司置{title}{quota}人。", "编制", quota=quota, staff_type=officer)
        touched.add(eid)
    warehouse_eid, warehouse = state(
        w, i, "南外宗正司亲睦仓库", "机构", "南宋",
        "南外宗正司所辖仓库", roster, "外宗正司所属机构",
        "据编制建立南外宗正司亲睦仓库。", "编制",
    )
    relation(w, i, south, warehouse, "上下级机构", roster, "亲睦仓库隶南外宗正司。", "编制")
    touched.add(warehouse_eid)
    alias_note(w, i, north, aliases, "简称与别名")
    alias_note(w, i, south, aliases, "简称与别名")
    for eid in touched:
        rechain(w, eid, "整理南京、南外宗正司及其官属时间链。")
    w.commit()


def entry224():
    i, main = 224, F[224]["text"]
    history, roster, aliases = field(i, "职源与沿革"), field(i, "编制"), field(i, "简称")
    w = W(i)
    north_eid, north = state(
        w, i, "西京外宗正司", "机构", "北宋崇宁元年十一月十二日",
        "始置于西京河南府", history, "外宗正司",
        "建立西京外宗正司始置节点。", "职源与沿革",
    )
    south_eid, lake = state(
        w, i, "西外宗正司", "机构", "南宋绍兴元年",
        "南迁后移司湖州", history, "外宗正司",
        "按南宋通行正称建立西外宗正司湖州节点。", "职源与沿革",
    )
    _, fuzhou = state(
        w, i, "西外宗正司", "机构", "南宋绍兴五年",
        "移司福州", history, "外宗正司",
        "建立西外宗正司福州节点。", "职源与沿革",
    )
    relation(w, i, north, lake, "前后演变", aliases, "北宋西京外宗正司南迁后称西外宗正司。", "简称")
    posts = (
        ("知西外宗正事", "职事官", 1),
        ("西外宗正丞", "兼官", 1),
        ("西外宗正司主簿", "兼官", 1),
        ("西外宗正司教授", "职事官", 1),
        ("西外宗正司书吏", "吏", None),
        ("西外宗正司贴司", "吏", None),
    )
    touched = {north_eid, south_eid}
    for title, officer, quota in posts:
        eid, post = state(
            w, i, title, "官职", "南宋", "西外宗正司官额之一", roster,
            "外宗正司官", f"据西外宗正司编制建立{title}。", "编制", officer=officer,
        )
        quota_text = f"，定额{quota}人" if quota is not None else ""
        staff(w, i, fuzhou, post, roster, f"西外宗正司置{title}{quota_text}。", "编制", quota=quota, staff_type=officer)
        touched.add(eid)
    warehouse_eid, warehouse = state(
        w, i, "西外宗正司亲睦仓库", "机构", "南宋",
        "西外宗正司所辖仓库", roster, "外宗正司所属机构",
        "据编制建立西外宗正司亲睦仓库。", "编制",
    )
    relation(w, i, fuzhou, warehouse, "上下级机构", roster, "亲睦仓库隶西外宗正司。", "编制")
    touched.add(warehouse_eid)
    alias_note(w, i, north, aliases, "简称")
    alias_note(w, i, fuzhou, aliases, "简称")
    for eid in touched:
        rechain(w, eid, "整理西京、西外宗正司及其官属时间链。")
    w.commit()


def entry225():
    i, main = 225, F[225]["text"]
    w = W(i)
    eid, north = state(
        w, i, "外宗正司", "机构", "北宋", "南京、西京两外宗正司通称",
        main, "机构统称", "建立北宋外宗正司统称节点。",
    )
    _, south = state(
        w, i, "外宗正司", "机构", "南宋",
        "包括南外宗正司、西外宗正司及乾道七年前的绍兴府大宗正行司",
        main, "机构统称", "建立南宋外宗正司统称节点。",
    )
    for generic, title, time in (
        (north, "南京外宗正司", "北宋崇宁元年十一月十二日"),
        (north, "西京外宗正司", "北宋崇宁元年十一月十二日"),
        (south, "南外宗正司", "南宋建炎三年十二月"),
        (south, "西外宗正司", "南宋绍兴五年"),
        (south, "绍兴府大宗正行司", "南宋绍兴二年正月十四日"),
    ):
        relation(w, i, generic, tp(w, title, "机构", time), "统称与实例", main, f"{title}为外宗正司实例。")
    rechain(w, eid, "连接外宗正司北宋、南宋统称节点。")
    w.commit()


def entry226():
    i, main, aliases = 226, F[226]["text"], field(226, "简称")
    w = W(i)
    eid, generic = state(
        w, i, "西南两外宗正司", "机构", "宋代",
        "南外宗正司与西外宗正司合称", main,
        "机构统称", "建立西南两外宗正司统称。",
    )
    relation(w, i, generic, tp(w, "南外宗正司", "机构", "南宋建炎三年十二月"), "统称与实例", main, "南外宗正司为西南两外宗正司实例。")
    relation(w, i, generic, tp(w, "西外宗正司", "机构", "南宋绍兴五年"), "统称与实例", main, "西外宗正司为西南两外宗正司实例。")
    alias_note(w, i, generic, aliases, "简称")
    rechain(w, eid, "确认西南两外宗正司统称时间链。")
    w.commit()


def entries227_230():
    specs = {
        227: ("知南外宗正事", "南外宗正司", "南宋建炎三年十二月", "南宋", "知南外宗正事隶南外宗正司。"),
        228: ("知西外宗正事", "西外宗正司", "南宋绍兴五年", "南宋", "知西外宗正事隶西外宗正司。"),
        230: ("判西外宗正事", "西外宗正司", "南宋绍兴五年", "南宋", "判西外宗正事领西外宗正司事。"),
    }
    for i, (title, parent_title, parent_time, time, decision) in specs.items():
        main = F[i]["text"]
        w = W(i)
        eid, post = state(
            w, i, title, "官职", time, main, main,
            "外宗正司长官", f"据专条建立或补足{title}。", officer="职事官",
        )
        staff(w, i, tp(w, parent_title, "机构", parent_time), post, main, decision)
        if F[i]["fields"]:
            name = next(iter(F[i]["fields"]))
            alias_note(w, i, post, field(i, name), name)
        rechain(w, eid, f"确认{title}时间链。")
        w.commit()


def entry229():
    i, main = 229, F[229]["text"]
    w = W(i)
    eid, generic = state(
        w, i, "知宗", "官职", "宋代",
        "知西外宗正事、知南外宗正事官通称", main,
        "官职统称", "建立知宗通称。",
    )
    relation(w, i, generic, tp(w, "知南外宗正事", "官职", "南宋"), "统称与实例", main, "知南外宗正事为知宗实例。")
    relation(w, i, generic, tp(w, "知西外宗正事", "官职", "南宋"), "统称与实例", main, "知西外宗正事为知宗实例。")
    rechain(w, eid, "确认知宗统称时间链。")
    w.commit()


def entry231():
    i, main, aliases = 231, F[231]["text"], field(231, "简称")
    w = W(i)
    eid, generic = state(
        w, i, "外宗正丞", "官职", "宋代",
        "西外、南外及绍兴府大宗正行司丞的通称；由所在州通判兼",
        main, "官职统称", "建立外宗正丞通称。", officer="兼官",
    )
    specs = (
        ("南外宗正丞", "南外宗正司", "南宋建炎三年十二月", "南宋"),
        ("西外宗正丞", "西外宗正司", "南宋绍兴五年", "南宋"),
        ("绍兴府大宗正行司丞", "绍兴府大宗正行司", "南宋绍兴二年正月十四日", "南宋绍兴年间"),
    )
    touched = {eid}
    for title, parent, parent_time, time in specs:
        peid, post = state(
            w, i, title, "官职", time, "协助本司知宗管理所辖宗室事，由所在州通判兼",
            main, "外宗正司属官", f"建立外宗正丞实例{title}。", officer="兼官",
        )
        relation(w, i, generic, post, "统称与实例", main, f"{title}为外宗正丞实例。")
        staff(w, i, tp(w, parent, "机构", parent_time), post, main, f"{title}隶{parent}。", quota=1, staff_type="兼官")
        touched.add(peid)
    alias_note(w, i, generic, aliases, "简称")
    for x in touched:
        rechain(w, x, "整理外宗正丞统称及实例时间链。")
    w.commit()


def entry232():
    i, main, aliases = 232, F[232]["text"], field(232, "简称")
    w = W(i)
    eid, generic = state(
        w, i, "外宗正主簿", "官职", "宋代",
        "西外、南外宗正司主簿通称；掌簿书勾考、出纳，由所在州佥判兼",
        main, "官职统称", "建立外宗正主簿通称。", officer="兼官",
    )
    touched = {eid}
    for title, parent, parent_time in (
        ("南外宗正司主簿", "南外宗正司", "南宋建炎三年十二月"),
        ("西外宗正司主簿", "西外宗正司", "南宋绍兴五年"),
    ):
        peid, post = state(
            w, i, title, "官职", "南宋",
            "掌本司簿书勾考、出纳，由所在州佥书节度判官厅公事兼",
            main, "外宗正司属官", f"建立外宗正主簿实例{title}。", officer="兼官",
        )
        relation(w, i, generic, post, "统称与实例", main, f"{title}为外宗正主簿实例。")
        staff(w, i, tp(w, parent, "机构", parent_time), post, main, f"{title}隶{parent}。", quota=1, staff_type="兼官")
        touched.add(peid)
    alias_note(w, i, generic, aliases, "简称")
    for x in touched:
        rechain(w, x, "整理外宗正主簿统称及实例时间链。")
    w.commit()


def entry233():
    i, main = 233, F[233]["text"]
    history, duty, roster = field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制")
    w = W(i)
    generic_eid, generic = state(
        w, i, "财用司", "机构", "宋代",
        "绍兴府大宗正行司、南外宗正司、西外宗正司所置财用机构通称",
        main, "机构统称", "建立财用司通称。",
    )
    specs = (
        ("南外宗正司财用司", "南外宗正司", "南宋建炎三年十二月", "北宋崇宁元年十一月十二日", "南宋建炎三年十二月"),
        ("西外宗正司财用司", "西外宗正司", "南宋绍兴元年", "北宋崇宁元年十一月十二日", "南宋绍兴元年"),
        ("绍兴府大宗正行司财用司", "绍兴府大宗正行司", "南宋绍兴二年正月十四日", "南宋绍兴元年", None),
    )
    touched = {generic_eid}
    for title, parent, parent_time, start_time, affiliate_time in specs:
        eid, start = state(
            w, i, title, "机构", start_time,
            "掌本宗正司官吏及所属宗室逐月请给钱粮与修治住房等财用事",
            history, "外宗正司财用机构", f"建立{title}始置节点。", "职源与沿革",
        )
        cite(w, "Timepoints", start, i, duty, f"补充{title}职掌。", "职掌")
        relation(w, i, generic, start, "统称与实例", main, f"{title}为财用司实例。")
        affiliate = start
        if affiliate_time and affiliate_time != start_time:
            _, affiliate = state(
                w, i, title, "机构", affiliate_time,
                f"随所隶{parent}南迁后继续运行", history,
                "外宗正司财用机构", f"建立{title}南迁后的归隶节点。", "职源与沿革",
            )
        relation(w, i, tp(w, parent, "机构", parent_time), affiliate, "上下级机构", main, f"{title}分隶{parent}。")
        touched.add(eid)
    for title in ("南外宗正司财用司", "西外宗正司财用司"):
        eid = w.find_entity(title, "机构")
        _, end = state(
            w, i, title, "机构", "南宋绍兴元年九月十九日", "罢置", history,
            "外宗正司财用机构", f"记录{title}罢置。", "职源与沿革",
        )
        touched.add(eid)
    cite(w, "Timepoints", generic, i, roster, "记录财用司所置管勾或主管、指使及军典。", "编制")
    for x in touched:
        rechain(w, x, "整理财用司统称及三司实例时间链。")
    w.commit()


def entries234_237():
    # 234 管勾宗室财用
    i, main = 234, F[234]["text"]
    w = W(i)
    eid, manager = state(
        w, i, "管勾宗室财用", "官职", "北宋",
        "统管本宗正司官吏及宗室成员请给钱米等财用事", main,
        "外宗正司财用官", "建立管勾宗室财用。", officer="职事官",
    )
    staff(w, i, tp(w, "财用司", "机构", "宋代"), manager, main, "管勾宗室财用隶外宗正司财用司。", quota=2)
    rechain(w, eid, "确认管勾宗室财用时间链。")
    w.commit()

    # 235 主管宗室财用，以及与管勾的名称演变
    i, main = 235, F[235]["text"]
    w = W(i)
    eid, manager = state(
        w, i, "主管宗室财用", "官职", "南宋",
        "由管勾宗室财用改称，专一检察帮书", main,
        "外宗正司财用官", "建立南宋主管宗室财用。", officer="职事官",
    )
    staff(w, i, tp(w, "财用司", "机构", "宋代"), manager, main, "主管宗室财用为南宋外宗正司财用司官。")
    relation(w, i, tp(w, "管勾宗室财用", "官职", "北宋"), manager, "前后演变", main, "南宋改管勾宗室财用为主管宗室财用。")
    cite(w, "Timepoints", manager, i, main, "‘主管财用’只作简称，不另建实体。", note="纯简称不另建实体")
    rechain(w, eid, "确认主管宗室财用时间链。")
    w.commit()

    # 236 指使
    i, main = 236, F[236]["text"]
    w = W(i)
    eid, messenger = state(
        w, i, "外宗正司财用司指使", "官职", "宋代",
        "承办催督、发放、检察宗室钱米等公事", main,
        "外宗正司财用官", "按所隶机构消歧建立财用司指使。", officer="职事官",
    )
    staff(w, i, tp(w, "财用司", "机构", "宋代"), messenger, main, "指使隶外宗正司财用司。", quota=2)
    rechain(w, eid, "确认外宗正司财用司指使时间链。")
    w.commit()

    # 237 军典；与既有皮剥所军典消歧
    i, main = 237, F[237]["text"]
    w = W(i)
    eid, clerk = state(
        w, i, "外宗正司财用司军典", "官职", "宋代",
        "在指使下抄转、书写财用司簿历等文书", main,
        "外宗正司财用司吏", "按所隶机构消歧，避免与皮剥所军典合并。", officer="吏",
    )
    staff(w, i, tp(w, "财用司", "机构", "宋代"), clerk, main, "军典隶外宗正司财用司。", quota=1, staff_type="吏")
    rechain(w, eid, "确认外宗正司财用司军典时间链。")
    w.commit()


def entry238():
    i, main = 238, F[238]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职能"),
        field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    generic_eid, start = state(
        w, i, "敦宗院", "机构", "北宋崇宁元年十一月十二日",
        "西京、南京各置外宗正司时分别始置", history,
        "外宗正司所属机构", "建立敦宗院始置节点。", "职源与沿革",
    )
    _, abolished = state(
        w, i, "敦宗院", "机构", "北宋大观三年三月二十三日",
        "罢置", history, "外宗正司所属机构", "记录敦宗院罢置。", "职源与沿革",
    )
    _, restored = state(
        w, i, "敦宗院", "机构", "北宋政和二年七月八日",
        "复置", history, "外宗正司所属机构", "记录敦宗院复置。", "职源与沿革",
    )
    _, south = state(
        w, i, "敦宗院", "机构", "南宋初",
        "随所隶南外、西外宗正司移往泉州、福州", history,
        "外宗正司所属机构", "记录两京敦宗院南迁。", "职源与沿革",
    )
    cite(w, "Timepoints", start, i, duty, "记录敦宗院收聚、安置与纠察贫弱宗室的职能。", "职能")
    cite(w, "Timepoints", start, i, roster, "记录敦宗院官吏与所收宗室、田房编制。", "编制")
    specific = (
        ("西京敦宗院", "西京外宗正司", "北宋崇宁元年十一月十二日"),
        ("南京敦宗院", "南京外宗正司", "北宋崇宁元年十一月十二日"),
    )
    touched = {generic_eid}
    for title, parent, time in specific:
        eid, tid = state(
            w, i, title, "机构", time, "外宗正司所属敦宗院之一", history,
            "敦宗院实例", f"据总条建立{title}实例。", "职源与沿革",
        )
        relation(w, i, start, tid, "统称与实例", main, f"{title}为敦宗院实例。")
        relation(w, i, tp(w, parent, "机构", time), tid, "上下级机构", main, f"{title}隶{parent}。")
        touched.add(eid)
    new_eid, new_name = state(
        w, i, "睦宗院", "机构", "南宋淳熙十六年二月",
        "光宗即位，敦宗院避讳改名睦宗院", aliases,
        "外宗正司所属机构", "建立敦宗院改名睦宗院节点。", "简称与别名",
    )
    relation(w, i, south, new_name, "前后演变", aliases, "淳熙十六年敦宗院改名睦宗院。", "简称与别名")
    cite(w, "Timepoints", start, i, aliases, "‘厚宗院’为南宋史家避讳改称，只作名称证据。", "简称与别名", note="史家避讳称谓不另建实体")
    touched.add(new_eid)
    for title, officer, quota in (
        ("管勾敦宗院", "职事官", 2),
        ("敦宗院教授", "职事官", 1),
        ("监敦宗院门", "职事官", 1),
        ("敦宗院吏人", "吏", 2),
        ("敦宗院监门军典", "吏", 1),
    ):
        post_eid, post = state(
            w, i, title, "官职", "宋代", "敦宗院官吏编制之一", roster,
            "敦宗院官吏", f"据敦宗院编制建立{title}。", "编制", officer=officer,
        )
        staff(w, i, start, post, roster, f"敦宗院置{title}{quota}人。", "编制", quota=quota, staff_type=officer)
        touched.add(post_eid)
    for x in touched:
        rechain(w, x, "整理敦宗院始置、罢复、南迁及改名时间链。")
    w.commit()


def entries239_240():
    specs = {
        239: ("西京敦宗院", "西外宗正司", "南宋绍兴五年", "南宋", "随西外宗正司移至福州"),
        240: ("南京敦宗院", "南外宗正司", "南宋建炎三年十二月", "南宋", "随南外宗正司移至泉州"),
    }
    for i, (title, south_parent, parent_time, south_time, south_event) in specs.items():
        main = F[i]["text"]
        field_name = next(iter(F[i]["fields"]))
        aliases = field(i, field_name)
        w = W(i)
        eid, north = state(
            w, i, title, "机构", "北宋崇宁元年十一月十二日",
            main.replace("\n", " "), main, "敦宗院实例", f"据专条补足{title}始置。",
        )
        _, south = state(
            w, i, title, "机构", south_time, south_event, aliases,
            "敦宗院实例", f"据别称与总条语境建立{title}南宋节点。", field_name,
        )
        relation(w, i, tp(w, south_parent, "机构", parent_time), south, "上下级机构", aliases, f"南宋时{title}随所隶{south_parent}南迁。", field_name)
        alias_note(w, i, north, aliases, field_name)
        alias_note(w, i, south, aliases, field_name)
        rechain(w, eid, f"连接{title}北宋始置与南宋南迁节点。")
        w.commit()


def main():
    assert [F[i]["title"] for i in range(221, 241)] == [
        "主管宗室财用", "教授", "南京外宗正司", "西京外宗正司",
        "外宗正司", "西南两外宗正司", "知南外宗正事", "知西外宗正事",
        "知宗", "判西外宗正事", "外宗正丞", "外宗正主簿", "财用司",
        "管勾宗室财用", "主管宗室财用", "指使", "军典", "敦宗院",
        "西京敦宗院", "南京敦宗院",
    ]
    entry221()
    entry222()
    entry223()
    entry224()
    entry225()
    entry226()
    entries227_230()
    entry229()
    entry231()
    entry232()
    entry233()
    entries234_237()
    entry238()
    entries239_240()


if __name__ == "__main__":
    main()
