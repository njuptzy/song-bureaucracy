#!/usr/bin/env python3
"""提取 chapter2t4 第771–790条：中书省诸房、长官与中书后省系统。"""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ew import EntryWriter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DICT_DB = os.path.join(ROOT, "data/database/song_bureaucracy_dictionary_ch2t4.db")
ENTRY_DB = os.environ.get(
    "SONG_ENTRY_DB", os.path.join(ROOT, "data/database/song_bureaucracy_entries_ch2t4.db")
)


def load(i):
    with sqlite3.connect(DICT_DB) as conn:
        row = conn.execute(
            "select title,page,text,fields from chapter2t4 where id=?", (i,)
        ).fetchone()
    assert row, i
    return {
        "title": row[0],
        "page": row[1],
        "text": row[2] or "",
        "fields": json.loads(row[3] or "{}"),
    }


F = {i: load(i) for i in range(771, 791)}


def W(i):
    return EntryWriter(ENTRY_DB, F[i]["title"], F[i]["page"])


def Q(i, needle, field=None):
    source = F[i]["fields"][field] if field else F[i]["text"]
    assert needle in source, (i, field, needle)
    return needle


def C(i, field=None):
    base = f'《宋代官制辞典》第{F[i]["page"]}页"{F[i]["title"]}"条'
    return base + (f"（{field}字段）" if field else "")


def en(w, title, typ, quotation, decision):
    return w.entity(title, typ, decision, quotation=quotation)


def fe(w, title, typ=None):
    entity_id = w.find_entity(title, typ)
    assert entity_id, (title, typ)
    return entity_id


def ft(w, entity_id, time):
    timepoint_id = w.find_timepoint(entity_id, time)
    assert timepoint_id, (entity_id, time)
    return timepoint_id


def cite(w, table, target_id, i, quotation, decision, field=None, **kwargs):
    return w.citation(
        table, target_id, C(i, field), quotation, decision, **kwargs
    )


def tp(
    w,
    entity_id,
    time,
    event,
    i,
    quotation,
    category,
    decision,
    field=None,
    **kwargs,
):
    timepoint_id = w.timepoint(
        entity_id,
        time,
        event,
        decision,
        quotation,
        attr_category=category,
        **kwargs,
    )
    cite(w, "Timepoints", timepoint_id, i, quotation, decision, field)
    return timepoint_id


def rel(
    w,
    subject_id,
    object_id,
    relation_type,
    i,
    quotation,
    decision,
    field=None,
    **kwargs,
):
    relationship_id = w.relationship(
        subject_id,
        object_id,
        relation_type,
        decision,
        quotation,
        **kwargs,
    )
    cite(w, "Relationships", relationship_id, i, quotation, decision, field)
    return relationship_id


def chain(w, timepoint_ids, decision):
    assert timepoint_ids and len(timepoint_ids) == len(set(timepoint_ids))
    for index, timepoint_id in enumerate(timepoint_ids):
        w.relink(
            timepoint_id,
            decision,
            prev_id=timepoint_ids[index - 1] if index else None,
            succ_id=(
                timepoint_ids[index + 1]
                if index + 1 < len(timepoint_ids)
                else None
            ),
        )


def chain_all(w, entity_id, timepoint_ids, decision):
    all_ids = {
        row[0]
        for row in w.conn.execute(
            "select id from Timepoints where entity_id=?", (entity_id,)
        )
    }
    assert set(timepoint_ids) == all_ids, (
        entity_id,
        sorted(all_ids - set(timepoint_ids)),
    )
    chain(w, timepoint_ids, decision)


def refine(
    w,
    timepoint_id,
    i,
    quotation,
    decision,
    field=None,
    *,
    time=None,
    event=None,
    category=None,
    officer=None,
    grade=None,
):
    row = w.conn.execute(
        "select entity_id,time,event,attr_category,attr_officer_type,attr_grade,"
        "quotation from Timepoints where id=?",
        (timepoint_id,),
    ).fetchone()
    assert row, timepoint_id
    new_time = time if time is not None else row[1]
    clash = w.conn.execute(
        "select id from Timepoints where entity_id=? and time=? and id<>?",
        (row[0], new_time, timepoint_id),
    ).fetchone()
    assert not clash, (timepoint_id, new_time, clash)
    new = (
        new_time,
        event if event is not None else row[2],
        category if category is not None else row[3],
        officer if officer is not None else row[4],
        grade if grade is not None else row[5],
        quotation,
    )
    old = row[1:]
    if new != old:
        w.conn.execute(
            "update Timepoints set time=?,event=?,attr_category=?,"
            "attr_officer_type=?,attr_grade=?,quotation=? where id=?",
            (*new, timepoint_id),
        )
        w._br(
            "Timepoints",
            timepoint_id,
            f"据专条细化 time {row[1]}->{new[0]}、event {row[2]}->{new[1]}、"
            f"category {row[3]}->{new[2]}：{decision}",
        )
    cite(w, "Timepoints", timepoint_id, i, quotation, decision, field)
    return timepoint_id


def relation_id(
    w,
    subject_title,
    object_title,
    relation_type,
    subject_time=None,
    object_time=None,
):
    sql = (
        "select r.id from Relationships r "
        "join Timepoints s on s.id=r.subject_id "
        "join Entities es on es.id=s.entity_id "
        "join Timepoints o on o.id=r.object_id "
        "join Entities eo on eo.id=o.entity_id "
        "where es.title=? and eo.title=? and r.relation_type=?"
    )
    params = [subject_title, object_title, relation_type]
    if subject_time is not None:
        sql += " and s.time=?"
        params.append(subject_time)
    if object_time is not None:
        sql += " and o.time=?"
        params.append(object_time)
    row = w.conn.execute(sql + " order by r.id limit 1", params).fetchone()
    return row[0] if row else None


def set_rel_attrs(w, relationship_id, quota, staff_type, decision):
    old = w.conn.execute(
        "select staff_quota,staff_type from Relationships where id=?",
        (relationship_id,),
    ).fetchone()
    assert old, relationship_id
    new = (
        quota if quota is not None else old[0],
        staff_type if staff_type is not None else old[1],
    )
    if tuple(old) != new:
        w.conn.execute(
            "update Relationships set staff_quota=?,staff_type=? where id=?",
            (*new, relationship_id),
        )
        w._br(
            "Relationships",
            relationship_id,
            f"编制属性 quota {old[0]}->{new[0]}、staff_type {old[1]}->{new[1]}："
            f"{decision}",
        )


def mark_citation_conflict(w, table, target_id, i, quotation, note, decision, field=None):
    row = w.conn.execute(
        "select id,conflict_flag,note from Citations "
        "where target_table=? and target_id=? and citation=? and quotation=? "
        "order by id desc limit 1",
        (table, target_id, C(i, field), quotation),
    ).fetchone()
    assert row, (table, target_id, i)
    if row[1] != 1 or row[2] != note:
        w.conn.execute(
            "update Citations set conflict_flag=1,note=? where id=?",
            (note, row[0]),
        )
        w._br("Citations", row[0], f"将引用显式标为内部矛盾：{decision}")


def repair_entry775_name():
    i = 775
    main = Q(
        i,
        "中书省常设办事部门之一。掌受、发文书，后改为开拆房。"
        "按：《宋史·职官志》写作“主事房”，误。",
    )
    w = W(i)
    old_id = fe(w, "中书省主事房", "机构")
    assert w.find_entity("中书省生事房", "机构") is None
    old = w.conn.execute(
        "select title,quotation from Entities where id=?", (old_id,)
    ).fetchone()
    w.conn.execute(
        "update Entities set title=?,quotation=? where id=?",
        ("中书省生事房", main, old_id),
    )
    w._br(
        "Entities",
        old_id,
        "据专条纠正《宋史》误名：中书省主事房改为中书省生事房，保留原实体ID与关系。",
    )
    w.commit()


def refine_room(i, title, time, event):
    main = Q(i, F[i]["text"])
    w = W(i)
    entity_id = fe(w, title, "机构")
    tid = refine(
        w,
        ft(w, entity_id, time),
        i,
        main,
        f"专条细化{title}职掌。",
        event=event,
        category="中央政务办事部门",
    )
    rid = relation_id(w, "中书省", title, "上下级机构", object_time=time)
    assert rid
    cite(w, "Relationships", rid, i, main, f"专条补证{title}为中书省常设办事部门。")
    w.commit()


def entry771_778():
    specs = (
        (
            771,
            "中书省礼房",
            "北宋哲宗朝",
            "掌郊祀、陵庙典礼、封册、科举考官奏请及递送国书诏命",
        ),
        (
            772,
            "中书省兵房",
            "北宋哲宗朝",
            "掌除授外国头领王爵、官封及相关取旨文字",
        ),
        (
            773,
            "中书省刑房",
            "北宋元丰新制（中书省）",
            "掌赦宥罪人、贬官重新录用及相关取旨文字",
        ),
        (
            774,
            "中书省工房",
            "北宋元丰新制（中书省）",
            "掌重大营造经费预算奏请及河防修治",
        ),
        (
            775,
            "中书省生事房",
            "北宋元丰新制（中书省）",
            "掌收发文书，后改名开拆房",
        ),
        (
            776,
            "中书省班簿房",
            "北宋元丰新制（中书省）",
            "掌百官名籍、出身、历任与功过登记，以备选用",
        ),
        (
            777,
            "中书省制敕库房",
            "北宋元丰新制（中书省）",
            "掌汇编登记敕令格式、提供检阅及管理架阁库",
        ),
        (
            778,
            "中书省催驱房",
            "北宋哲宗朝",
            "催促诸房发送文书并纠察延误",
        ),
    )
    for spec in specs:
        refine_room(*spec)


def entry779():
    i = 779
    main = Q(i, "中书省常设办事部门之一。掌校对、检查诸房书写文书有无差误")
    w = W(i)
    institute_e = fe(w, "中书省", "机构")
    institute_late = tp(
        w,
        institute_e,
        "北宋后期（开拆、点检房，未载具体年月）",
        "设点检房，生事房后改为开拆房",
        i,
        main,
        "中央政务机构",
        "为点检房及开拆房补建中书省北宋后期节点。",
        chain="none",
    )
    chain_all(
        w,
        institute_e,
        [
            ft(w, institute_e, "魏黄初元年"),
            ft(w, institute_e, "北宋建隆三年前"),
            ft(w, institute_e, "北宋元丰改制前"),
            ft(w, institute_e, "北宋元丰新制"),
            ft(w, institute_e, "北宋元祐元年十一月"),
            ft(w, institute_e, "北宋哲宗朝（中书省分房变化）"),
            institute_late,
            ft(w, institute_e, "南宋建炎三年四月二十九日"),
        ],
        "把开拆、点检房节点接入中书省全局时间链。",
    )
    entity_id = en(w, "中书省点检房", "机构", main, "本条明确为中书省常设办事部门。")
    tid = tp(
        w,
        entity_id,
        "北宋后期（未载具体年月）",
        "校对、检查诸房书写文书差误",
        i,
        main,
        "中央政务办事部门",
        "建中书省点检房职掌节点。",
        chain="none",
    )
    rel(
        w,
        institute_late,
        tid,
        "上下级机构",
        i,
        main,
        "本条明载点检房为中书省常设办事部门。",
    )
    w.commit()


def entry780():
    i = 780
    main = Q(i, "中书省生事房改名。《通考·职官》5《中书省》：“又改生事房为开拆。”")
    w = W(i)
    source_e = fe(w, "中书省生事房", "机构")
    source_end = tp(
        w,
        source_e,
        "北宋后期（改开拆房，未载具体年月）",
        "改名中书省开拆房",
        i,
        main,
        "中央政务办事部门",
        "建生事房改名开拆房的终点。",
        chain="none",
    )
    chain_all(
        w,
        source_e,
        [
            ft(w, source_e, "北宋元丰新制（中书省）"),
            source_end,
        ],
        "连接生事房元丰始置与后期改名节点。",
    )
    target_e = en(w, "中书省开拆房", "机构", main, "本条明确为生事房改名后的机构。")
    target_t = tp(
        w,
        target_e,
        "北宋后期（未载具体年月）",
        "由中书省生事房改名，掌收发文书",
        i,
        main,
        "中央政务办事部门",
        "建中书省开拆房始置节点。",
        chain="none",
    )
    rel(
        w,
        source_end,
        target_t,
        "前后演变",
        i,
        main,
        "中书省生事房改名开拆房。",
    )
    rel(
        w,
        ft(
            w,
            fe(w, "中书省", "机构"),
            "北宋后期（开拆、点检房，未载具体年月）",
        ),
        target_t,
        "上下级机构",
        i,
        main,
        "开拆房为中书省常设办事部门。",
    )
    w.commit()


def entry781():
    i = 781
    main = Q(i, "宋前期差遣官名。")
    duty = Q(
        i,
        "掌郊祀册文、本司吏人任满覆奏、季度考核帐籍",
        "职掌",
    )
    grade = Q(i, "以中书舍人充判省事，官品依中书舍人官而定", "官品")
    w = W(i)
    entity_id = fe(w, "判中书省事", "官职")
    tid = refine(
        w,
        ft(w, entity_id, "宋前期"),
        i,
        main,
        "专条确认判中书省事为宋前期差遣官。",
        event="掌郊祀册文、吏人任满覆奏及季度考核帐籍",
        category="差遣官",
        officer="中书舍人",
    )
    cite(w, "Timepoints", tid, i, duty, "补证判中书省事职掌。", "职掌")
    cite(w, "Timepoints", tid, i, grade, "补证以中书舍人充任。", "官品")
    rid = relation_id(
        w,
        "中书省",
        "判中书省事",
        "编制隶属",
        "北宋元丰改制前",
        "宋前期",
    )
    assert rid
    cite(w, "Relationships", rid, i, main, "专条补证判中书省事隶中书省。")
    w.commit()


def entry782():
    i = 782
    origin = Q(
        i,
        "中书令之名始自汉武帝时，由服侍禁中的宦官担任。",
        "职源",
    )
    early = Q(
        i,
        "①宋前期不与政事，为加官或赠官，系叙禄位的阶官",
        "职掌",
    )
    yuan = Q(
        i,
        "②元丰新制，中书令虚设，以尚书右仆射兼中书侍郎行中书令之职。"
        "乾道八年(1172)罢而不置",
        "职掌",
    )
    grades = Q(
        i,
        "宋前期依《六典》正二品，元丰新制，“中书令正一品”",
        "官品",
    )
    w = W(i)
    entity_id = fe(w, "中书令", "官职")
    han = tp(
        w,
        entity_id,
        "汉武帝时",
        "中书令之名始见，由服侍禁中的宦官担任",
        i,
        origin,
        "禁中官",
        "建中书令汉代名源节点。",
        "职源",
        attr_officer_type="宦官",
        chain="none",
    )
    early_t = refine(
        w,
        ft(w, entity_id, "宋代（未载具体年月）"),
        i,
        early,
        "专条细化宋前期中书令为不预政事的加官、赠官。",
        "职掌",
        time="宋前期",
        event="不预政事，为加官或赠官，仅叙禄位",
        category="阶官、加官、赠官",
        grade="正二品",
    )
    cite(w, "Timepoints", early_t, i, grades, "补证宋前期中书令正二品。", "官品")
    yuan_t = refine(
        w,
        ft(w, entity_id, "北宋元丰新制（中书省）"),
        i,
        yuan,
        "专条明确元丰中书令虚设，右仆射兼中书侍郎仅行其职。",
        "职掌",
        event="官额虚设；尚书右仆射兼中书侍郎仅行中书令之职",
        category="职事官（虚设）",
        grade="正一品",
    )
    cite(w, "Timepoints", yuan_t, i, grades, "补证元丰新制中书令正一品。", "官品")
    south_end = refine(
        w,
        ft(w, entity_id, "南宋乾道八年二月"),
        i,
        yuan,
        "专条补证乾道八年中书令罢而不置。",
        "职掌",
        event="罢而不置",
        category="职事官（虚设）",
    )
    chain_all(
        w,
        entity_id,
        [han, early_t, yuan_t, south_end],
        "连接中书令汉代名源、宋前、元丰与乾道停置节点。",
    )
    rid = relation_id(
        w,
        "中书省",
        "中书令",
        "编制隶属",
        "北宋元丰新制",
        "北宋元丰新制（中书省）",
    )
    assert rid
    set_rel_attrs(w, rid, 1, "官（虚设）", "中书令条明确元丰新制官额虚设。")
    cite(
        w,
        "Relationships",
        rid,
        i,
        yuan,
        "中书令条补证元丰官额虚设，不把“行中书令之职”误作正式授官。",
        "职掌",
    )
    w.commit()


def entry783():
    i = 783
    main = Q(
        i,
        "中书省令曾用名。徽宗朝政和二年九月二十五日，诏改中书令为右弼。"
        "靖康元年十一月二十九日复旧称",
    )
    w = W(i)
    source_e = fe(w, "中书令", "官职")
    source_change = tp(
        w,
        source_e,
        "北宋政和二年九月二十五日",
        "改名右弼",
        i,
        main,
        "职事官（虚设）",
        "建中书令政和二年改名节点。",
        chain="none",
    )
    source_restore = tp(
        w,
        source_e,
        "北宋靖康元年十一月二十九日",
        "右弼复旧称中书令",
        i,
        main,
        "职事官（虚设）",
        "建靖康元年恢复中书令旧称节点。",
        chain="none",
    )
    chain_all(
        w,
        source_e,
        [
            ft(w, source_e, "汉武帝时"),
            ft(w, source_e, "宋前期"),
            ft(w, source_e, "北宋元丰新制（中书省）"),
            source_change,
            source_restore,
            ft(w, source_e, "南宋乾道八年二月"),
        ],
        "把政和改名与靖康复旧节点接入中书令时间链。",
    )
    target_e = fe(w, "右弼", "官职")
    target_start = refine(
        w,
        ft(w, target_e, "北宋政和二年九月"),
        i,
        main,
        "专条给出右弼改名始置确日。",
        time="北宋政和二年九月二十五日",
        event="由中书令改名，为中书省令官名",
        category="宰相职事官",
    )
    target_end = tp(
        w,
        target_e,
        "北宋靖康元年十一月二十九日",
        "复旧称中书令",
        i,
        main,
        "宰相职事官",
        "建右弼靖康元年复旧称终点。",
        chain="none",
    )
    chain_all(w, target_e, [target_start, target_end], "连接右弼政和始置与靖康复旧节点。")
    rel(
        w,
        source_change,
        target_start,
        "前后演变",
        i,
        main,
        "政和二年中书令改名右弼。",
    )
    rel(
        w,
        target_end,
        source_restore,
        "前后演变",
        i,
        main,
        "靖康元年右弼复旧称中书令。",
    )
    w.commit()


def entry784():
    i = 784
    main = Q(i, "宋前期阶官名，新制职事官名。")
    origin = Q(
        i,
        "中书侍郎之名始于晋，“及晋，（通事郎）改曰中书侍郎”"
        "（《晋书·职官志》）。隋称内史省侍郎、内书省侍郎。"
        "唐武德三年改为中书省侍郎",
        "职源",
    )
    early = Q(
        i,
        "① 宋前期为同中书门下平章事（宰相）所带阶官，实无职事。",
        "职掌",
    )
    yuan = Q(
        i,
        "② 元丰新制，中书侍郎有两种职能，一为尚书右仆射兼官，充宰相之职；"
        "一为单除，代参知政事行副宰相之职",
        "职掌",
    )
    south = Q(
        i,
        "③ 建炎三年四月，中书侍郎复改为参知政事，"
        "右仆射亦不兼中书侍郎",
        "职掌",
    )
    grades = Q(
        i,
        "① 宋前期沿唐制为正三品。② 元丰新制后为正二品",
        "品位",
    )
    w = W(i)
    entity_id = fe(w, "中书侍郎", "官职")
    for time in ("晋", "隋", "唐武德三年"):
        cite(
            w,
            "Timepoints",
            ft(w, entity_id, time),
            i,
            origin,
            "专条补证中书侍郎晋、隋、唐名称沿革。",
            "职源",
        )
    early_t = refine(
        w,
        ft(w, entity_id, "宋前期"),
        i,
        early,
        "专条明确宋前期仅为宰相所带阶官，实无职事。",
        "职掌",
        event="同中书门下平章事所带阶官，实无职事",
        category="阶官",
        grade="正三品",
    )
    cite(w, "Timepoints", early_t, i, grades, "补证宋前期正三品。", "品位")
    yuan_t = refine(
        w,
        ft(w, entity_id, "北宋元丰新制"),
        i,
        yuan,
        "专条区分兼官充宰相与单除行副相职两种正式任用。",
        "职掌",
        event="可由尚书右仆射兼任充宰相，或单除行副宰相职",
        category="职事官",
        grade="正二品",
    )
    cite(w, "Timepoints", yuan_t, i, grades, "补证元丰新制后正二品。", "品位")
    refine(
        w,
        ft(w, entity_id, "南宋建炎三年四月十三日"),
        i,
        south,
        "专条补证建炎三年复改参知政事且右仆射不再兼任。",
        "职掌",
        event="复改为参知政事，右仆射不再兼中书侍郎",
        category="职事官",
    )
    rid = relation_id(
        w,
        "中书省",
        "中书侍郎",
        "编制隶属",
        "北宋元丰新制",
        "北宋元丰新制",
    )
    assert rid
    cite(w, "Relationships", rid, i, main, "专条补证元丰中书侍郎为中书省职事官。")
    w.commit()


def entry785_core():
    i = 785
    origin = Q(
        i,
        "元丰四年（1081）十月行新官制时创建。"
        "“元丰官制，门下、中书各增建后省”",
        "职源",
    )
    north_staff = Q(
        i,
        "①元丰新制，官额：右散骑常侍、右谏议大夫、右司谏、右正言各一员，"
        "中书舍人六员，起居舍人一员。以中书舍人判后省事。"
        "设案五：上案、下案、制诰、谏官、记注。",
        "编制",
    )
    south_intro = Q(
        i,
        "②建炎三年复置，以中书舍人为长官，常除二员，余官同元丰之制。"
        "设案四：上案、下案、制诰、记注案。",
        "编制",
    )
    south_clerks = Q(
        i,
        "吏额十人：点检一、令史二、守当官五",
        "编制",
    )
    w = W(i)
    entity_id = fe(w, "中书后省", "机构")
    start = refine(
        w,
        ft(w, entity_id, "北宋元丰新官制"),
        i,
        origin,
        "专条给出中书后省始置确月。",
        "职源",
        time="北宋元丰四年十月",
        event="行新官制时创建",
        category="中书省附属政务机构",
    )
    cite(w, "Timepoints", start, i, north_staff, "补证元丰中书后省官额与五案。", "编制")
    south = tp(
        w,
        entity_id,
        "南宋建炎三年",
        "复置，以中书舍人为长官，设上、下、制诰、记注四案",
        i,
        south_intro,
        "中书门下省附属政务机构",
        "建中书后省建炎三年复置节点。",
        "编制",
        chain="none",
    )
    cite(
        w,
        "Timepoints",
        south,
        i,
        south_clerks,
        "补证南宋吏额；原文总额十人与分项合计八人不一致。",
        "编制",
        note="辞典原文称吏额十人，但点检一、令史二、守当官五合计仅八人。",
        conflict_flag=1,
    )
    mark_citation_conflict(
        w,
        "Timepoints",
        south,
        i,
        south_clerks,
        "辞典原文称吏额十人，但点检一、令史二、守当官五合计仅八人。",
        "保留中书后省南宋吏额总数与分项合计不一致。",
        "编制",
    )
    chain_all(w, entity_id, [start, south], "连接中书后省元丰始置与建炎复置节点。")
    rel(
        w,
        ft(w, fe(w, "中书省", "机构"), "北宋元丰新制"),
        start,
        "上下级机构",
        i,
        origin,
        "元丰新制中书省增建中书后省。",
        "职源",
    )
    rel(
        w,
        ft(w, fe(w, "中书门下省", "机构"), "南宋建炎三年四月二十九日"),
        south,
        "上下级机构",
        i,
        south_intro,
        "建炎三年中书后省复置于合并后的中书门下省体系。",
        "编制",
    )
    w.commit()


def entry785_officials():
    i = 785
    north_staff = Q(
        i,
        "①元丰新制，官额：右散骑常侍、右谏议大夫、右司谏、右正言各一员，"
        "中书舍人六员，起居舍人一员。以中书舍人判后省事。",
        "编制",
    )
    south_staff = Q(
        i,
        "②建炎三年复置，以中书舍人为长官，常除二员，余官同元丰之制。",
        "编制",
    )
    w = W(i)
    back_e = fe(w, "中书后省", "机构")
    north = ft(w, back_e, "北宋元丰四年十月")
    south = ft(w, back_e, "南宋建炎三年")

    north_specs = (
        ("右散骑常侍", "北宋元丰新制（中书省）", 1),
        ("右谏议大夫", "北宋元丰改制后", 1),
        ("右司谏", "北宋元丰新制", 1),
        ("右正言", "北宋元丰新制", 1),
        ("中书舍人", "北宋元丰新制（中书省）", 6),
        ("起居舍人", "北宋元丰五年五月", 1),
    )
    for title, time, quota in north_specs:
        rel(
            w,
            north,
            ft(w, fe(w, title, "官职"), time),
            "编制隶属",
            i,
            north_staff,
            f"元丰新制中书后省{title}{quota}人。",
            "编制",
            staff_quota=quota,
            staff_type="官",
        )

    right_attendant_e = fe(w, "右散骑常侍", "官职")
    right_attendant_south = tp(
        w,
        right_attendant_e,
        "南宋建炎三年（中书后省）",
        "中书后省复置后沿元丰官制设一人",
        i,
        south_staff,
        "职事官",
        "建右散骑常侍在南宋中书后省的编制节点。",
        "编制",
        chain="none",
    )
    chain_all(
        w,
        right_attendant_e,
        [
            ft(w, right_attendant_e, "宋代（未载具体年月）"),
            ft(w, right_attendant_e, "北宋元丰新制（中书省）"),
            right_attendant_south,
        ],
        "把南宋中书后省节点接入右散骑常侍时间链。",
    )
    diarist_e = fe(w, "起居舍人", "官职")
    diarist_south = tp(
        w,
        diarist_e,
        "南宋建炎三年（中书后省）",
        "中书后省复置后沿元丰官制设一人",
        i,
        south_staff,
        "职事官",
        "建起居舍人在南宋中书后省的编制节点。",
        "编制",
        chain="none",
    )
    chain_all(
        w,
        diarist_e,
        [
            ft(w, diarist_e, "宋初"),
            ft(w, diarist_e, "北宋元丰五年五月"),
            diarist_south,
        ],
        "把南宋中书后省节点接入起居舍人时间链。",
    )
    south_specs = (
        ("右散骑常侍", right_attendant_south, 1),
        ("右谏议大夫", ft(w, fe(w, "右谏议大夫", "官职"), "南宋"), 1),
        ("右司谏", ft(w, fe(w, "右司谏", "官职"), "南宋"), 1),
        ("右正言", ft(w, fe(w, "右正言", "官职"), "南宋"), 1),
        (
            "中书舍人",
            ft(w, fe(w, "中书舍人", "官职"), "南宋（未载具体年月）"),
            2,
        ),
        ("起居舍人", diarist_south, 1),
    )
    for title, target, quota in south_specs:
        rel(
            w,
            south,
            target,
            "编制隶属",
            i,
            south_staff,
            f"建炎三年中书后省复置，{title}{quota}人。",
            "编制",
            staff_quota=quota,
            staff_type="官",
        )
    w.commit()


def entry785_cases():
    i = 785
    north_cases = Q(
        i,
        "设案五：上案、下案、制诰、谏官、记注。",
        "编制",
    )
    south_cases = Q(
        i,
        "设案四：上案、下案、制诰、记注案。",
        "编制",
    )
    w = W(i)
    back_e = fe(w, "中书后省", "机构")
    north = ft(w, back_e, "北宋元丰四年十月")
    south = ft(w, back_e, "南宋建炎三年")
    titles = (
        "中书后省上案",
        "中书后省下案",
        "中书后省制诰案",
        "中书后省谏官案",
        "中书后省记注案",
    )
    for title in titles:
        eid = en(w, title, "机构", north_cases, f"元丰中书后省五案编制明载{title}。")
        north_t = tp(
            w,
            eid,
            "北宋元丰四年十月（中书后省）",
            "中书后省五个常设办事案之一",
            i,
            north_cases,
            "中央政务办事部门",
            f"建{title}元丰始置节点。",
            "编制",
            chain="none",
        )
        rel(
            w,
            north,
            north_t,
            "上下级机构",
            i,
            north_cases,
            f"元丰中书后省设{title}。",
            "编制",
        )
        if title == "中书后省谏官案":
            end_t = tp(
                w,
                eid,
                "南宋建炎三年",
                "复置中书后省时不列入四案编制",
                i,
                south_cases,
                "中央政务办事部门",
                "建谏官案未列入南宋四案编制的终点。",
                "编制",
                chain="none",
            )
            chain_all(w, eid, [north_t, end_t], "连接谏官案元丰设置与建炎未复置节点。")
        else:
            south_t = tp(
                w,
                eid,
                "南宋建炎三年（中书后省）",
                "中书后省复置后的四个常设办事案之一",
                i,
                south_cases,
                "中央政务办事部门",
                f"建{title}南宋复置节点。",
                "编制",
                chain="none",
            )
            chain_all(w, eid, [north_t, south_t], f"连接{title}元丰与建炎复置节点。")
            rel(
                w,
                south,
                south_t,
                "上下级机构",
                i,
                south_cases,
                f"建炎三年中书后省复置{title}。",
                "编制",
            )
    w.commit()


def entry785_clerks():
    i = 785
    clerks = Q(
        i,
        "吏额十人：点检一、令史二、守当官五",
        "编制",
    )
    w = W(i)
    back_south = ft(w, fe(w, "中书后省", "机构"), "南宋建炎三年")
    checker_e = en(w, "点检", "官职", clerks, "中书后省吏额明载点检一人。")
    checker_t = tp(
        w,
        checker_e,
        "南宋建炎三年（中书后省）",
        "中书后省点检一人",
        i,
        clerks,
        "吏",
        "建中书后省点检编制节点。",
        "编制",
        chain="none",
    )
    rel(
        w,
        back_south,
        checker_t,
        "编制隶属",
        i,
        clerks,
        "建炎三年中书后省点检一人。",
        "编制",
        staff_quota=1,
        staff_type="吏",
    )

    clerk_e = fe(w, "令史", "官职")
    clerk_t = tp(
        w,
        clerk_e,
        "南宋建炎三年（中书后省）",
        "中书后省令史二人",
        i,
        clerks,
        "吏",
        "建令史在南宋中书后省的编制节点。",
        "编制",
        chain="none",
    )
    chain_all(
        w,
        clerk_e,
        [
            ft(w, clerk_e, "汉至唐"),
            ft(w, clerk_e, "宋代（枢密院，未载具体年月）"),
            ft(w, clerk_e, "北宋（登闻检院，未载具体年月）"),
            ft(w, clerk_e, "北宋（登闻鼓院，未载具体年月）"),
            ft(w, clerk_e, "北宋元丰新制（门下省）"),
            ft(w, clerk_e, "北宋元丰新制（中书省）"),
            clerk_t,
            ft(w, clerk_e, "南宋嘉定五年"),
        ],
        "把南宋中书后省节点接入令史全局时间链。",
    )
    rel(
        w,
        back_south,
        clerk_t,
        "编制隶属",
        i,
        clerks,
        "建炎三年中书后省令史二人。",
        "编制",
        staff_quota=2,
        staff_type="吏",
    )

    keeper_e = fe(w, "守当官", "官职")
    keeper_t = tp(
        w,
        keeper_e,
        "南宋建炎三年（中书后省）",
        "中书后省守当官五人",
        i,
        clerks,
        "吏",
        "建守当官在南宋中书后省的编制节点。",
        "编制",
        chain="none",
    )
    chain_all(
        w,
        keeper_e,
        [
            ft(w, keeper_e, "宋前期"),
            ft(w, keeper_e, "北宋熙宁三年十一月"),
            ft(w, keeper_e, "北宋元丰新制（门下省）"),
            ft(w, keeper_e, "北宋元丰新制（中书省）"),
            ft(w, keeper_e, "南宋初（登闻检院）"),
            ft(w, keeper_e, "南宋（登闻鼓院）"),
            keeper_t,
            ft(w, keeper_e, "南宋嘉定五年"),
        ],
        "把南宋中书后省节点接入守当官全局时间链。",
    )
    rel(
        w,
        back_south,
        keeper_t,
        "编制隶属",
        i,
        clerks,
        "建炎三年中书后省守当官五人。",
        "编制",
        staff_quota=5,
        staff_type="吏",
    )
    w.commit()


def refine_case(i, title, event, has_south=True):
    main = Q(i, F[i]["text"])
    w = W(i)
    entity_id = fe(w, title, "机构")
    north_t = refine(
        w,
        ft(w, entity_id, "北宋元丰四年十月（中书后省）"),
        i,
        main,
        f"专条细化{title}职掌。",
        event=event,
        category="中央政务办事部门",
    )
    rid = relation_id(
        w,
        "中书后省",
        title,
        "上下级机构",
        "北宋元丰四年十月",
        "北宋元丰四年十月（中书后省）",
    )
    assert rid
    cite(w, "Relationships", rid, i, main, f"专条补证{title}隶中书后省。")
    if has_south:
        cite(
            w,
            "Timepoints",
            ft(w, entity_id, "南宋建炎三年（中书后省）"),
            i,
            main,
            f"专条职掌沿用于建炎复置后的{title}。",
        )
    w.commit()


def entry786_790():
    specs = (
        (
            786,
            "中书后省上案",
            "掌王公、后妃、大臣册命礼及大朝会文书准备",
            True,
        ),
        (787, "中书后省下案", "掌收发中书后省五案文书", True),
        (
            788,
            "中书后省制诰案",
            "掌抄写中书舍人草拟制词及中书省人吏考试补迁",
            True,
        ),
        (
            789,
            "中书后省谏官案",
            "掌收受朝廷诸司报送中书后省文书",
            False,
        ),
        (
            790,
            "中书后省记注案",
            "掌抄写起居舍人所记皇帝、大臣、侍从朝廷议论的起居注",
            True,
        ),
    )
    for spec in specs:
        refine_case(*spec)


def main():
    repair_entry775_name()
    entry771_778()
    entry779()
    entry780()
    entry781()
    entry782()
    entry783()
    entry784()
    entry785_core()
    entry785_officials()
    entry785_cases()
    entry785_clerks()
    entry786_790()


if __name__ == "__main__":
    main()
