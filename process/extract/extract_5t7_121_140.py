#!/usr/bin/env python3
"""提取 chapter5t7 第121–140条：大晟府吏案、伶人伶官与太医局。"""

import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter
import extract_5t7_101_120 as previous


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


F = {i: load(i) for i in range(121, 141)}


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
    "秦汉": -200, "北齐": 550, "宋初": 960, "北宋初": 960,
    "北宋淳化三年五月": 992.4, "北宋英宗朝": 1064,
    "北宋熙宁四年四月二十一日": 1071.31,
    "北宋熙宁八年十二月": 1075.95,
    "北宋熙宁九年五月八日": 1076.35,
    "北宋熙宁九年八月二十五日": 1076.65,
    "北宋元丰改制后": 1082, "北宋元丰新制": 1082, "北宋元丰五年": 1082.5,
    "北宋政和初": 1111, "北宋政和元年八月十八日": 1111.65,
    "北宋政和间": 1112, "南宋": 1127,
    "南宋乾道八年正月二日": 1172.01,
    "南宋隆兴元年": 1163, "南宋隆兴元年八月十四日": 1163.62,
    "南宋绍熙二年七月十九日": 1191.55,
    "南宋理宗朝": 1224,
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


def entry121_122():
    specs = (
        (121, "大晟府胥佐", "大晟府文书吏，位次于胥史、高于贴书"),
        (122, "大晟府贴书", "大晟府文书吏，位次于胥佐，主掌抄写文字"),
    )
    for i, title, event in specs:
        main = F[i]["text"]
        w = W(i)
        eid, tid = upsert_state(
            w, i, title, "官职", "北宋崇宁四年八月二十六日", event,
            main, "大晟府文书吏", f"据{F[i]['title']}专条细化职掌与序位。",
            officer="书吏",
        )
        staff(
            w, i,
            tp(w, "大晟府", "机构", "北宋崇宁四年八月二十六日"), tid,
            main, f"{title}为大晟府文书吏。", staff_type="书吏",
        )
        rechain(w, eid, f"确认{title}时间链。")
        w.commit()


def entry123_128():
    specs = (
        (123, "大晟府大乐案", "干办太常乐（雅乐）应奉事"),
        (124, "大晟府鼓吹案", "干办仪仗导引等所用鼓吹乐事"),
        (125, "大晟府宴乐案", "干办应奉岁时宴享所需乐事"),
        (126, "大晟府法物案", "干办应奉太乐所需服色、仪仗事"),
        (127, "大晟府知杂案", "干办大晟府杂事"),
        (128, "大晟府掌法案", "掌大晟府法令条制事"),
    )
    for i, title, event in specs:
        main = F[i]["text"]
        w = W(i)
        eid, tid = upsert_state(
            w, i, title, "机构", "北宋崇宁四年八月二十六日", event,
            main, "大晟府所属案", f"据{F[i]['title']}专条细化职掌。",
        )
        relationship(
            w, i,
            tp(w, "大晟府", "机构", "北宋崇宁四年八月二十六日"), tid,
            "上下级机构", main, f"{F[i]['title']}为大晟府案名。",
        )
        rechain(w, eid, f"确认{title}时间链。")
        w.commit()


def entry129():
    i, main = 129, F[129]["text"]
    w = W(i)
    eid, tid = upsert_state(
        w, i, "提举大晟府所", "机构", "北宋崇宁四年八月二十六日",
        "由内侍省宦官充，监领大晟府，奏禀可专达于上", main,
        "大晟府监领官司", "据专条补全提举大晟府所的充任、职掌与奏禀权。",
    )
    relationship(
        w, i, tid,
        tp(w, "大晟府", "机构", "北宋崇宁四年八月二十六日"),
        "上下级机构", main, "提举大晟府所监领大晟府，方向为监领所至被监领府。",
    )
    rechain(w, eid, "确认提举大晟府所时间链。")
    w.commit()


def entry130_132():
    i, main = 130, F[130]["text"]
    w = W(i)
    eid, generic = upsert_state(
        w, i, "伶人", "官职", "宋代", "以乐舞演剧为业的技艺人通称", main,
        "技艺人通称", "四表无人员类型，以官职类承载原文明确的技艺人通称，不视为正式职事官。",
        officer="乐舞技艺人通称",
    )
    for title in ("乐官", "乐人", "舞人"):
        child_eid, child = upsert_state(
            w, i, title, "官职", "宋代", f"可泛称伶人的{title}类别", main,
            "乐舞人员类别", f"仅建立原文明举的{title}类别。",
            officer="乐舞人员类别",
        )
        relationship(w, i, generic, child, "统称与实例", main,
                     f"原文明确{title}都可泛称伶人。")
        rechain(w, child_eid, f"确认{title}宋代类别节点。")
    rechain(w, eid, "确认伶人宋代通称节点。")
    w.commit()

    i, main = 131, F[131]["text"]
    w = W(i)
    eid, generic = upsert_state(
        w, i, "伶官", "官职", "宋代", "乐官、乐人皆可通称伶官", main,
        "乐舞人员通称", "建立原文明确的伶官通称，不将其扩大为单一正式官职。",
        officer="乐舞人员通称",
    )
    for title in ("乐官", "乐人"):
        relationship(
            w, i, generic, tp(w, title, "官职", "宋代"),
            "统称与实例", main, f"原文明确{title}可通称伶官。",
        )
    cite(w, "Timepoints", generic, i, main,
         "‘俳优’仅作伶人的同义名证据，不另建实体。",
         note="纯同义名不另建实体")
    rechain(w, eid, "确认伶官宋代通称节点。")
    w.commit()

    assert F[132]["fields"].get("_placeholder") is True and not F[132]["text"]


def entry133():
    i = 133
    main = F[i]["text"]
    history, duty, roster, aliases = (
        field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制"),
        field(i, "简称与别名"),
    )
    w = W(i)
    touched = set()
    eid, song_start = upsert_state(
        w, i, "太医局", "机构", "宋初", "沿置，隶太常寺", main,
        "中央医学教育机构", "建立太医局宋初隶属节点。", officer=None,
    )
    touched.add(eid)
    _, named = upsert_state(
        w, i, "太医局", "机构", "北宋淳化三年五月", "太医局之名始见", history,
        "中央医学教育机构", "记录太医局名称首见时点。", "职源与沿革",
    )
    _, independent = upsert_state(
        w, i, "太医局", "机构", "北宋熙宁九年五月八日",
        "置提举官，不再隶太常寺，以教养学生、试选医官为主", main,
        "中央医学教育机构", "记录熙宁九年提举与脱离太常寺的状态。",
    )
    cite(w, "Timepoints", independent, i, duty, "记录太医局的教学、试选和派医职掌边界。", "职掌")
    _, reform = upsert_state(
        w, i, "太医局", "机构", "北宋元丰改制后", "改隶太常寺、礼部", main,
        "中央医学教育机构", "建立元丰新制隶属变化节点。",
    )
    _, abolished = upsert_state(
        w, i, "太医局", "机构", "南宋乾道八年正月二日", "罢局", history,
        "中央医学教育机构", "建立乾道八年罢局节点。", "职源与沿革",
    )
    _, restored = upsert_state(
        w, i, "太医局", "机构", "南宋绍熙二年七月十九日", "复置", history,
        "中央医学教育机构", "建立绍熙二年复置节点。", "职源与沿革",
    )
    cite(w, "Timepoints", named, i, aliases,
         "医局、医学只作太医局简称或俗称证据；不与崇宁间国子监医学混同。",
         "简称与别名", note="纯简称、别名不另建实体")

    taichang_song = tp(w, "太常寺", "机构", "宋初")
    relationship(w, i, taichang_song, song_start, "上下级机构", main,
                 "宋初太医局隶太常寺。")
    relationship(
        w, i, tp(w, "太常寺", "机构", "北宋元丰改制后"), reform,
        "上下级机构", main, "元丰新制太医局改隶太常寺。",
    )
    relationship(
        w, i, tp(w, "礼部", "机构", "北宋元丰新制"), reform,
        "上下级机构", main, "原文并列记载元丰新制太医局改隶礼部。",
    )

    student_eid = None
    student_nodes = {}
    for time, event, quota in (
        ("北宋熙宁九年五月八日", "九科医学生以三百人为额", 300),
        ("南宋隆兴元年", "九科学生编制合计二百九十人", 290),
        ("南宋隆兴元年八月十四日", "九科编制名额各减半，大方脉科以实有三十四人为额", None),
        ("南宋绍熙二年七月十九日", "复置后生员定以一百人为额", 100),
        ("南宋理宗朝", "生员二百五十人", 250),
    ):
        student_eid, student = upsert_state(
            w, i, "太医局学生", "官职", time, event, roster,
            "太医局生员", "记录太医局学生合计编制变化。", "编制",
            officer="生员",
            note=("该数字为九科合计" if quota else "各科减额事件，未伪造新合计数"),
        )
        student_nodes[time] = student
        parent_event = (
            "九科编制名额各减半"
            if time == "南宋隆兴元年八月十四日" else event
        )
        parent = independent if time.startswith("北宋") else (
            restored if time == "南宋绍熙二年七月十九日"
            else upsert_state(
                w, i, "太医局", "机构", time,
                parent_event, roster, "中央医学教育机构",
                "为当期学生编制建立太医局同期节点。", "编制",
            )[1]
        )
        staff(w, i, parent, student, roster, f"太医局当期学生编制{quota or '见事件说明'}。",
              "编制", quota=quota, staff_type="生员")

    course_specs = (
        ("大方脉科", 120, 34), ("风科", 80, 47), ("小方脉科", 20, 6),
        ("眼科", 20, 5), ("疮肿兼伤折科", 10, 1), ("产科", 10, 1),
        ("口齿兼咽喉科", 10, 3), ("针灸科", 10, 0), ("金镞兼书禁科", 10, 10),
    )
    course_parent = upsert_state(
        w, i, "太医局", "机构", "南宋隆兴元年",
        "九科学生编制合计二百九十人", roster,
        "中央医学教育机构", "记录隆兴元年九科编制。", "编制",
    )[1]
    reduced_parent = upsert_state(
        w, i, "太医局", "机构", "南宋隆兴元年八月十四日",
        "九科编制名额各减半", roster, "中央医学教育机构",
        "记录隆兴元年八月各科减额。", "编制",
    )[1]
    for course, quota, actual in course_specs:
        ceid, ctp = upsert_state(
            w, i, course, "机构", "南宋隆兴元年",
            f"太医局医学九科之一，学生额{quota}人，实有{actual}人", roster,
            "太医局医学科", f"建立{course}及隆兴元年额数。", "编制",
        )
        _, reduced = upsert_state(
            w, i, course, "机构", "南宋隆兴元年八月十四日",
            ("以实有三十四人为额" if course == "大方脉科" else "编制名额减半"),
            roster, "太医局医学科", f"记录{course}减额。", "编制",
        )
        relationship(w, i, course_parent, ctp, "上下级机构", roster,
                     f"太医局学生分为九科，{course}为其一。", "编制")
        relationship(w, i, reduced_parent, reduced, "上下级机构", roster,
                     f"隆兴元年八月{course}仍属太医局。", "编制")
        seid, stp = upsert_state(
            w, i, f"{course}学生", "官职", "南宋隆兴元年",
            f"编制{quota}人，实有{actual}人", roster, "太医局生员",
            f"建立{course}学生的明确编制与实有数。", "编制", officer="生员",
            note="staff_quota只保存编制额，实有数保存在事件文本",
        )
        _, sr = upsert_state(
            w, i, f"{course}学生", "官职", "南宋隆兴元年八月十四日",
            ("以实有三十四人为额" if course == "大方脉科" else "编制名额减半"),
            roster, "太医局生员", f"记录{course}学生减额。", "编制", officer="生员",
        )
        staff(w, i, ctp, stp, roster, f"{course}学生编制{quota}人。", "编制",
              quota=quota, staff_type="生员")
        reduced_quota = 34 if course == "大方脉科" else quota // 2
        staff(w, i, reduced, sr, roster, f"{course}减额后编制。", "编制",
              quota=reduced_quota, staff_type="生员")
        touched.update((ceid, seid))

    clerk_eid, clerk = upsert_state(
        w, i, "太医局吏", "官职", "南宋绍熙二年七月十九日",
        "吏额四人，有前行、手分", roster, "太医局吏属", "记录复置后吏额。", "编制",
        officer="吏属",
    )
    staff(w, i, restored, clerk, roster, "绍熙二年太医局吏额四人。", "编制",
          quota=4, staff_type="吏")
    touched.update((student_eid, clerk_eid))
    for touched_eid in touched:
        rechain(w, touched_eid, "整理太医局、九科、生员与吏额的完整时间链。")
    assert abolished
    w.commit()


def entry134_137():
    # 太医局令
    i = 134
    main, history, duty, rank = F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位")
    w = W(i)
    upsert_state(
        w, i, "太医局", "机构", "北宋政和间",
        "局令始见置", history, "中央医学教育机构",
        "为太医局令建立同期机构节点。", "职源与沿革",
    )
    eid, tid = upsert_state(
        w, i, "太医局令", "官职", "北宋政和间", "始见置，为太医局长官，领局事", history,
        "太医局局官", "建立太医局令政和间节点。", "职源与沿革", officer="职事官",
        grade="位于大晟府乐令之下、宗正丞之上（约从七品序位）",
    )
    cite(w, "Timepoints", tid, i, duty, "记录太医局令职掌。", "职掌")
    cite(w, "Timepoints", tid, i, rank, "记录太医局令序位。", "品位")
    cite(w, "Timepoints", tid, i, field(i, "简称"), "太医令只作简称证据。", "简称", note="简称不另建实体")
    staff(w, i, tp(w, "太医局", "机构", "北宋政和间"), tid, duty,
          "太医局令为局长官。", "职掌", staff_type="局官")
    rechain(w, eid, "整理太医局令时间链。")
    w.commit()

    # 太医局正
    i, main = 135, F[135]["text"]
    w = W(i)
    upsert_state(
        w, i, "太医局", "机构", "北宋英宗朝",
        "局正已见置", main, "中央医学教育机构",
        "为太医局正建立同期机构节点。",
    )
    eid, tid = upsert_state(
        w, i, "太医局正", "官职", "北宋英宗朝", "已见置，为局令佐贰，参掌本局事", main,
        "太医局局官", "建立太医局正英宗朝节点。", officer="职事官",
        grade="序位在太史局正（正八品）之下",
    )
    _, end = upsert_state(
        w, i, "太医局正", "官职", "南宋", "罢置", main,
        "太医局局官", "建立太医局正南宋罢置节点。", officer="职事官",
    )
    cite(w, "Timepoints", tid, i, field(i, "简称"), "太医正只作简称证据。", "简称", note="简称不另建实体")
    staff(w, i, tp(w, "太医局", "机构", "北宋英宗朝"), tid, main,
          "太医局正为局官之一。", staff_type="局官")
    rechain(w, eid, "整理太医局正始见与罢置链。")
    assert end
    w.commit()

    # 太医局丞
    i = 136
    main, history, duty, rank = F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"), field(i, "品位")
    w = W(i)
    for parent_time, parent_event, quotation, field_name in (
        ("北宋熙宁四年四月二十一日", "始置太医局丞", history, "职源与沿革"),
        ("北宋政和初", "太医局丞视监丞", rank, "品位"),
        ("南宋", "仍置局官", duty, "职掌"),
    ):
        upsert_state(
            w, i, "太医局", "机构", parent_time, parent_event, quotation,
            "中央医学教育机构", "为太医局丞编制建立同期机构节点。", field_name,
        )
    eid, start = upsert_state(
        w, i, "太医局丞", "官职", "北宋熙宁四年四月二十一日", "始置，无令时以丞领局事", history,
        "太医局局官", "建立太医局丞始置节点。", "职源与沿革", officer="职事官",
        grade="请给、佩鱼视尚药奉御（从七品）",
    )
    cite(w, "Timepoints", start, i, duty, "记录无令时丞领局事。", "职掌")
    _, reform = upsert_state(
        w, i, "太医局丞", "官职", "北宋政和初", "视监丞，位于都水监丞之下", rank,
        "太医局局官", "建立政和初序位节点。", "品位", officer="职事官", grade="从八品",
    )
    _, south = upsert_state(
        w, i, "太医局丞", "官职", "南宋", "仍置；以选人充，局长为判太医局或主管医官局", duty,
        "太医局局官", "建立南宋延续与充任节点。", "职掌", officer="职事官", grade="正九品",
    )
    cite(w, "Timepoints", south, i, field(i, "简称"), "太医丞、丞只作简称证据。", "简称", note="简称不另建实体")
    for parent_time, child in (("北宋熙宁四年四月二十一日", start), ("北宋政和初", reform), ("南宋", south)):
        staff(w, i, tp(w, "太医局", "机构", parent_time), child, duty,
              "太医局丞为局官之一。", "职掌", staff_type="局官")
    rechain(w, eid, "整理太医局丞始置、政和及南宋时间链。")
    w.commit()

    # 知太医局丞公事
    i, main = 137, F[137]["text"]
    w = W(i)
    upsert_state(
        w, i, "太医局", "机构", "北宋熙宁九年八月二十五日",
        "置选人充任的知太医局丞公事", main, "中央医学教育机构",
        "为知太医局丞公事建立同期机构节点。",
    )
    eid, tid = upsert_state(
        w, i, "知太医局丞公事", "官职", "北宋熙宁九年八月二十五日",
        "始置，选人充局官者以此名称领事", main, "太医局差遣官",
        "建立知太医局丞公事始置节点。", officer="差遣官",
    )
    cite(w, "Timepoints", tid, i, field(i, "简称"), "知丞事只作简称证据。", "简称", note="简称不另建实体")
    staff(w, i, tp(w, "太医局", "机构", "北宋熙宁九年八月二十五日"), tid, main,
          "知太医局丞公事为选人充任的局官差遣。", staff_type="差遣官")
    rechain(w, eid, "整理知太医局丞公事时间链。")
    w.commit()


def entry138():
    i = 138
    main, history, duty, roster, rank = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "编制"), field(i, "品位"),
    )
    w = W(i)
    eid, start = upsert_state(
        w, i, "太医局教授", "官职", "北宋熙宁九年五月八日",
        "始置，各科一员，共九人，教导本科生员", history, "太医局教官",
        "建立太医局教授始置与九员编制节点。", "职源与沿革", officer="职事官",
        grade="重医术，或命官、或杂流",
    )
    cite(w, "Timepoints", start, i, duty, "记录教授教导本科生员之职掌。", "职掌")
    cite(w, "Timepoints", start, i, rank, "记录教授选拔范围与品位不一。", "品位")
    _, south = upsert_state(
        w, i, "太医局教授", "官职", "南宋", "沿置，教授共四员", roster,
        "太医局教官", "建立南宋教授四员节点。", "编制", officer="职事官",
    )
    staff(w, i, tp(w, "太医局", "机构", "北宋熙宁九年五月八日"), start, roster,
          "熙宁九年太医局九科各教授一员，共九员。", "编制", quota=9, staff_type="教官")
    staff(w, i, tp(w, "太医局", "机构", "南宋"), south, roster,
          "南宋太医局教授共四员。", "编制", quota=4, staff_type="教官")
    courses = (
        "大方脉科", "风科", "小方脉科", "产科", "口齿兼咽喉科",
        "疮肿兼伤折科", "眼科", "针灸科", "金镞兼书禁科",
    )
    touched = {eid}
    for course in courses:
        title = f"{course}教授"
        course_eid, course_tp = upsert_state(
            w, i, course, "机构", "北宋熙宁九年五月八日",
            "太医局创置九科教授时所属医学科", roster,
            "太医局医学科", f"为{title}建立熙宁九年同期医学科节点。", "编制",
        )
        ceid, ctp = upsert_state(
            w, i, title, "官职", "北宋熙宁九年五月八日",
            f"始置，掌教导{course}生员，编制一员", roster,
            "太医局分科教授", f"建立原文明举的{title}。", "编制", officer="职事官",
        )
        relationship(
            w, i, tp(w, "太医局", "机构", "北宋熙宁九年五月八日"), course_tp,
            "上下级机构", roster, f"太医局诸科包括{course}。", "编制",
        )
        relationship(w, i, start, ctp, "统称与实例", roster,
                     f"太医局教授的九科实例包括{title}。", "编制")
        staff(w, i, course_tp, ctp, roster,
              f"{course}教授一员。", "编制", quota=1, staff_type="教官")
        touched.update((course_eid, ceid))
    for touched_eid in touched:
        rechain(w, touched_eid, "整理太医局教授及九科教授时间链。")
    w.commit()


def entry139_140():
    i, main = 139, F[139]["text"]
    w = W(i)
    medical_eid, medical_before = upsert_state(
        w, i, "太医局", "机构", "北宋熙宁八年十二月",
        "设提举官领局后，改以‘提举太医局所’为名", main,
        "中央医学教育机构", "建立太医局改名前的同期节点。",
    )
    eid, start = upsert_state(
        w, i, "提举太医局所", "机构", "北宋熙宁八年十二月",
        "创置；太医局设提举官后改以此名，不复隶太常寺，奏禀可直达于上", main,
        "中央医学教育机构", "建立提举太医局所创置节点。",
    )
    _, end = upsert_state(
        w, i, "提举太医局所", "机构", "北宋元丰五年", "元丰新制罢", main,
        "中央医学教育机构", "建立提举太医局所罢置节点。",
    )
    relationship(
        w, i, medical_before, start,
        "前后演变", main, "太医局设提举官后改以‘提举太医局所’为名。",
    )
    rechain(w, eid, "整理提举太医局所创置与罢置链。")
    rechain(w, medical_eid, "补入太医局熙宁八年改名节点。")
    w.commit()

    i, main = 140, F[140]["text"]
    w = W(i)
    eid, start = upsert_state(
        w, i, "提举太医局", "官职", "北宋熙宁八年十二月",
        "初设，由京官充，掌领太医局公事，序位在判局之上", main,
        "太医局差遣官", "建立提举太医局初设节点。", officer="差遣官",
    )
    _, changed = upsert_state(
        w, i, "提举太医局", "官职", "北宋熙宁九年五月八日",
        "改由两制官充（不必懂医学），掌领本局公事", main,
        "太医局差遣官", "建立提举太医局充任变化节点。", officer="差遣官",
    )
    cite(w, "Timepoints", changed, i, field(i, "简称"), "提举官只作简称证据。", "简称", note="简称不另建实体")
    staff(w, i, tp(w, "提举太医局所", "机构", "北宋熙宁八年十二月"), start, main,
          "提举太医局领提举太医局所公事。", staff_type="差遣官")
    staff(w, i, tp(w, "太医局", "机构", "北宋熙宁九年五月八日"), changed, main,
          "熙宁九年提举官掌领太医局公事。", staff_type="差遣官")
    rechain(w, eid, "整理提举太医局初设与充任变化链。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(121, 141)] == [
        "胥佐", "贴书", "大乐案", "鼓吹案", "宴乐案", "法物案", "知杂案",
        "掌法案", "提举大晟府所", "伶人", "伶官", "排优", "太医局", "太医局令",
        "太医局正", "太医局丞", "知太医局丞公事", "教授", "提举太医局所", "提举太医局",
    ]
    entry121_122()
    entry123_128()
    entry129()
    entry130_132()
    entry133()
    entry134_137()
    entry138()
    entry139_140()


if __name__ == "__main__":
    main()
