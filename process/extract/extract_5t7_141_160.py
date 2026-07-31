#!/usr/bin/env python3
"""提取 chapter5t7 第141–160条：太医局差遣、生员杂职与宗正寺。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter
import extract_5t7_121_140 as previous


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


F = {i: load(i) for i in range(141, 161)}


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
    "秦汉": -200, "北齐": 550, "宋代": 960, "宋前期": 970,
    "北宋前期": 970, "北宋初": 960,
    "北宋景德二年": 1005, "北宋英宗朝": 1064,
    "北宋景祐三年": 1036, "北宋崇宁以后": 1102,
    "北宋嘉祐六年十月十二日": 1061.78,
    "北宋嘉祐七年八月": 1062.62,
    "北宋熙宁九年三月五日": 1076.18,
    "北宋熙宁九年五月": 1076.34,
    "北宋熙宁九年五月八日": 1076.35,
    "北宋元丰五年五月": 1082.34,
    "北宋元丰改制后": 1082.5, "北宋元丰新制": 1082.5,
    "南宋": 1127, "南宋建炎三年四月十三日": 1129.3,
    "南宋绍兴三年": 1133, "南宋绍兴五年闰二月二十七日": 1135.2,
    "南宋绍兴十年": 1140, "南宋隆兴元年": 1163,
    "南宋隆兴二年": 1164, "南宋绍兴以后": 1165,
    "南宋绍熙二年十月十四日": 1191.78,
    "南宋庆元元年九月前": 1195.68,
    "南宋庆元元年九月后": 1195.72,
    "南宋嘉泰间": 1202,
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


def medical_parent(w, i, time, event, quotation, field_name=None):
    eid = w.find_entity("太医局", "机构")
    assert eid
    tid = w.find_timepoint(eid, time)
    if tid is None:
        eid, tid = upsert_state(
            w, i, "太医局", "机构", time, event, quotation,
            "中央医学教育机构", "为当期太医局官职或生员建立同期机构节点。",
            field_name,
        )
    else:
        cite(
            w, "Timepoints", tid, i, quotation,
            "为太医局既有同期节点补充本条官职或生员证据，不覆盖原有综合事件。", field_name,
        )
    return eid, tid


def alias_note(w, i, tid, quotation, field_name="简称"):
    cite(
        w, "Timepoints", tid, i, quotation,
        f"{F[i]['title']}的简称只作名称证据，不另建实体。",
        field_name, note="纯简称、别名不另建实体",
    )


def entry141():
    i = 141
    main, history, duty, rank, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    parent_eid, parent_start = medical_parent(
        w, i, "北宋熙宁九年五月八日", "置判太医局二员", history, "职源与沿革",
    )
    _, parent_end = medical_parent(
        w, i, "北宋元丰五年五月", "改制前仍置判太医局", history, "职源与沿革",
    )
    eid, start = upsert_state(
        w, i, "判太医局", "官职", "北宋熙宁九年五月",
        "始置，二员；有提举官时为佐贰，不置提举官时为局长", history,
        "太医局差遣官", "建立判太医局始置节点。", "职源与沿革",
        officer="差遣官", grade="从七品，懂医道的朝官充",
    )
    cite(w, "Timepoints", start, i, duty, "记录判太医局与提举官的职掌分工。", "职掌")
    cite(w, "Timepoints", start, i, rank, "记录判太医局品位与充任资格。", "品位")
    _, reform = upsert_state(
        w, i, "判太医局", "官职", "北宋元丰五年五月",
        "元丰改制前仍置，此后不再以旧差遣设置", history,
        "太医局差遣官", "建立判太医局北宋制度转折节点。", "职源与沿革",
        officer="差遣官",
    )
    _, south = upsert_state(
        w, i, "判太医局", "官职", "南宋", "沿置，一员，为局长官之一", roster,
        "太医局差遣官", "建立南宋判太医局编制节点。", "编制",
        officer="差遣官", grade="从七品",
    )
    staff(w, i, parent_start, start, roster, "熙宁创置时判太医局二员。", "编制", quota=2, staff_type="差遣官")
    staff(w, i, parent_end, reform, history, "元丰五年五月改制前仍置。", "职源与沿革", staff_type="差遣官")
    staff(w, i, tp(w, "太医局", "机构", "南宋"), south, roster, "南宋判太医局一员。", "编制", quota=1, staff_type="差遣官")
    alias_note(w, i, start, aliases)
    for touched in (eid, parent_eid):
        rechain(w, touched, "整理判太医局及太医局同期时间链。")
    w.commit()


def entry142_144():
    i = 142
    main, history, duty, rank, aliases = (
        F[i]["text"], field(i, "职掌与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "简称"),
    )
    w = W(i)
    parent_eid, parent_start = medical_parent(
        w, i, "北宋熙宁九年三月五日", "始置管勾太医局", history, "职掌与沿革",
    )
    _, parent_changed = medical_parent(
        w, i, "北宋熙宁九年五月八日", "管勾改以京官充", rank, "品位",
    )
    eid, start = upsert_state(
        w, i, "管勾太医局", "官职", "北宋熙宁九年三月五日",
        "始置，以选人充，参领太医局公事", history, "太医局差遣官",
        "建立管勾太医局始置节点。", "职掌与沿革", officer="差遣官", grade="从八品",
    )
    cite(w, "Timepoints", start, i, duty, "记录管勾太医局参领局事职掌。", "职掌")
    _, changed = upsert_state(
        w, i, "管勾太医局", "官职", "北宋熙宁九年五月八日",
        "改以京官充，并成为定制", rank, "太医局差遣官",
        "建立管勾太医局充任资格变化节点。", "品位", officer="差遣官", grade="从八品",
    )
    _, south_end = upsert_state(
        w, i, "管勾太医局", "官职", "南宋", "因避高宗赵构讳改称主管太医局", history,
        "太医局差遣官", "建立管勾太医局南宋改称节点。", "职掌与沿革", officer="差遣官",
    )
    staff(w, i, parent_start, start, main, "管勾太医局为局官之一。", staff_type="差遣官")
    staff(w, i, parent_changed, changed, rank, "熙宁九年五月后以京官充管勾。", "品位", staff_type="差遣官")
    alias_note(w, i, start, aliases)
    for touched in (eid, parent_eid):
        rechain(w, touched, "整理管勾太医局及太医局同期链。")
    w.commit()

    i, main, aliases = 143, F[143]["text"], field(143, "简称")
    w = W(i)
    eid, start = upsert_state(
        w, i, "主管太医局", "官职", "南宋", "由管勾太医局避赵构讳改称", main,
        "太医局差遣官", "建立主管太医局南宋改称节点。", officer="差遣官", grade="从八品",
    )
    relationship(w, i, south_end, start, "前后演变", main, "南宋管勾太医局避讳改称主管太医局。")
    staff(w, i, tp(w, "太医局", "机构", "南宋"), start, main, "主管太医局为南宋局官。", staff_type="差遣官")
    alias_note(w, i, start, aliases)
    rechain(w, eid, "整理主管太医局时间链。")
    w.commit()

    i, main = 144, F[144]["text"]
    w = W(i)
    parent_eid, parent = medical_parent(
        w, i, "南宋绍熙二年十月十四日", "主管邓骁改称提点太医局", main,
    )
    supervisor_eid, supervisor = upsert_state(
        w, i, "主管太医局", "官职", "南宋绍熙二年十月十四日",
        "内侍邓骁因不宜称主管而改称提点", main, "太医局差遣官",
        "建立主管太医局改称前节点。", officer="差遣官",
    )
    eid, point = upsert_state(
        w, i, "提点太医局", "官职", "南宋绍熙二年十月十四日",
        "由主管太医局改称；不得干预局务，只掌行移及申请事", main,
        "太医局差遣官", "建立提点太医局始置与权限节点。", officer="差遣官",
    )
    relationship(w, i, supervisor, point, "前后演变", main, "主管太医局邓骁改称提点太医局。")
    staff(w, i, parent, point, main, "提点太医局掌局中行移及申请事。", staff_type="差遣官")
    for touched in (parent_eid, supervisor_eid, eid):
        rechain(w, touched, "整理绍熙二年主管改提点的时间链。")
    w.commit()


def entry145_146():
    i, main, aliases = 145, F[145]["text"], field(145, "简称")
    w = W(i)
    parent_eid, parent = medical_parent(
        w, i, "北宋熙宁九年五月八日", "九科教养新招习学医生", main,
    )
    student = tp(w, "太医局学生", "官职", "北宋熙宁九年五月八日")
    eid, learner = upsert_state(
        w, i, "太医局习学医生", "官职", "北宋熙宁九年五月八日",
        "新招学生；听教授讲课，并轮流往三学及在京诸军治病，岁终评为上中下三等", main,
        "太医局新生", "建立太医局习学医生的学习、实习与考核节点。", officer="生员",
    )
    relationship(w, i, student, learner, "统称与实例", main, "太医局学生中新招者称习学医生。")
    staff(w, i, parent, learner, main, "习学医生在太医局学习并轮流实习。", staff_type="生员")
    cite(w, "Timepoints", learner, i, aliases, "学生、医生、习学生、习医生、局生、生只作历史名称证据；不与下条嘉泰间经试升补的‘太医局局生’混同。", "简称", note="简称不另建实体")
    for touched in (parent_eid, eid):
        rechain(w, touched, "整理习学医生及太医局同期链。")
    w.commit()

    i, main, aliases = 146, F[146]["text"], field(146, "简称")
    w = W(i)
    parent_eid, parent = medical_parent(w, i, "南宋嘉泰间", "习医生试中者升局生", main)
    learner_eid, learner = upsert_state(
        w, i, "太医局习学医生", "官职", "南宋嘉泰间", "经试中格者升局生", main,
        "太医局新生", "建立习学医生升局生前节点。", officer="生员",
    )
    eid, student = upsert_state(
        w, i, "太医局局生", "官职", "南宋嘉泰间",
        "习医生试中格者升补，给帖，满三年附省试，可望改官", main,
        "太医局入格生员", "建立太医局局生升补与应试资格节点。", officer="生员",
    )
    relationship(w, i, learner, student, "前后演变", main, "太医局习医生试中格者升为局生。")
    staff(w, i, parent, student, main, "局生为太医局试中入格生员。", staff_type="生员")
    alias_note(w, i, student, aliases)
    for touched in (parent_eid, learner_eid, eid):
        rechain(w, touched, "整理嘉泰间习医生升局生链。")
    w.commit()


def entry147_151():
    specs = (
        (147, "太医局堂长", "掌讲堂表率，罚不遵堂规者", "太医局", 1),
        (148, "太医局斋长", "掌表率、纠察斋内学生并依斋规处罚", "太医局斋舍", 1),
        (149, "太医局斋谕", "佐斋长管理斋舍，以讲说道理为主", "太医局斋舍", 1),
        (150, "太医局司书", "掌本局医书保管、借阅", "太医局", 1),
        (151, "太医局司门", "掌局大门按时启闭", "太医局", 1),
    )
    student_eid = None
    for i, title, event, parent_title, quota in specs:
        main = F[i]["text"]
        w = W(i)
        parent_eid = entity_id(w, "太医局", "机构")
        parent = tp(w, "太医局", "机构", "南宋")
        if i == 147:
            student_eid, student = upsert_state(
                w, i, "太医局学生", "官职", "南宋",
                "大方脉科、风科学生中可挑选堂长、斋长、斋谕、司书、司门等杂职", main,
                "太医局生员", "为太医局学生入选杂职建立南宋节点。", officer="生员",
            )
        else:
            student_eid = entity_id(w, "太医局学生", "官职")
            student = tp(w, "太医局学生", "官职", "南宋")
            cite(w, "Timepoints", student, i, main, f"第{i}条证明该杂职由大方脉科、风科学生中挑选。")
        eid, post = upsert_state(
            w, i, title, "官职", "南宋", event + "；由大方脉科、风科学生挑选充任", main,
            "太医局杂职", f"建立{title}的充任、职掌和食钱节点。", officer="杂职",
            grade="每月在学生食钱外增给一贯",
        )
        if parent_title == "太医局斋舍":
            room_eid = w.find_entity("太医局斋舍", "机构")
            parent = w.find_timepoint(room_eid, "南宋") if room_eid else None
            if parent is None:
                room_eid, parent = upsert_state(
                    w, i, "太医局斋舍", "机构", "南宋", "太医局学生斋舍系统", main,
                    "太医局内部教学机构", "建立太医局斋舍作为斋长、斋谕的所属机构。",
                )
            else:
                cite(w, "Timepoints", parent, i, main, f"为太医局斋舍既有节点补充{title}证据。")
            relationship(w, i, tp(w, "太医局", "机构", "南宋"), parent, "上下级机构", main, "太医局设学生斋舍。")
        staff(w, i, parent, post, main, f"{title}为所属杂职。", quota=quota, staff_type="杂职")
        for touched in (eid, student_eid, parent_eid):
            rechain(w, touched, f"整理{title}及相关学生、机构时间链。")
        w.commit()

    i, main = 148, F[148]["text"]
    w = W(i)
    generic_eid = entity_id(w, "太医局斋舍", "机构")
    generic = tp(w, "太医局斋舍", "机构", "南宋")
    for title in ("守一斋", "全冲斋", "精微斋", "立本斋", "慈幼斋", "致用斋", "深明斋", "稽疾斋"):
        eid, child = upsert_state(
            w, i, f"太医局{title}", "机构", "南宋", "太医局八斋之一", main,
            "太医局学生斋舍", f"建立原文明举的{title}。",
        )
        relationship(w, i, generic, child, "统称与实例", main, f"太医局八斋包括{title}。")
        rechain(w, eid, f"确认{title}南宋节点。")
    rechain(w, generic_eid, "确认太医局斋舍时间链。")
    w.commit()


def entry152_156():
    i, main, aliases = 152, F[152]["text"], field(152, "简称")
    w = W(i)
    parent_eid, parent_before = medical_parent(w, i, "南宋庆元元年九月前", "局生附贡院试三场合格者称广场人", main)
    _, parent_after = medical_parent(w, i, "南宋庆元元年九月后", "医人奏试三场及格也称广场人", main)
    student_eid, student = upsert_state(
        w, i, "太医局学生", "官职", "南宋庆元元年九月前", "赴贡院试三场合格可出为医官", main,
        "太医局生员", "建立太医局生应试出官节点。", officer="生员",
    )
    eid, before = upsert_state(
        w, i, "广场人", "官职", "南宋庆元元年九月前",
        "太医局生试三场合格所得出官资格，可补本局试官", main, "医官出身资格",
        "建立庆元元年九月前广场人资格。", officer="医官出身资格",
    )
    medical_eid, doctor = upsert_state(
        w, i, "医人", "官职", "南宋庆元元年九月后", "奏试赴三场及格者也可称广场人", main,
        "民间业医人员类别", "四表无人员类型，以官职类承载原文明确的医人类别，不视为正式官职。", officer="民间业医人员",
    )
    _, after = upsert_state(
        w, i, "广场人", "官职", "南宋庆元元年九月后", "医人奏试三场及格者也称广场人", main,
        "医官出身资格", "建立庆元元年九月后广场人范围扩大节点。", officer="医官出身资格",
    )
    relationship(w, i, student, before, "前后演变", main, "太医局生试三场合格后成为广场人。")
    relationship(w, i, doctor, after, "前后演变", main, "庆元元年九月后医人试三场及格也成为广场人。")
    alias_note(w, i, before, aliases)
    for touched in (parent_eid, student_eid, medical_eid, eid):
        rechain(w, touched, "整理广场人资格变化及相关人员时间链。")
    w.commit()

    specs = (
        (153, "太医局上等学生", "年终考核入上等，月给十五贯", 20),
        (154, "太医局中等学生", "年终考核入中等，月给十贯", 30),
        (155, "太医局下等学生", "年终考核入下等，月给五贯", 50),
    )
    for i, title, event, quota in specs:
        main = F[i]["text"]
        w = W(i)
        parent = tp(w, "太医局", "机构", "北宋熙宁九年五月八日")
        generic = tp(w, "太医局学生", "官职", "北宋熙宁九年五月八日")
        eid, child = upsert_state(
            w, i, title, "官职", "北宋熙宁九年五月八日", event, main,
            "太医局入等生员", f"建立{title}的考核等第、月给和限额。", officer="生员",
        )
        relationship(w, i, generic, child, "统称与实例", main, f"太医局入等学生包括{title}。")
        staff(w, i, parent, child, main, f"{title}限额{quota}人。", quota=quota, staff_type="生员")
        rechain(w, eid, f"确认{title}时间链。")
        w.commit()

    i, main = 156, F[156]["text"]
    w = W(i)
    eid, generic = upsert_state(
        w, i, "医人", "官职", "宋代", "民间业医、无学历无仕历者；年十五可投状报考太医局学生，也可由门荫、荐举入仕", main,
        "民间业医人员类别", "四表无人员类型，以官职类承载原文明确的医人类别，不视为正式官职。", officer="民间业医人员",
    )
    student = tp(w, "太医局学生", "官职", "北宋熙宁九年五月八日")
    relationship(w, i, generic, student, "前后演变", main, "医人年十五可投状报考，试补后进入太医局学生序列。")
    rechain(w, eid, "整理医人宋代人员类别时间链。")
    w.commit()


def entry157():
    i = 157
    main, history, duty, rank, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"), field(i, "简称与别名"),
    )
    w = W(i)
    eid, origin = upsert_state(
        w, i, "宗正寺", "机构", "北齐", "始设宗正寺", history, "宗室管理机构",
        "建立宗正寺北齐始设节点；秦汉‘宗正’为古官源流，不写成宗正寺时间点。", "职源与沿革",
    )
    _, early = upsert_state(
        w, i, "宗正寺", "机构", "宋前期", "两宋沿置；掌宗室名籍、牒谱图籍、赐名定名及陵庙荐享等事", duty,
        "中央宗室管理机构", "细化宗正寺宋前期职掌与编制节点。", "职掌",
    )
    _, reform = upsert_state(
        w, i, "宗正寺", "机构", "北宋元丰新制", "元丰新制定职事官与两案，辖玉牒所", roster,
        "中央宗室管理机构", "细化宗正寺元丰新制编制节点。", "编制",
    )
    _, reduced = upsert_state(
        w, i, "宗正寺", "机构", "北宋景祐三年",
        "大宗正司建立后，宗正寺不再直接管理皇族宗室，职能减弱为主管玉牒、属籍等事", duty,
        "中央宗室管理机构", "建立大宗正司设置后宗正寺职能减弱节点。", "职掌",
    )
    _, schools = upsert_state(
        w, i, "宗正寺", "机构", "北宋崇宁以后", "提举诸王宫大小学", duty,
        "中央宗室管理机构", "建立徽宗崇宁后新增提举诸王宫学职掌节点。", "职掌",
    )
    _, south = upsert_state(
        w, i, "宗正寺", "机构", "南宋", "编制无常，经建炎并省、绍兴复置及隆兴省复", roster,
        "中央宗室管理机构", "细化宗正寺南宋编制概况。", "编制",
    )
    _, merged = upsert_state(
        w, i, "宗正寺", "机构", "南宋建炎三年四月十三日", "并入太常寺", history,
        "中央宗室管理机构", "建立建炎三年并入太常寺节点。", "职源与沿革",
    )
    _, restored = upsert_state(
        w, i, "宗正寺", "机构", "南宋绍兴五年闰二月二十七日", "复置宗正寺", history,
        "中央宗室管理机构", "建立绍兴五年复置节点。", "职源与沿革",
    )
    _, later = upsert_state(
        w, i, "宗正寺", "机构", "南宋绍兴以后", "复置后管理玉牒、属籍等事，官吏编制陆续恢复", roster,
        "中央宗室管理机构", "细化宗正寺绍兴以后编制节点。", "编制",
    )
    cite(w, "Timepoints", early, i, rank, "记录宗正寺在九寺中序位及长贰品位。", "品位")
    cite(w, "Timepoints", early, i, aliases, "宗寺、宗正、司宗、麟寺只作简称、拟古名与雅称证据。", "简称与别名", note="纯简称、别名不另建实体")
    relationship(w, i, merged, tp(w, "太常寺", "机构", "南宋建炎三年四月"), "前后演变", history, "建炎三年宗正寺并入太常寺。", "职源与沿革")
    relationship(w, i, tp(w, "太常寺", "机构", "南宋建炎三年四月"), restored, "前后演变", history, "绍兴五年宗正寺从并入状态复置。", "职源与沿革")

    touched = {eid}

    def post(title, time, event, parent, quota=None, staff_type="官", type_="官职"):
        peid = w.find_entity(title, type_)
        ptid = w.find_timepoint(peid, time) if peid else None
        if ptid is None:
            peid, ptid = upsert_state(
                w, i, title, type_, time, event, roster,
                "宗正寺所属机构" if type_ == "机构" else "宗正寺官吏",
                f"据宗正寺编制建立{title}{time}节点。", "编制",
                officer=None if type_ == "机构" else staff_type,
            )
        else:
            cite(
                w, "Timepoints", ptid, i, roster,
                f"为{title}{time}既有节点补充宗正寺编制证据，不覆盖专条事件。", "编制",
            )
        if type_ == "机构":
            relationship(w, i, parent, ptid, "上下级机构", roster, f"{title}隶宗正寺。", "编制")
        else:
            staff(w, i, parent, ptid, roster, f"{title}隶宗正寺。", "编制", quota=quota, staff_type=staff_type)
        touched.add(peid)
        return peid, ptid

    # 宋前期官属、庙陵差役与吏额。
    for title, event, quota, staff_type in (
        ("判宗正寺事", "领寺事，与同判合计一或二员", None, "差遣官"),
        ("同判宗正寺事", "与判寺事合计一或二员", None, "差遣官"),
        ("知宗正丞事", "判寺阙时补领寺事", None, "差遣官"),
        ("宗正寺主簿", "主簿一员", 1, "职事官"),
        ("宗正寺兼卿官", "或置兼卿官", None, "兼差官"),
        ("宗正寺室长", "无定数", None, "杂职"), ("宗正寺斋郎", "无定数", None, "杂职"),
        ("太庙宫闱令", "一人", 1, "庙官"), ("后庙宫闱令", "一人", 1, "庙官"),
        ("奉慈庙宫闱令", "一人", 1, "庙官"), ("宗正寺修玉牒官", "多为兼差，无定员", None, "兼差官"),
        ("宗正寺陵台令", "永安知县兼", None, "兼差官"), ("宗正寺诸陵副使", "无定员", None, "陵官"),
        ("宗正寺诸陵都监", "无定员", None, "陵官"), ("宗正寺楷书", "四人", 4, "吏"),
        ("宗正寺府吏", "二人", 2, "吏"), ("宗正寺驱使官", "九人", 9, "吏"),
        ("宗正寺庙直官", "一人", 1, "吏"),
    ):
        post(title, "宋前期", event, early, quota, staff_type)
    _, jade_early = post("宗正寺玉牒所", "宋前期", "修玉牒所", early, type_="机构")
    for title, event, quota in (("宗正寺玉牒所典", "三人", 3), ("宗正寺玉牒所楷书", "四人", 4)):
        post(title, "宋前期", event, jade_early, quota, "吏")

    # 元丰新制。
    for title, post_time, event, quota in (
        ("宗正寺卿", "北宋元丰新制", "一人", 1),
        ("宗正寺少卿", "北宋元丰五年新制", "一人", 1),
        ("宗正寺丞", "北宋元丰新制", "一人", 1),
        ("宗正寺主簿", "北宋元丰新制", "一人", 1),
        ("太庙令", "北宋元丰改制后", "由太常寺归隶宗正寺", 1),
        ("宗正寺胥长", "北宋元丰新制", "一人", 1),
        ("宗正寺胥史", "北宋元丰新制", "一人", 1),
        ("宗正寺胥佐", "北宋元丰新制", "二人", 2),
        ("宗正寺楷书", "北宋元丰新制", "一人", 1),
        ("宗正寺贴书", "北宋元丰新制", "一人", 1),
    ):
        post(title, post_time, event, reform, quota, "职事官" if title in {"宗正寺卿", "宗正寺少卿", "宗正寺丞", "宗正寺主簿", "太庙令"} else "吏")
    _, jade_reform = post("宗正寺玉牒所", "北宋元丰新制", "宗正寺所辖玉牒所", reform, type_="机构")
    post("宗正寺属籍案", "北宋元丰新制", "分案之一", reform, type_="机构")
    post("宗正寺知籍案", "北宋元丰新制", "分案之一", reform, type_="机构")
    assert jade_reform

    # 南宋绍兴以后稳定见载的官吏额。
    for title, event, quota, staff_type in (
        ("宗正寺少卿", "绍兴三年置一员", 1, "职事官"),
        ("宗正寺丞", "绍兴五年复寺后增置一员", 1, "职事官"),
        ("宗正寺主簿", "绍兴十年增置，隆兴元年省、二年复置", 1, "职事官"),
        ("宗正寺胥长", "一人", 1, "吏"), ("宗正寺胥史", "一人", 1, "吏"),
        ("宗正寺胥佐", "二人", 2, "吏"), ("宗正寺贴书", "二人", 2, "吏"),
        ("宗正寺楷书", "二人", 2, "吏"),
    ):
        post(title, "南宋绍兴以后", event, later, quota, staff_type)

    for touched_eid in touched:
        rechain(w, touched_eid, "整理宗正寺及所属官司官吏的全局时间链。")
    assert origin and reduced and schools and south
    w.commit()


def entry158_160():
    i = 158
    main, history, duty, rank, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位"),
        field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    eid = entity_id(w, "判宗正寺事", "官职")
    start = tp(w, "判宗正寺事", "官职", "宋前期")
    upsert_state(
        w, i, "判宗正寺事", "官职", "宋前期",
        "北宋始置，领宗正寺事，掌陵庙荐享及皇族籍；一人或二人", history,
        "宗正寺差遣官", "据专条细化判宗正寺事始置、职掌与编制。", "职源与沿革",
        officer="差遣官", grade="以国姓两制以上文官充",
    )
    cite(w, "Timepoints", start, i, duty, "记录判宗正寺事职掌。", "职掌")
    cite(w, "Timepoints", start, i, rank, "记录判宗正寺事充任资格。", "品位")
    _, end = upsert_state(
        w, i, "判宗正寺事", "官职", "北宋元丰改制后", "元丰改制正名，不复设", history,
        "宗正寺差遣官", "建立判宗正寺事元丰不复设节点。", "职源与沿革", officer="差遣官",
    )
    cite(w, "Timepoints", start, i, roster, "记录判宗正寺事一人或二人。", "编制")
    alias_note(w, i, start, aliases)
    rechain(w, eid, "整理判宗正寺事始置与元丰罢置链。")
    assert end
    w.commit()

    i, main = 159, F[159]["text"]
    w = W(i)
    eid = entity_id(w, "同判宗正寺事", "官职")
    _, start = upsert_state(
        w, i, "同判宗正寺事", "官职", "北宋景德二年",
        "始置，以朝官充，位次于正判寺官，赐三品紫服", main, "宗正寺差遣官",
        "建立同判宗正寺事始置、充任与序位节点。", officer="差遣官", grade="赐三品紫服",
    )
    parent_eid, parent = upsert_state(
        w, i, "宗正寺", "机构", "北宋景德二年", "始置同判宗正寺事", main,
        "中央宗室管理机构", "为同判宗正寺事建立同期机构节点。",
    )
    staff(w, i, parent, start, main, "同判宗正寺事位次于正判寺官。", staff_type="差遣官")
    for touched in (eid, parent_eid):
        rechain(w, touched, "整理同判宗正寺事及宗正寺同期链。")
    w.commit()

    i = 160
    main, history, duty, roster, aliases = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制"), field(i, "简称"),
    )
    w = W(i)
    eid, early = upsert_state(
        w, i, "知宗正寺事", "官职", "北宋前期", "曾设权知、知宗正寺官，为行礼官一员", history,
        "宗正寺差遣官", "建立知宗正寺事北宋前期节点。", "职源与沿革", officer="差遣官",
    )
    _, appointed = upsert_state(
        w, i, "知宗正寺事", "官职", "北宋嘉祐六年十月十二日",
        "始以宗室子秦州防御使赵宗实为之，管勾本司公事", history, "宗正寺差遣官",
        "建立赵宗实知宗正寺节点。", "职源与沿革", officer="差遣官",
    )
    cite(w, "Timepoints", appointed, i, duty, "记录知宗正寺管勾本司公事。", "职掌")
    _, stopped = upsert_state(
        w, i, "知宗正寺事", "官职", "北宋嘉祐七年八月", "赵宗实许罢宗正，后无继者", aliases,
        "宗正寺差遣官", "建立赵宗实罢宗正及无继者节点。", "简称", officer="差遣官",
    )
    _, reform = upsert_state(
        w, i, "知宗正寺事", "官职", "北宋元丰新制", "新制定员一人", roster,
        "宗正寺差遣官", "建立元丰新制定员节点。", "编制", officer="差遣官",
    )
    for time, post, quotation, field_name, quota in (
        ("北宋前期", early, roster, "编制", 1),
        ("北宋嘉祐六年十月十二日", appointed, duty, "职掌", None),
        ("北宋元丰新制", reform, roster, "编制", 1),
    ):
        parent_time = "宋前期" if time == "北宋前期" else time
        parent_eid = entity_id(w, "宗正寺", "机构")
        parent = w.find_timepoint(parent_eid, parent_time)
        if parent is None:
            _, parent = upsert_state(
                w, i, "宗正寺", "机构", parent_time, "置知宗正寺事领寺事", quotation,
                "中央宗室管理机构", "为知宗正寺事建立同期机构节点。", field_name,
            )
        else:
            cite(w, "Timepoints", parent, i, quotation, "为宗正寺既有同期节点补充知寺事证据，不覆盖寺级综合事件。", field_name)
        staff(w, i, parent, post, quotation, "知宗正寺事领宗正寺公事。", field_name, quota=quota, staff_type="差遣官")
        rechain(w, parent_eid, "补入知宗正寺事同期机构节点。")
    cite(w, "Timepoints", appointed, i, aliases, "知寺事、宗正只作简称证据。", "简称", note="简称不另建实体")
    rechain(w, eid, "整理知宗正寺事北宋前期、嘉祐及元丰节点。")
    assert stopped
    w.commit()


def main():
    assert [F[i]["title"] for i in range(141, 161)] == [
        "判太医局", "管勾太医局", "主管太医局", "提点太医局", "太医局习学医生",
        "太医局局生", "太医局堂长", "太医局斋长", "太医局斋谕", "太医局司书",
        "太医局司门", "广场人", "太医局上等学生", "太医局中等学生", "太医局下等学生",
        "医人", "宗正寺", "判宗正寺事", "同判宗正寺事", "知宗正寺事",
    ]
    entry141()
    entry142_144()
    entry145_146()
    entry147_151()
    entry152_156()
    entry157()
    entry158_160()


if __name__ == "__main__":
    main()
