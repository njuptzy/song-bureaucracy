#!/usr/bin/env python3
"""提取 chapter5t7 第21-40条：太常寺官属、九案及郊社局令。"""

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter
import extract_5t7_001_020 as previous


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
        "title": row[0],
        "page": row[1],
        "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(21, 41)}


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


def state(
    w,
    i,
    title,
    type_,
    time,
    event,
    quotation,
    category,
    decision,
    field_name=None,
    *,
    officer=None,
    grade=None,
    note=None,
    conflict_flag=0,
):
    eid = w.entity(title, type_, decision, quotation=quotation)
    tid = w.timepoint(
        eid,
        time,
        event,
        decision,
        quotation,
        attr_category=category,
        attr_officer_type=officer,
        attr_grade=grade,
        chain="none",
    )
    cite(
        w, "Timepoints", tid, i, quotation, decision, field_name,
        note=note, conflict_flag=conflict_flag,
    )
    return eid, tid


def refine(
    w,
    i,
    entity_id,
    time,
    event,
    quotation,
    category,
    decision,
    field_name=None,
    *,
    officer=None,
    grade=None,
):
    tid = w.find_timepoint(entity_id, time)
    if tid is None:
        title, type_ = w.conn.execute(
            "select title,type from Entities where id=?", (entity_id,)
        ).fetchone()
        return state(
            w, i, title, type_, time, event, quotation, category, decision,
            field_name, officer=officer, grade=grade,
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
    cite(w, "Timepoints", tid, i, quotation, decision, field_name)
    return tid


def relationship(
    w,
    i,
    subject_id,
    object_id,
    relation_type,
    quotation,
    decision,
    field_name=None,
    **kwargs,
):
    rid = w.relationship(
        subject_id, object_id, relation_type, decision, quotation, **kwargs
    )
    cite(w, "Relationships", rid, i, quotation, decision, field_name)
    return rid


SPECIAL_TIME_ORDER = {
    "战国秦昭王时代": -300,
    "秦汉": -150,
    "西汉": -100,
    "西汉武帝时": -90,
    "东汉": 25,
    "西晋": 265,
    "北魏太和十五年": 491,
    "北魏": 386,
    "北齐": 550,
    "隋": 581,
    "唐永徽二年以前": 600,
    "唐永徽二年": 651,
    "北宋初": 960,
    "英宗朝": 1063,
    "南宋初": 1127,
}


def time_key(time, row_id):
    if time in SPECIAL_TIME_ORDER:
        return (SPECIAL_TIME_ORDER[time], 0, row_id)
    return previous.time_key(time, row_id)


def rechain(w, entity_id, decision):
    rows = w.conn.execute(
        "select id,time from Timepoints where entity_id=?", (entity_id,)
    ).fetchall()
    ordered = [row[0] for row in sorted(rows, key=lambda row: time_key(row[1], row[0]))]
    for index, tid in enumerate(ordered):
        w.relink(
            tid,
            decision,
            prev_id=ordered[index - 1] if index else None,
            succ_id=ordered[index + 1] if index + 1 < len(ordered) else None,
        )


def entity_id(w, title, type_):
    eid = w.find_entity(title, type_)
    assert eid, (title, type_)
    return eid


def timepoint_id(w, title, type_, time):
    eid = entity_id(w, title, type_)
    tid = w.find_timepoint(eid, time)
    assert tid, (title, time)
    return tid


def temple_state(w, i, time, event, quotation, field_name=None):
    return state(
        w, i, "太常寺", "机构", time, event, quotation,
        "中央礼制机构", f"据{F[i]['title']}条建立太常寺{time}编制状态。",
        field_name,
    )


def staff_relation(
    w, i, parent_tp, post_tp, quotation, decision, field_name=None,
    *, quota=None, staff_type="官",
):
    return relationship(
        w, i, parent_tp, post_tp, "编制隶属", quotation, decision,
        field_name, staff_quota=quota, staff_type=staff_type,
    )


def alias_citation(w, i, tid, field_name="简称与别名"):
    if field_name in F[i]["fields"]:
        cite(
            w, "Timepoints", tid, i, field(i, field_name),
            f"{F[i]['title']}简称与典故称谓仅作名称证据。",
            field_name, note="纯简称、别名不另建实体",
        )


def entry21():
    i = 21
    main, history, duty, rank, staff = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"),
    )
    w = W(i)
    eid = entity_id(w, "太常寺少卿", "官职")
    origin1 = refine(
        w, i, eid, "北魏太和十五年", "始置太常少卿", history,
        "前代职源", "建立太常寺少卿北魏职源节点。", "职源与沿革",
        officer="副长官",
    )
    origin2 = refine(
        w, i, eid, "北齐", "始置太常寺少卿", history,
        "前代职源", "建立太常寺少卿北齐职源节点。", "职源与沿革",
        officer="副长官",
    )
    early = refine(
        w, i, eid, "北宋前期", "无职事，为文臣寄禄官", duty,
        "文臣寄禄官", "细化太常寺少卿北宋前期性质。", "职掌",
        officer="阶官", grade="正四品上",
    )
    reform = refine(
        w, i, eid, "北宋元丰五年新制",
        "易阶官为朝议大夫；改为太常寺副长官，佐正卿领寺事",
        duty, "太常寺副长官", "细化太常寺少卿元丰职事。", "职掌",
        officer="职事官", grade="从五品",
    )
    south = refine(
        w, i, eid, "南宋绍兴以后",
        "一人；太常卿不常置时专领寺任，并可兼宗正寺少卿",
        field(i, "简称与别名"), "太常寺副长官",
        "补全南宋太常寺少卿专领寺任及兼官事实。", "简称与别名",
        officer="职事官", grade="从五品",
    )
    cite(w, "Timepoints", early, i, rank, "补证宋前期品位。", "品位")
    cite(w, "Timepoints", reform, i, rank, "补证元丰后从五品及班序。", "品位")
    cite(w, "Timepoints", reform, i, staff, "补证太常寺少卿一人。", "编制")
    cite(w, "Timepoints", reform, i, main, "正文区分宋前期阶官与元丰职事官。")
    alias_citation(w, i, reform)
    parent_early = temple_state(w, i, "北宋前期", "置无职事太常寺少卿阶官", duty, "职掌")[1]
    parent_reform = timepoint_id(w, "太常寺", "机构", "北宋元丰改制后")
    parent_south = temple_state(w, i, "南宋绍兴以后", "置太常寺少卿一人专领寺任", staff, "编制")[1]
    staff_relation(w, i, parent_early, early, duty, "宋前期太常寺少卿为无职事阶官。", "职掌", staff_type="阶官")
    staff_relation(w, i, parent_reform, reform, duty, "元丰新制太常寺少卿为副长官。", "职掌", quota=1, staff_type="职事官")
    staff_relation(w, i, parent_south, south, staff, "南宋太常寺置少卿一人。", "编制", quota=1, staff_type="职事官")
    rechain(w, eid, "连接太常寺少卿北魏、北齐、宋前期、元丰与南宋节点。")
    rechain(w, entity_id(w, "太常寺", "机构"), "插入太常寺少卿相关编制节点。")
    assert origin1 and origin2
    w.commit()


def entry22():
    i = 22
    quote = F[i]["text"]
    w = W(i)
    group_eid, group_tp = state(
        w, i, "太常卿少", "官职", "宋代", "太常卿与太常少卿连称",
        quote, "官职统称", "建立太常卿少统称节点。",
    )
    for title in ("太常寺卿", "太常寺少卿"):
        member = timepoint_id(w, title, "官职", "宋代")
        relationship(w, i, group_tp, member, "统称与实例", quote,
                     f"{title}是太常卿少的实例。")
    rechain(w, group_eid, "确认太常卿少单节点时间链。")
    w.commit()


def entry23():
    i = 23
    main, history, duty, rank, staff = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"),
    )
    w = W(i)
    eid = entity_id(w, "太常寺丞", "官职")
    refine(w, i, eid, "西汉", "始置太常丞", history, "前代职源",
           "建立太常寺丞西汉职源节点。", "职源与沿革", officer="佐贰官")
    refine(w, i, eid, "北齐", "始置太常寺丞", history, "前代职源",
           "建立太常寺丞北齐职源节点。", "职源与沿革", officer="佐贰官")
    early = refine(
        w, i, eid, "宋前期", "无职事，为文臣寄禄官", duty,
        "文臣寄禄官", "细化太常寺丞宋前期性质。", "职掌",
        officer="阶官", grade="从五品上",
    )
    reform = refine(
        w, i, eid, "北宋元丰新制",
        "官阶易奉议郎；改为职事官，参领太常寺事",
        duty, "太常寺佐贰官", "细化太常寺丞元丰职事。", "职掌",
        officer="职事官", grade="从七品",
    )
    changes = (
        ("南宋建炎三年四月", "罢置"),
        ("南宋绍兴三年六月", "复置"),
        ("南宋隆兴元年", "再次罢置"),
        ("南宋隆兴二年", "再次复置"),
    )
    for time, event in changes:
        refine(w, i, eid, time, event, history, "太常寺佐贰官",
               f"建立太常寺丞{time}{event}节点。", "职源与沿革",
               officer="职事官", grade="从七品")
    cite(w, "Timepoints", early, i, rank, "补证宋前期品位。", "品位")
    cite(w, "Timepoints", reform, i, rank,
         "补证元丰后从七品及三丞地位。", "品位")
    cite(w, "Timepoints", reform, i, staff, "补证太常寺丞一人。", "编制")
    cite(w, "Timepoints", reform, i, main, "正文区分阶官与职事官。")
    alias_citation(w, i, reform)
    parent_early = timepoint_id(w, "太常寺", "机构", "宋前期")
    parent_reform = timepoint_id(w, "太常寺", "机构", "北宋元丰改制后")
    staff_relation(w, i, parent_early, early, duty, "宋前期太常寺丞为无职事阶官。", "职掌", staff_type="阶官")
    staff_relation(w, i, parent_reform, reform, duty, "元丰太常寺丞参领寺事。", "职掌", quota=1, staff_type="职事官")
    for time, event in changes:
        parent = temple_state(w, i, time, f"太常寺丞{event}", history, "职源与沿革")[1]
        post = w.find_timepoint(eid, time)
        if "复置" in event:
            staff_relation(w, i, parent, post, history, f"{time}太常寺丞{event}。", "职源与沿革", quota=1, staff_type="职事官")
    rechain(w, eid, "连接太常寺丞前代、宋前期、元丰与南宋罢复节点。")
    rechain(w, entity_id(w, "太常寺", "机构"), "插入太常寺丞南宋罢复编制节点。")
    w.commit()


def entry24():
    i = 24
    main, history, duty, rank, staff = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"),
    )
    w = W(i)
    eid = entity_id(w, "太常寺博士", "官职")
    refine(w, i, eid, "西汉", "太常属官已有博士，掌通古今、定礼或教授五经",
           history, "前代职源", "建立太常寺博士西汉职源节点。", "职源与沿革", officer="礼官")
    refine(w, i, eid, "北齐", "始置太常博士", history, "前代职源",
           "建立太常寺博士北齐职源节点。", "职源与沿革", officer="礼官")
    early = refine(w, i, eid, "北宋初", "沿置，为文臣迁转官阶", history,
                   "文臣迁转官阶", "建立太常寺博士北宋初节点。", "职源与沿革",
                   officer="阶官", grade="从七品上")
    dzhf = refine(
        w, i, eid, "北宋大中祥符间", "置二员为职事官，掌定谥等事",
        duty, "太常寺礼官", "建立太常寺博士大中祥符职事节点。", "职掌",
        officer="职事官", grade="从七品上",
    )
    reform = refine(
        w, i, eid, "北宋元丰改制后",
        "止为职事官，讲定五礼、审议礼制、拟谥并监视祠祭仪物",
        duty, "太常寺礼官", "细化太常寺博士元丰职掌。", "职掌",
        officer="职事官", grade="正八品",
    )
    cite(w, "Timepoints", reform, i, rank, "补证元丰后正八品及班序。", "品位")
    cite(w, "Timepoints", dzhf, i, staff, "补证大中祥符间二员。", "编制")
    cite(w, "Timepoints", reform, i, staff, "补证元丰后四员。", "编制")
    cite(w, "Timepoints", reform, i, main, "正文概括阶官、兼置职事官与元丰专为职事官。")
    alias_citation(w, i, reform)
    parent_early = temple_state(w, i, "北宋初", "太常寺博士为迁转官阶", history, "职源与沿革")[1]
    parent_dzhf = temple_state(w, i, "北宋大中祥符间", "置职事太常寺博士二员", staff, "编制")[1]
    parent_reform = timepoint_id(w, "太常寺", "机构", "北宋元丰改制后")
    staff_relation(w, i, parent_early, early, history, "北宋初太常寺博士为迁转官阶。", "职源与沿革", staff_type="阶官")
    staff_relation(w, i, parent_dzhf, dzhf, staff, "大中祥符间太常寺置职事博士二员。", "编制", quota=2, staff_type="职事官")
    staff_relation(w, i, parent_reform, reform, staff, "元丰后太常寺博士四员。", "编制", quota=4, staff_type="职事官")
    rechain(w, eid, "连接太常寺博士西汉、北齐、北宋初、大中祥符与元丰节点。")
    rechain(w, entity_id(w, "太常寺", "机构"), "插入太常寺博士相关编制节点。")
    w.commit()


def entry25():
    i = 25
    main, history, duty, rank, staff = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"),
    )
    w = W(i)
    eid = entity_id(w, "太常寺主簿", "官职")
    origins = (
        ("战国秦昭王时代", "已有主簿之名"),
        ("西晋", "始置太常主簿"),
        ("北齐", "始置太常寺主簿"),
    )
    for time, event in origins:
        refine(w, i, eid, time, event, history, "前代职源",
               f"建立太常寺主簿{time}职源节点。", "职源与沿革", officer="主簿")
    early = refine(w, i, eid, "宋前期", "文臣迁转官阶，偶为职事官", duty,
                   "文臣迁转官阶", "细化太常寺主簿宋前期性质。", "职掌",
                   officer="阶官或职事官")
    huangyou = refine(
        w, i, eid, "北宋皇祐三年二月一日",
        "置有职事太常寺主簿一人，勾检寺中文书并掌出纳",
        history, "太常寺主簿", "建立皇祐三年职事主簿节点。", "职源与沿革",
        officer="职事官",
    )
    stop = refine(w, i, eid, "北宋皇祐四年后", "不复置职事太常寺主簿",
                  history, "太常寺主簿", "建立皇祐四年后停置节点。", "职源与沿革")
    reform = refine(
        w, i, eid, "北宋元丰新制",
        "九寺五监均置主簿；掌稽考、点检簿书、出纳文书并与闻礼乐",
        duty, "太常寺主簿", "细化太常寺主簿元丰职掌。", "职掌",
        officer="职事官", grade="从八品",
    )
    suspend = refine(w, i, eid, "南宋建炎三年至绍兴十年间", "省而不置",
                     history, "太常寺主簿", "建立南宋省置区间节点。", "职源与沿革")
    restore = refine(w, i, eid, "南宋绍兴十年以后", "恢复沿置",
                     history, "太常寺主簿", "建立绍兴十年后恢复节点。", "职源与沿革",
                     officer="职事官", grade="从八品")
    cite(w, "Timepoints", reform, i, rank, "补证元丰后从八品。", "品位")
    cite(w, "Timepoints", huangyou, i, staff, "补证太常寺主簿一人。", "编制")
    cite(w, "Timepoints", reform, i, main, "正文说明兼有寄禄官与职事官性质。")
    alias_citation(w, i, reform)
    for time, post, event in (
        ("北宋皇祐三年二月一日", huangyou, "置职事主簿一人"),
        ("北宋皇祐四年后", stop, "不复置职事主簿"),
        ("南宋建炎三年至绍兴十年间", suspend, "省太常寺主簿"),
        ("南宋绍兴十年以后", restore, "恢复太常寺主簿"),
    ):
        parent = temple_state(w, i, time, event, history, "职源与沿革")[1]
        if post in (huangyou, restore):
            staff_relation(w, i, parent, post, history, event, "职源与沿革", quota=1, staff_type="职事官")
    parent_reform = timepoint_id(w, "太常寺", "机构", "北宋元丰改制后")
    staff_relation(w, i, parent_reform, reform, duty, "元丰新制太常寺置主簿。", "职掌", quota=1, staff_type="职事官")
    assert early
    rechain(w, eid, "连接太常寺主簿前代、宋前期、皇祐、元丰与南宋节点。")
    rechain(w, entity_id(w, "太常寺", "机构"), "插入太常寺主簿相关编制节点。")
    w.commit()


def flag_existing_dacheng_conflict(w, i, note):
    rows = list(
        w.conn.execute(
            "select c.id,c.conflict_flag,c.note from Citations c join Timepoints t "
            "on c.target_table='Timepoints' and c.target_id=t.id "
            "join Entities e on e.id=t.entity_id "
            "where c.citation like '%\"太常寺\"条%' "
            "and ((e.title='大晟府' and t.time='北宋崇宁四年八月') "
            "or (e.title='太常寺' and t.time='北宋崇宁四年八月'))"
        )
    )
    assert len(rows) == 2, rows
    for cid, old_flag, old_note in rows:
        if old_flag == 1 and old_note == note:
            continue
        w.conn.execute("update Citations set conflict_flag=1,note=? where id=?", (note, cid))
        w._br("Citations", cid, f"第26条与第17条关于大晟府年代冲突，标记既有引用：{note}")


def flag_target_citation(w, i, table, target_id, quotation, note, field_name=None):
    row = w.conn.execute(
        "select id,conflict_flag,note from Citations where target_table=? "
        "and target_id=? and citation=? and quotation=?",
        (table, target_id, C(i, field_name), quotation),
    ).fetchone()
    assert row, (table, target_id, i, field_name)
    if row[1] == 1 and row[2] == note:
        return
    w.conn.execute(
        "update Citations set conflict_flag=1,note=? where id=?", (note, row[0])
    )
    w._br(
        "Citations", row[0],
        f"标记第{i}条所据制度事实与另一条年代冲突：{note}",
    )


def entry26():
    i = 26
    main, history, duty, rank, staff = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"),
    )
    w = W(i)
    eid = entity_id(w, "太常寺协律郎", "官职")
    stages = (
        ("西汉武帝时", "始置协律都尉，为协律官职源", "前代职源"),
        ("北魏", "始置协律郎", "前代职源"),
        ("北齐", "始置太常寺协律郎", "前代职源"),
        ("北宋前期", "大朝会、宴享或亲郊祀时临时遣官摄协律郎事", "太常寺乐官"),
        ("北宋元祐", "见置，隶太常寺", "太常寺乐官"),
        ("北宋崇宁二年", "改隶大晟府", "大晟府乐官"),
        ("南宋", "临时差摄", "太常寺乐官"),
    )
    tids = {}
    for time, event, category in stages:
        tids[time] = refine(
            w, i, eid, time, event, history, category,
            f"建立太常寺协律郎{time}节点。", "职源与沿革",
            officer="职事官" if "宋" in time else "前代乐官",
            grade="从八品" if "宋" in time else None,
        )
    cite(w, "Timepoints", tids["北宋元祐"], i, duty, "补证协律郎职掌。", "职掌")
    cite(w, "Timepoints", tids["北宋元祐"], i, rank, "补证从八品。", "品位")
    cite(w, "Timepoints", tids["北宋元祐"], i, staff, "补证一人。", "编制")
    cite(w, "Timepoints", tids["北宋元祐"], i, main, "正文明确其为职事官。")
    alias_citation(w, i, tids["北宋元祐"], "简称")
    parent_early = temple_state(w, i, "北宋前期", "临时差摄协律郎", history, "职源与沿革")[1]
    parent_yuanyou = temple_state(w, i, "北宋元祐", "置协律郎一人", history, "职源与沿革")[1]
    staff_relation(w, i, parent_early, tids["北宋前期"], history, "北宋前期太常寺临时差摄协律郎。", "职源与沿革", staff_type="临时差摄")
    staff_relation(w, i, parent_yuanyou, tids["北宋元祐"], staff, "元祐太常寺置协律郎一人。", "编制", quota=1, staff_type="职事官")

    conflict_note = "本条原书称崇宁二年协律郎隶大晟府，与第17条称崇宁四年八月建大晟府年代冲突，原说并存。"
    dacheng_eid, dacheng_2 = state(
        w, i, "大晟府", "机构", "北宋崇宁二年", "协律郎已改隶大晟府",
        history, "中央音乐机构", "据协律郎条建立大晟府崇宁二年节点。",
        "职源与沿革", note=conflict_note, conflict_flag=1,
    )
    flag_existing_dacheng_conflict(w, i, conflict_note)
    flag_target_citation(
        w, i, "Timepoints", tids["北宋崇宁二年"], history,
        conflict_note, "职源与沿革",
    )
    conflict_relation = staff_relation(
        w, i, dacheng_2, tids["北宋崇宁二年"], history,
        "崇宁二年协律郎改隶大晟府。", "职源与沿革",
        quota=1, staff_type="职事官",
    )
    flag_target_citation(
        w, i, "Relationships", conflict_relation, history,
        conflict_note, "职源与沿革",
    )
    rechain(w, eid, "连接太常寺协律郎前代、北宋、改隶大晟府与南宋节点。")
    rechain(w, entity_id(w, "太常寺", "机构"), "插入协律郎相关太常寺节点。")
    rechain(w, dacheng_eid, "连接大晟府内部冲突年代节点。")
    w.commit()


def entry27():
    i = 27
    main, history, duty, rank, staff = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"),
    )
    w = W(i)
    eid = entity_id(w, "太常寺奉礼郎", "官职")
    old_eid, old = state(
        w, i, "理礼郎", "官职", "唐永徽二年以前", "此前均称理礼郎",
        history, "前代礼官", "建立理礼郎唐代节点。", "职源与沿革", officer="礼官",
    )
    _, rename_end = state(
        w, i, "理礼郎", "官职", "唐永徽二年", "改名奉礼郎",
        history, "前代礼官", "建立理礼郎改名节点。", "职源与沿革", officer="礼官",
    )
    tang = refine(w, i, eid, "唐永徽二年", "理礼郎改名奉礼郎", history,
                  "前代礼官", "建立奉礼郎唐永徽改名节点。", "职源与沿革", officer="礼官")
    early = refine(
        w, i, eid, "宋前期", "文臣寄禄官，多作门荫官并供祠祭行事",
        duty, "文臣寄禄官", "建立太常寺奉礼郎宋前期节点。", "职掌",
        officer="阶官", grade="从九品上",
    )
    reform = refine(
        w, i, eid, "北宋元丰改制后",
        "职事官，掌祭祀奉币帛授初献官并布置皇帝亲祠板位",
        duty, "太常寺礼官", "细化太常寺奉礼郎元丰职掌。", "职掌",
        officer="职事官", grade="从八品",
    )
    relationship(w, i, rename_end, tang, "前后演变", history,
                 "唐永徽二年理礼郎改名奉礼郎。", "职源与沿革")
    cite(w, "Timepoints", early, i, rank, "补证宋前期品位及门荫待遇。", "品位")
    cite(w, "Timepoints", reform, i, rank, "补证元丰后从八品。", "品位")
    cite(w, "Timepoints", reform, i, staff, "补证元丰新制一人。", "编制")
    cite(w, "Timepoints", reform, i, main, "正文区分寄禄官与职事官。")
    alias_citation(w, i, reform, "简称")
    parent_early = timepoint_id(w, "太常寺", "机构", "宋前期")
    parent_reform = timepoint_id(w, "太常寺", "机构", "北宋元丰改制后")
    staff_relation(w, i, parent_early, early, duty, "宋前期太常寺奉礼郎为寄禄官并供祠祭。", "职掌", staff_type="阶官")
    staff_relation(w, i, parent_reform, reform, staff, "元丰太常寺置奉礼郎一人。", "编制", quota=1, staff_type="职事官")
    rechain(w, old_eid, "连接理礼郎沿革节点。")
    rechain(w, eid, "连接奉礼郎唐代、宋前期与元丰节点。")
    assert old
    w.commit()


def entry28():
    i = 28
    main, history, duty, rank, staff = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"),
    )
    w = W(i)
    eid = entity_id(w, "太常寺太祝", "官职")
    refine(w, i, eid, "秦汉", "为奉常（太常）属官", history,
           "前代职源", "建立太常寺太祝秦汉职源节点。", "职源与沿革", officer="礼官")
    refine(w, i, eid, "北齐", "始置太常寺太祝", history,
           "前代职源", "建立太常寺太祝北齐职源节点。", "职源与沿革", officer="礼官")
    early = refine(
        w, i, eid, "宋前期", "文臣寄禄官，多作门荫官",
        duty, "文臣寄禄官", "建立太常寺太祝宋前期节点。", "职掌",
        officer="阶官", grade="从九品上",
    )
    reform = refine(
        w, i, eid, "北宋元丰改制后",
        "职事官，祭祀掌读册辞、奉毛血盘并进抟黍以嘏告",
        duty, "太常寺礼官", "细化太常寺太祝元丰职掌。", "职掌",
        officer="职事官", grade="从八品",
    )
    cite(w, "Timepoints", early, i, rank, "补证宋前期品位及门荫待遇。", "品位")
    cite(w, "Timepoints", reform, i, rank, "补证元丰后从八品。", "品位")
    cite(w, "Timepoints", reform, i, staff, "补证元丰新制一人。", "编制")
    cite(w, "Timepoints", reform, i, main, "正文区分迁转官与职事官。")
    alias_citation(w, i, reform)
    parent_early = timepoint_id(w, "太常寺", "机构", "宋前期")
    parent_reform = timepoint_id(w, "太常寺", "机构", "北宋元丰改制后")
    staff_relation(w, i, parent_early, early, duty, "宋前期太常寺太祝为寄禄官。", "职掌", staff_type="阶官")
    staff_relation(w, i, parent_reform, reform, staff, "元丰太常寺置太祝一人。", "编制", quota=1, staff_type="职事官")
    rechain(w, eid, "连接太常寺太祝秦汉、北齐、宋前期与元丰节点。")
    w.commit()


CASE_CANONICAL = {
    29: ("太常寺礼仪案", None),
    30: ("太常寺礼祭案", "太常寺祠祭案"),
    31: ("太常寺坛庙案", None),
    32: ("太常寺太乐案", "太常寺大乐案"),
    33: ("太常寺法物案", None),
    34: ("太常寺廪牺案", None),
    35: ("太常寺太医案", None),
    36: ("太常寺掌法案", None),
    37: ("太常寺知杂案", None),
}


def canonical_case_entity(w, i):
    canonical, old_title = CASE_CANONICAL[i]
    current = w.find_entity(canonical, "机构")
    old = w.find_entity(old_title, "机构") if old_title else None
    if current:
        assert old is None or old == current
        return current
    assert old, (canonical, old_title)
    w.conn.execute("update Entities set title=? where id=?", (canonical, old))
    w._br(
        "Entities", old,
        f"据第{i}条专名将第17条九案总表所用变体 {old_title} 规范为 {canonical}；"
        "沿用同一机构实体，不另造重复节点。",
    )
    return old


def case_entry(i):
    quote = F[i]["text"]
    canonical, _ = CASE_CANONICAL[i]
    w = W(i)
    eid = canonical_case_entity(w, i)
    tid = refine(
        w, i, eid, "北宋元丰改制后", quote, quote,
        "太常寺办事机构", f"据{F[i]['title']}专条细化{canonical}职掌。",
    )
    detail_quote = quote.split("。", 1)[1].strip()
    assert detail_quote
    cite(
        w, "Timepoints", tid, i, detail_quote,
        f"补证{canonical}具体承办职掌，使专条成为该实体的主要审查来源。",
    )
    parent = timepoint_id(w, "太常寺", "机构", "北宋元丰改制后")
    relationship(w, i, parent, tid, "上下级机构", quote,
                 f"{canonical}为元丰改制后太常寺办事机构。")
    rechain(w, eid, f"确认{canonical}时间链。")
    w.commit()


def entry38():
    i = 38
    main, history, duty, rank, staff = (
        F[i]["text"], field(i, "职源与沿革"), field(i, "职掌"),
        field(i, "品位"), field(i, "编制"),
    )
    w = W(i)
    old_eid, sui = state(
        w, i, "郊社署令", "官职", "隋", "隋太常寺已置郊社署令",
        history, "前代郊社官", "建立隋郊社署令节点。", "职源与沿革", officer="职事官",
    )
    _, song_old = state(
        w, i, "郊社署令", "官职", "北宋嘉祐元年十二月五日", "始置",
        history, "太常寺郊社官", "建立北宋郊社署令始置节点。", "职源与沿革",
        officer="职事官",
    )
    eid, rename = state(
        w, i, "郊社局令", "官职", "英宗朝",
        "避赵曙讳，由郊社署令改名郊社局令",
        history, "太常寺郊社官", "建立郊社局令避讳改名节点。", "职源与沿革",
        officer="职事官",
    )
    reform = refine(
        w, i, eid, "北宋元丰新制后",
        "巡视四郊坛壝及社稷、维护郊兆清洁，祭祀时参与省牲",
        duty, "太常寺郊社官", "建立郊社局令元丰职掌节点。", "职掌",
        officer="职事官", grade="正九品",
    )
    relationship(w, i, song_old, rename, "前后演变", history,
                 "英宗朝郊社署令避讳改名郊社局令。", "职源与沿革")
    cite(w, "Timepoints", reform, i, rank, "补证元丰后正九品。", "品位")
    cite(w, "Timepoints", reform, i, staff, "补证编制一人。", "编制")
    cite(w, "Timepoints", reform, i, main, "正文明确郊社局令隶太常寺郊社局。")
    alias_citation(w, i, reform)

    office_eid, office_start = state(
        w, i, "太常寺郊社局", "机构", "北宋嘉祐元年十二月五日",
        "置郊社署令，管理四郊坛壝及社稷",
        history, "太常寺所属机构", "建立太常寺郊社局嘉祐节点。", "职源与沿革",
    )
    _, office_reform = state(
        w, i, "太常寺郊社局", "机构", "北宋元丰新制后",
        "设郊社局令一人，管理四郊坛壝及社稷",
        duty, "太常寺所属机构", "建立太常寺郊社局元丰节点。", "职掌",
    )
    temple_start = temple_state(w, i, "北宋嘉祐元年十二月五日", "置郊社署令一人", history, "职源与沿革")[1]
    temple_reform = timepoint_id(w, "太常寺", "机构", "北宋元丰改制后")
    relationship(w, i, temple_start, office_start, "上下级机构", main,
                 "太常寺下设郊社局。")
    relationship(w, i, temple_reform, office_reform, "上下级机构", main,
                 "元丰新制太常寺下设郊社局。")
    staff_relation(w, i, office_start, song_old, staff, "嘉祐始置郊社署令一人。", "编制", quota=1, staff_type="职事官")
    staff_relation(w, i, office_reform, reform, staff, "元丰太常寺郊社局置令一人。", "编制", quota=1, staff_type="职事官")
    rechain(w, old_eid, "连接郊社署令隋与北宋节点。")
    rechain(w, eid, "连接郊社局令英宗改名与元丰节点。")
    rechain(w, office_eid, "连接太常寺郊社局嘉祐与元丰节点。")
    rechain(w, entity_id(w, "太常寺", "机构"), "插入郊社局相关太常寺节点。")
    assert sui
    w.commit()


def entry39():
    assert F[39]["text"] == ""
    assert F[39]["fields"].get("__status__") == "placeholder"
    assert "社稷令" in F[38]["fields"]["简称与别名"]


def entry40():
    i = 40
    main, rank, aliases = F[i]["text"], field(i, "品位"), field(i, "简称与别名")
    w = W(i)
    old_eid = entity_id(w, "郊社局令", "官职")
    old_end = refine(
        w, i, old_eid, "南宋初", "阙置郊社局令", main,
        "太常寺郊社官", "建立南宋初郊社局令阙置节点。",
        officer="职事官", grade="正九品",
    )
    eid, start = state(
        w, i, "太社局令", "官职", "南宋绍兴十九年二月二十三日",
        "始置；即郊社局令，职掌与编制同",
        main, "太常寺郊社官", "建立太社局令始置节点。",
        officer="职事官", grade="正九品",
    )
    cite(w, "Timepoints", start, i, rank, "补证正九品及请给等第。", "品位")
    cite(w, "Timepoints", start, i, aliases,
         "太社令、大社令仅作简称与别名证据。", "简称与别名",
         note="纯简称、别名不另建实体")
    relationship(w, i, old_end, start, "前后演变", main,
                 "南宋初阙郊社局令，绍兴十九年始置太社局令。")

    office_eid, office = state(
        w, i, "太常寺太社局", "机构", "南宋绍兴十九年二月二十三日",
        "始置太社局令，承郊社局职掌",
        main, "太常寺所属机构", "建立太常寺太社局绍兴始置节点。",
    )
    temple = temple_state(
        w, i, "南宋绍兴十九年二月二十三日", "置太社局令",
        main,
    )[1]
    relationship(w, i, temple, office, "上下级机构", main,
                 "太社局为太常寺所属机构。")
    staff_rel = staff_relation(
        w, i, office, start, main, "太社局置令一人，职掌编制同郊社局令。",
        quota=1, staff_type="职事官",
    )
    rechain(w, old_eid, "连接郊社局令北宋与南宋阙置节点。")
    rechain(w, eid, "确认太社局令绍兴始置时间链。")
    rechain(w, office_eid, "确认太常寺太社局时间链。")
    rechain(w, entity_id(w, "太常寺", "机构"), "插入太社局相关太常寺节点。")
    w.commit()

    # 第40条明确“职掌、编制与郊社局令同”；补引已在本批加载的第38条实际字段，
    # BuildRecords.source_entry 必须归属第38条而非第40条。
    w38 = W(38)
    duty38, staff38 = field(38, "职掌"), field(38, "编制")
    cite(w38, "Timepoints", start, 38, duty38,
         "太社局令职掌同郊社局令，补入第38条具体职掌。", "职掌")
    cite(w38, "Timepoints", start, 38, staff38,
         "太社局令编制同郊社局令，补入第38条一人编制。", "编制")
    cite(w38, "Relationships", staff_rel, 38, staff38,
         "太社局令编制同郊社局令，补证一人。", "编制")
    w38.commit()


def main():
    assert [F[i]["title"] for i in range(21, 41)] == [
        "太常寺少卿", "太常卿少", "太常寺丞", "太常寺博士", "太常寺主簿",
        "太常寺协律郎", "太常寺奉礼郎", "太常寺太祝", "礼仪案", "礼祭案",
        "坛庙案", "太乐案", "法物案", "廪牺案", "太医案", "掌法案",
        "知杂案", "郊社局令", "社稷令", "太社局令",
    ]
    entry21()
    entry22()
    entry23()
    entry24()
    entry25()
    entry26()
    entry27()
    entry28()
    for i in range(29, 38):
        case_entry(i)
    entry38()
    entry39()
    entry40()


if __name__ == "__main__":
    main()
