#!/usr/bin/env python3
"""提取 chapter2t4 第751–770条：登闻鼓院系统与中书省主条、吏户二房。"""
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


F = {i: load(i) for i in range(751, 771)}


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


def entry751():
    i = 751
    main = Q(i, "吏名。隶登闻检院。抄写文书。南宋已不复置")
    w = W(i)
    entity_id = fe(w, "书写人", "官职")
    discontinued = tp(
        w,
        entity_id,
        "南宋（登闻检院）",
        "登闻检院不再设置书写人",
        i,
        main,
        "吏",
        "建书写人在南宋登闻检院不复置的制度节点。",
        chain="none",
    )
    chain_all(
        w,
        entity_id,
        [
            ft(w, entity_id, "北宋咸平四年九月（都进奏院）"),
            ft(w, entity_id, "北宋（登闻检院，未载具体年月）"),
            ft(w, entity_id, "南宋初（都进奏院）"),
            discontinued,
            ft(w, entity_id, "南宋淳熙十五年"),
        ],
        "把南宋登闻检院不复置节点接入书写人全局时间链。",
    )
    rid = relation_id(
        w,
        "登闻检院",
        "书写人",
        "编制隶属",
        "北宋（未载具体年月）",
        "北宋（登闻检院，未载具体年月）",
    )
    assert rid
    cite(
        w,
        "Relationships",
        rid,
        i,
        main,
        "本条补证书写人原隶登闻检院，并明确南宋不复置。",
    )
    w.commit()


def entry752():
    i = 752
    origin = Q(
        i,
        "宋初见置。《职源摄要》：“登闻鼓院，国初曰鼓司。”"
        "景德四年五月，改鼓司为登闻鼓院",
        "职源与沿革",
    )
    duty = Q(
        i,
        "凡文武臣僚不得由阁门通进朝廷、皇帝文字者，或臣民有冤申诉者，"
        "可击鼓往鼓司投状、投书。不先经鼓司投状，瓯院不予收接",
        "职掌",
    )
    staff = Q(i, "勾当鼓司公事二员", "编制")
    w = W(i)
    entity_id = en(w, "鼓司", "机构", origin, "本条明确鼓司为官署。")
    start = tp(
        w,
        entity_id,
        "宋初",
        "设置鼓司，受理臣民击鼓投状、投书",
        i,
        origin,
        "中央申诉受理机构",
        "建鼓司宋初始置节点。",
        "职源与沿革",
        chain="none",
    )
    cite(w, "Timepoints", start, i, duty, "补证鼓司受理击鼓投状的职掌。", "职掌")
    change = tp(
        w,
        entity_id,
        "北宋至道三年五月",
        "勾当鼓司公事改由文官朝臣充任",
        i,
        staff,
        "中央申诉受理机构",
        "为勾当官任用变化补建鼓司机构节点。",
        "编制",
        chain="none",
    )
    end = tp(
        w,
        entity_id,
        "北宋景德四年五月",
        "改名登闻鼓院",
        i,
        origin,
        "中央申诉受理机构",
        "建鼓司景德四年改名终点。",
        "职源与沿革",
        chain="none",
    )
    chain_all(w, entity_id, [start, change, end], "连接鼓司宋初、至道与景德改名节点。")
    w.commit()


def entry753():
    i = 753
    main = Q(
        i,
        "差遣官名。至道三年五月（真宗已登位）前，由宦官充，以后，"
        "始差文官朝臣充。掌鼓司事",
    )
    w = W(i)
    entity_id = en(w, "勾当鼓司公事", "官职", main, "本条明确为差遣官名。")
    early = tp(
        w,
        entity_id,
        "北宋至道三年五月以前",
        "掌鼓司事，由宦官充",
        i,
        main,
        "差遣官",
        "建勾当鼓司公事早期任用节点。",
        attr_officer_type="宦官",
        chain="none",
    )
    later = tp(
        w,
        entity_id,
        "北宋至道三年五月以后",
        "改差文官朝臣充，掌鼓司事",
        i,
        main,
        "差遣官",
        "建至道三年以后任用变化节点。",
        attr_officer_type="文官朝臣",
        chain="none",
    )
    chain_all(w, entity_id, [early, later], "连接勾当鼓司公事任用变化节点。")
    institute_e = fe(w, "鼓司", "机构")
    rel(
        w,
        ft(w, institute_e, "宋初"),
        early,
        "编制隶属",
        i,
        main,
        "勾当鼓司公事早期由宦官充，掌鼓司事；编制条明载二员。",
        staff_quota=2,
        staff_type="官",
    )
    rel(
        w,
        ft(w, institute_e, "北宋至道三年五月"),
        later,
        "编制隶属",
        i,
        main,
        "至道三年五月以后勾当鼓司公事改由文官朝臣充。",
        staff_quota=2,
        staff_type="官",
    )
    w.commit()


def entry754_note():
    i = 754
    main = Q(
        i,
        "鼓司设鼓，在宣德门外南街北廊。使有冤屈者诣阙而诉，"
        "得以挝鼓而达闻于上。",
    )
    w = W(i)
    cite(
        w,
        "Timepoints",
        ft(w, fe(w, "鼓司", "机构"), "宋初"),
        i,
        main,
        "鼓条补证鼓司击鼓申诉设施与位置；鼓为物件，不另建实体。",
    )
    w.commit()


def entry755_core():
    i = 755
    origin = Q(
        i,
        "宋初设鼓司。景德四年（1007）五月改鼓司为登闻鼓院",
        "职源与沿革",
    )
    north_duty = Q(
        i,
        "①北宋时与鼓司同。凡四方官吏、士民冤枉上封事、书牍等，"
        "通受而奏之于朝，以通万民之情",
        "职掌",
    )
    south_duty = Q(
        i,
        "②南宋时，与登闻检院职事上有分工。登闻鼓院掌有关大礼奏荐、"
        "敕断及致仕遗表等已得旨恩泽，试换文资，改正过名，陈乞再任等申诉事。",
        "职掌",
    )
    south_staff = Q(
        i,
        "②南宋时，隶谏院。监登闻鼓院一人，手分二人，书写人一人。"
        "看鼓一人，下夫一人",
        "编制",
    )
    w = W(i)
    entity_id = en(w, "登闻鼓院", "机构", origin, "本条明确登闻鼓院为官署。")
    start = tp(
        w,
        entity_id,
        "北宋景德四年五月",
        "由鼓司改名，受理臣民冤枉上封事、书牍",
        i,
        origin,
        "中央申诉受理机构",
        "建登闻鼓院景德四年始置节点。",
        "职源与沿革",
        chain="none",
    )
    north = tp(
        w,
        entity_id,
        "北宋（未载具体年月）",
        "通受官吏、士民冤枉上封事、书牍并奏朝廷；鼓院不行可赴检院",
        i,
        north_duty,
        "中央申诉受理机构",
        "建登闻鼓院北宋职掌节点。",
        "职掌",
        chain="none",
    )
    south = tp(
        w,
        entity_id,
        "南宋（未载具体年月）",
        "与登闻检院按职事分工，受理恩泽、换资、改名、再任等申诉",
        i,
        south_duty,
        "中央申诉受理机构",
        "建登闻鼓院南宋职掌变化节点。",
        "职掌",
        chain="none",
    )
    cite(w, "Timepoints", south, i, south_staff, "补证南宋隶谏院及编制。", "编制")
    chain_all(w, entity_id, [start, north, south], "连接登闻鼓院始置、北宋与南宋节点。")
    rel(
        w,
        ft(w, fe(w, "鼓司", "机构"), "北宋景德四年五月"),
        start,
        "前后演变",
        i,
        origin,
        "景德四年五月鼓司改名登闻鼓院。",
        "职源与沿革",
    )
    rel(
        w,
        ft(w, fe(w, "谏院", "机构"), "南宋"),
        south,
        "上下级机构",
        i,
        south_staff,
        "编制字段明载南宋登闻鼓院隶谏院。",
        "编制",
    )
    w.commit()


def entry757():
    i = 757
    main = Q(i, "宋前期差遣官名，元丰改制后职事官名。")
    origin = Q(
        i,
        "景德四年五月，与改鼓司为登闻鼓院同步，设判院官二人",
        "职源",
    )
    duty = Q(i, "领登闻鼓院事。", "职掌")
    w = W(i)
    entity_id = en(w, "判登闻鼓院事", "官职", main, "本条明确为差遣、职事官名。")
    start = tp(
        w,
        entity_id,
        "北宋景德四年五月",
        "随登闻鼓院始置，设二人，领院事",
        i,
        origin,
        "差遣官",
        "建判登闻鼓院事景德始置节点。",
        "职源",
        chain="none",
    )
    cite(w, "Timepoints", start, i, duty, "补证判登闻鼓院事职掌。", "职掌")
    reform = tp(
        w,
        entity_id,
        "北宋元丰新制后",
        "由差遣官改为职事官",
        i,
        main,
        "职事官",
        "建元丰改制后的官制变化节点。",
        chain="none",
    )
    chain_all(w, entity_id, [start, reform], "连接判登闻鼓院事始置与元丰改制节点。")
    rel(
        w,
        ft(w, fe(w, "登闻鼓院", "机构"), "北宋景德四年五月"),
        start,
        "编制隶属",
        i,
        origin,
        "景德四年登闻鼓院始设判院官二人。",
        "职源",
        staff_quota=2,
        staff_type="官",
    )
    w.commit()


def entry758():
    i = 758
    main = Q(
        i,
        "登闻鼓院置判院官二人，资浅者一员为同判。如景德四年，"
        "周起以右正言判登闻鼓院，路振同判登闻鼓院事",
    )
    w = W(i)
    entity_id = en(w, "同判登闻鼓院事", "官职", main, "本条明确为判院官中资浅一员。")
    officer_t = tp(
        w,
        entity_id,
        "北宋景德四年",
        "判院官二人中资浅一员称同判",
        i,
        main,
        "差遣官",
        "建同判登闻鼓院事景德可考节点。",
        chain="none",
    )
    rel(
        w,
        ft(w, fe(w, "登闻鼓院", "机构"), "北宋（未载具体年月）"),
        officer_t,
        "编制隶属",
        i,
        main,
        "同判为登闻鼓院二名判院官中资浅一员，额内一人。",
        staff_quota=1,
        staff_type="官（判院官二人额内）",
    )
    w.commit()


def entry759():
    i = 759
    main = Q(i, "南宋初，改判登闻鼓院事为监登闻鼓院。")
    w = W(i)
    source_e = fe(w, "判登闻鼓院事", "官职")
    source_end = tp(
        w,
        source_e,
        "南宋初",
        "改称监登闻鼓院",
        i,
        main,
        "职事官",
        "建判登闻鼓院事南宋初改称终点。",
        chain="none",
    )
    chain_all(
        w,
        source_e,
        [
            ft(w, source_e, "北宋景德四年五月"),
            ft(w, source_e, "北宋元丰新制后"),
            source_end,
        ],
        "把南宋初改称节点接入判登闻鼓院事时间链。",
    )
    target_e = en(w, "监登闻鼓院", "官职", main, "本条明确南宋初改置监登闻鼓院。")
    target_t = tp(
        w,
        target_e,
        "南宋初",
        "由判登闻鼓院事改称",
        i,
        main,
        "职事官",
        "建监登闻鼓院南宋初始置节点。",
        chain="none",
    )
    rel(
        w,
        source_end,
        target_t,
        "前后演变",
        i,
        main,
        "南宋初判登闻鼓院事改称监登闻鼓院。",
    )
    institute_e = fe(w, "登闻鼓院", "机构")
    institute_south_early = tp(
        w,
        institute_e,
        "南宋初",
        "判院官改称监院官",
        i,
        main,
        "中央申诉受理机构",
        "为南宋初主官改称补建机构节点。",
        chain="none",
    )
    chain_all(
        w,
        institute_e,
        [
            ft(w, institute_e, "北宋景德四年五月"),
            ft(w, institute_e, "北宋（未载具体年月）"),
            institute_south_early,
            ft(w, institute_e, "南宋（未载具体年月）"),
        ],
        "把南宋初主官改称节点接入登闻鼓院时间链。",
    )
    w.commit()


def entry761():
    i = 761
    main = Q(
        i,
        "职事官名，由宦官充。北宋时一人。南宋时，鼓院与检院监门官"
        "许差一员互权",
    )
    w = W(i)
    entity_id = en(w, "监登闻鼓院门", "官职", main, "本条明确为职事官名。")
    north = tp(
        w,
        entity_id,
        "北宋",
        "由宦官充，监守登闻鼓院门，设一人",
        i,
        main,
        "职事官",
        "建监登闻鼓院门北宋节点。",
        attr_officer_type="宦官",
        chain="none",
    )
    south = tp(
        w,
        entity_id,
        "南宋",
        "与监登闻检院门官可差一员互相权摄",
        i,
        main,
        "职事官",
        "建南宋鼓院、检院监门官互权节点。",
        attr_officer_type="宦官",
        chain="none",
    )
    chain_all(w, entity_id, [north, south], "连接监登闻鼓院门北宋、南宋节点。")
    w.commit()


def entry762():
    i = 762
    main = Q(i, "北宋差遣官，由内侍官充。掌监守登门鼓")
    w = W(i)
    entity_id = en(w, "监鼓", "官职", main, "本条明确为北宋差遣官。")
    tp(
        w,
        entity_id,
        "北宋",
        "由内侍官充，监守登闻鼓",
        i,
        main,
        "差遣官",
        "建监鼓北宋职掌节点；事件文字按官制语义校正 OCR“登门鼓”。",
        attr_officer_type="内侍官",
        chain="none",
    )
    w.commit()


def entry763():
    i = 763
    main = Q(i, "吏名。隶登闻鼓院。职掌监本院印及管本院事务")
    w = W(i)
    entity_id = fe(w, "令史", "官职")
    north = tp(
        w,
        entity_id,
        "北宋（登闻鼓院，未载具体年月）",
        "监登闻鼓院印并管本院事务",
        i,
        main,
        "吏",
        "建令史在登闻鼓院的北宋职役节点。",
        chain="none",
    )
    chain_all(
        w,
        entity_id,
        [
            ft(w, entity_id, "汉至唐"),
            ft(w, entity_id, "宋代（枢密院，未载具体年月）"),
            ft(w, entity_id, "北宋（登闻检院，未载具体年月）"),
            north,
            ft(w, entity_id, "北宋元丰新制（门下省）"),
            ft(w, entity_id, "南宋嘉定五年"),
        ],
        "把登闻鼓院令史节点接入令史全局时间链。",
    )
    w.commit()


def entry764():
    i = 764
    main = Q(
        i,
        "吏名。隶登闻鼓院。为书令史、守当官等文书吏总名，"
        "掌本院文书行遣事",
    )
    w = W(i)
    hand_e = fe(w, "手分", "官职")
    hand_t = tp(
        w,
        hand_e,
        "南宋（登闻鼓院）",
        "书令史、守当官等文书吏总名，掌本院文书行遣",
        i,
        main,
        "胥吏统称",
        "建手分在登闻鼓院的南宋职役节点。",
        chain="none",
    )
    chain_all(
        w,
        hand_e,
        [
            ft(w, hand_e, "宋代"),
            ft(w, hand_e, "南宋初（登闻检院）"),
            hand_t,
        ],
        "把登闻鼓院手分节点接入既有时间链。",
    )
    clerk_e = fe(w, "书令史", "官职")
    clerk_t = tp(
        w,
        clerk_e,
        "南宋（登闻鼓院）",
        "可充登闻鼓院手分，掌文书行遣",
        i,
        main,
        "胥吏",
        "建书令史作为登闻鼓院手分实例的同期节点。",
        chain="none",
    )
    chain_all(
        w,
        clerk_e,
        [
            ft(w, clerk_e, "汉至唐"),
            ft(w, clerk_e, "宋代（枢密院，未载具体年月）"),
            ft(w, clerk_e, "北宋淳化四年二月"),
            ft(w, clerk_e, "宋前期（通进司）"),
            ft(w, clerk_e, "北宋元丰新制（门下省）"),
            ft(w, clerk_e, "南宋初（登闻检院）"),
            clerk_t,
            ft(w, clerk_e, "南宋嘉定五年"),
        ],
        "把南宋登闻鼓院节点接入书令史全局时间链。",
    )
    keeper_e = fe(w, "守当官", "官职")
    keeper_t = tp(
        w,
        keeper_e,
        "南宋（登闻鼓院）",
        "可充登闻鼓院手分，掌文书行遣",
        i,
        main,
        "胥吏",
        "建守当官作为登闻鼓院手分实例的同期节点。",
        chain="none",
    )
    chain_all(
        w,
        keeper_e,
        [
            ft(w, keeper_e, "宋前期"),
            ft(w, keeper_e, "北宋熙宁三年十一月"),
            ft(w, keeper_e, "北宋元丰新制（门下省）"),
            ft(w, keeper_e, "南宋初（登闻检院）"),
            keeper_t,
            ft(w, keeper_e, "南宋嘉定五年"),
        ],
        "把南宋登闻鼓院节点接入守当官全局时间链。",
    )
    rel(
        w,
        hand_t,
        clerk_t,
        "统称与实例",
        i,
        main,
        "本条明载手分是书令史、守当官等文书吏总名。",
    )
    rel(
        w,
        hand_t,
        keeper_t,
        "统称与实例",
        i,
        main,
        "本条明载手分是书令史、守当官等文书吏总名。",
    )
    w.commit()


def entry765():
    i = 765
    main = Q(i, "吏名。抄写文字")
    w = W(i)
    entity_id = fe(w, "书写人", "官职")
    south = tp(
        w,
        entity_id,
        "南宋（登闻鼓院）",
        "登闻鼓院书写人，抄写文字",
        i,
        main,
        "吏",
        "建书写人在南宋登闻鼓院的职役节点。",
        chain="none",
    )
    chain_all(
        w,
        entity_id,
        [
            ft(w, entity_id, "北宋咸平四年九月（都进奏院）"),
            ft(w, entity_id, "北宋（登闻检院，未载具体年月）"),
            ft(w, entity_id, "南宋初（都进奏院）"),
            ft(w, entity_id, "南宋（登闻检院）"),
            south,
            ft(w, entity_id, "南宋淳熙十五年"),
        ],
        "把南宋登闻鼓院节点接入书写人全局时间链。",
    )
    w.commit()


def entry766():
    i = 766
    main = Q(
        i,
        "杂役名。隶登闻鼓院。由三省大程官（吏人）充。"
        "南宋建炎三年以后不置",
    )
    w = W(i)
    entity_id = en(w, "看鼓", "官职", main, "原书目录与正文明确看鼓为登闻鼓院杂役名。")
    active = tp(
        w,
        entity_id,
        "南宋建炎三年以前",
        "隶登闻鼓院，由三省大程官（吏人）充",
        i,
        main,
        "杂役",
        "建看鼓在建炎三年前的职役节点。",
        attr_officer_type="三省大程官（吏人）",
        chain="none",
    )
    end = tp(
        w,
        entity_id,
        "南宋建炎三年以后",
        "不再设置",
        i,
        main,
        "杂役",
        "建看鼓建炎三年以后不置节点。",
        chain="none",
    )
    chain_all(w, entity_id, [active, end], "连接看鼓设置与建炎三年后停置节点。")
    institute_e = fe(w, "登闻鼓院", "机构")
    institute_change = tp(
        w,
        institute_e,
        "南宋建炎三年",
        "看鼓、下夫等杂役此后不置",
        i,
        main,
        "中央申诉受理机构",
        "为看鼓停置补建登闻鼓院建炎三年节点。",
        chain="none",
    )
    chain_all(
        w,
        institute_e,
        [
            ft(w, institute_e, "北宋景德四年五月"),
            ft(w, institute_e, "北宋（未载具体年月）"),
            ft(w, institute_e, "南宋初"),
            institute_change,
            ft(w, institute_e, "南宋（未载具体年月）"),
        ],
        "把建炎三年杂役停置节点接入登闻鼓院时间链。",
    )
    rel(
        w,
        ft(w, institute_e, "南宋初"),
        active,
        "编制隶属",
        i,
        main,
        "看鼓在建炎三年前隶登闻鼓院，由三省大程官充。",
        staff_quota=1,
        staff_type="杂役",
    )
    w.commit()


def entry767():
    i = 767
    main = Q(i, "杂役名。由大程官充。南宋建炎三年后不置")
    w = W(i)
    entity_id = en(w, "下夫", "官职", main, "本条明确为杂役名。")
    active = tp(
        w,
        entity_id,
        "南宋建炎三年以前",
        "登闻鼓院杂役，由大程官充",
        i,
        main,
        "杂役",
        "建下夫在建炎三年前的职役节点。",
        attr_officer_type="大程官",
        chain="none",
    )
    end = tp(
        w,
        entity_id,
        "南宋建炎三年以后",
        "不再设置",
        i,
        main,
        "杂役",
        "建下夫建炎三年以后不置节点。",
        chain="none",
    )
    chain_all(w, entity_id, [active, end], "连接下夫设置与建炎三年后停置节点。")
    rel(
        w,
        ft(w, fe(w, "登闻鼓院", "机构"), "南宋初"),
        active,
        "编制隶属",
        i,
        main,
        "下夫在建炎三年前为登闻鼓院杂役，由大程官充。",
        staff_quota=1,
        staff_type="杂役",
    )
    w.commit()


def entry755_staff():
    i = 755
    north_staff = Q(
        i,
        "①北宋时隶司谏、正言。判登闻鼓院事二人，监登闻鼓院门一人，"
        "监鼓二人，令史二人。",
        "编制",
    )
    south_staff = Q(
        i,
        "②南宋时，隶谏院。监登闻鼓院一人，手分二人，书写人一人。"
        "看鼓一人，下夫一人",
        "编制",
    )
    w = W(i)
    institute_e = fe(w, "登闻鼓院", "机构")
    north = ft(w, institute_e, "北宋（未载具体年月）")
    south = ft(w, institute_e, "南宋（未载具体年月）")
    for target, quota, staff_type, label in (
        (
            ft(w, fe(w, "判登闻鼓院事", "官职"), "北宋景德四年五月"),
            2,
            "官",
            "判登闻鼓院事二人",
        ),
        (
            ft(w, fe(w, "监登闻鼓院门", "官职"), "北宋"),
            1,
            "宦官",
            "监登闻鼓院门一人",
        ),
        (ft(w, fe(w, "监鼓", "官职"), "北宋"), 2, "内侍官", "监鼓二人"),
        (
            ft(w, fe(w, "令史", "官职"), "北宋（登闻鼓院，未载具体年月）"),
            2,
            "吏",
            "令史二人",
        ),
    ):
        rel(
            w,
            north,
            target,
            "编制隶属",
            i,
            north_staff,
            f"北宋登闻鼓院编制：{label}。",
            "编制",
            staff_quota=quota,
            staff_type=staff_type,
        )
    for target, quota, staff_type, label in (
        (
            ft(w, fe(w, "监登闻鼓院", "官职"), "南宋初"),
            1,
            "官",
            "监登闻鼓院一人",
        ),
        (
            ft(w, fe(w, "手分", "官职"), "南宋（登闻鼓院）"),
            2,
            "吏",
            "手分二人",
        ),
        (
            ft(w, fe(w, "书写人", "官职"), "南宋（登闻鼓院）"),
            1,
            "吏",
            "书写人一人",
        ),
        (
            ft(w, fe(w, "看鼓", "官职"), "南宋建炎三年以前"),
            1,
            "杂役",
            "看鼓一人（建炎三年后不置）",
        ),
        (
            ft(w, fe(w, "下夫", "官职"), "南宋建炎三年以前"),
            1,
            "杂役",
            "下夫一人（建炎三年后不置）",
        ),
    ):
        subject = (
            ft(w, institute_e, "南宋初")
            if label.startswith(("看鼓", "下夫"))
            else south
        )
        rel(
            w,
            subject,
            target,
            "编制隶属",
            i,
            south_staff,
            f"南宋登闻鼓院编制：{label}。",
            "编制",
            staff_quota=quota,
            staff_type=staff_type,
        )
    w.commit()


def entry768_core():
    i = 768
    origin = Q(
        i,
        "魏黄初元年（220），改秘书省为中书省，此为中书省名之始",
        "职源",
    )
    early_duty = Q(
        i,
        "① 宋前期，为皇城外挂牌机构。仅掌郊祀大礼册文祝辞、皇帝死后的谥号册，"
        "本省所属玉册院等诸司吏人及祠祭官斋郎、室长等任满迁转或出职的奏请，"
        "幕职州县官考核，文官换赐官服，佛寺、道观取名赐额之类琐事",
        "职掌",
    )
    yuan_duty = Q(
        i,
        "② 元丰新制，为中央造令、传旨的政务机构。"
        "《玉海》卷121《元丰三省》：“事不以大小，并中书取旨、门下覆奏、尚书施行。”",
        "职掌",
    )
    merger = Q(
        i,
        "③南宋建炎三年（1129）四月二十九日，中书省与门下省合并为中书门下省。"
        "吏额八十九人：中书省四十三与门下省四十六相合。"
        "此外守阙守当官（候补吏人）一百五十人",
        "编制",
    )
    w = W(i)
    entity_id = fe(w, "中书省", "机构")
    pre_song = tp(
        w,
        entity_id,
        "魏黄初元年",
        "由秘书省改名，中书省之名始见",
        i,
        origin,
        "中央政务机构",
        "建中书省魏黄初元年名源节点。",
        "职源",
        chain="none",
    )
    early = refine(
        w,
        ft(w, entity_id, "北宋元丰改制前"),
        i,
        early_duty,
        "主条细化宋前期中书省仅为皇城外挂牌机构的职掌。",
        "职掌",
        event="皇城外挂牌机构，仅掌册文祝辞、谥号册、吏人迁转等琐事",
        category="中央名义机构",
    )
    yuan = refine(
        w,
        ft(w, entity_id, "北宋元丰新制"),
        i,
        yuan_duty,
        "主条细化元丰新制中书省造令、传旨职掌。",
        "职掌",
        event="中央造令、传旨并掌堂除的政务机构",
        category="中央政务机构",
    )
    end = tp(
        w,
        entity_id,
        "南宋建炎三年四月二十九日",
        "与门下省合并为中书门下省",
        i,
        merger,
        "中央政务机构",
        "建中书省建炎三年合省终点。",
        "编制",
        chain="none",
    )
    chain_all(
        w,
        entity_id,
        [
            pre_song,
            ft(w, entity_id, "北宋建隆三年前"),
            early,
            yuan,
            ft(w, entity_id, "北宋元祐元年十一月"),
            end,
        ],
        "把魏代名源与建炎合省节点接入中书省全局时间链。",
    )

    menxia_e = fe(w, "门下省", "机构")
    menxia_end = refine(
        w,
        ft(w, menxia_e, "南宋建炎三年四月"),
        i,
        merger,
        "主条给出门下、中书合省的确切日期。",
        "编制",
        time="南宋建炎三年四月二十九日",
        event="与中书省合并为中书门下省",
        category="中央审令机构",
    )
    target_e = en(w, "中书门下省", "机构", merger, "本条明确建炎三年两省合并后的机构名。")
    target_t = tp(
        w,
        target_e,
        "南宋建炎三年四月二十九日",
        "由中书省、门下省合并，吏额八十九人",
        i,
        merger,
        "中央政务机构",
        "建中书门下省合并始置节点。",
        "编制",
        chain="none",
    )
    rel(
        w,
        end,
        target_t,
        "前后演变",
        i,
        merger,
        "建炎三年中书省并入中书门下省。",
        "编制",
    )
    rel(
        w,
        menxia_end,
        target_t,
        "前后演变",
        i,
        merger,
        "建炎三年门下省并入中书门下省。",
        "编制",
    )
    w.commit()


def entry768_early_staff():
    i = 768
    duty = Q(i, "本省所属玉册院等诸司吏人", "职掌")
    staff = Q(
        i,
        "① 宋前期，判中书省事一人；吏额十五人：白院令史六人、"
        "甲库令史二人、驱使官三人，玉册院玉册官一人、刻字官一人、"
        "金字官一人、彩画官一人",
        "编制",
    )
    w = W(i)
    institute_e = fe(w, "中书省", "机构")
    institute_t = ft(w, institute_e, "北宋元丰改制前")

    judge_e = en(w, "判中书省事", "官职", staff, "宋前期中书省编制明载判省事一人。")
    judge_t = tp(
        w,
        judge_e,
        "宋前期",
        "主管皇城外中书省，设一人",
        i,
        staff,
        "差遣官",
        "建判中书省事宋前期编制节点。",
        "编制",
        chain="none",
    )
    rel(
        w,
        institute_t,
        judge_t,
        "编制隶属",
        i,
        staff,
        "宋前期中书省判省事一人。",
        "编制",
        staff_quota=1,
        staff_type="官",
    )

    for title, quota, event, existing_times in (
        (
            "白院令史",
            6,
            "中书省白院令史，设六人",
            ["宋前期（门下省）"],
        ),
        (
            "甲库令史",
            2,
            "中书省甲库令史，设二人",
            ["宋前期（门下省）"],
        ),
        (
            "驱使官",
            3,
            "中书省驱使官，设三人",
            ["宋前期"],
        ),
    ):
        eid = fe(w, title, "官职")
        tid = tp(
            w,
            eid,
            "宋前期（中书省）",
            event,
            i,
            staff,
            "吏",
            f"建{title}在宋前期中书省的编制节点。",
            "编制",
            chain="none",
        )
        chain_all(
            w,
            eid,
            [ft(w, eid, time) for time in existing_times] + [tid],
            f"把中书省节点接入{title}全局时间链。",
        )
        rel(
            w,
            institute_t,
            tid,
            "编制隶属",
            i,
            staff,
            f"宋前期中书省{title}{quota}人。",
            "编制",
            staff_quota=quota,
            staff_type="吏",
        )

    jade_e = en(w, "玉册院", "机构", duty, "职掌字段明确玉册院为中书省所属诸司。")
    jade_t = tp(
        w,
        jade_e,
        "宋前期",
        "中书省所属机构，承办玉册制作",
        i,
        staff,
        "册宝制作机构",
        "建玉册院宋前期节点。",
        "编制",
        chain="none",
    )
    rel(
        w,
        institute_t,
        jade_t,
        "上下级机构",
        i,
        duty,
        "职掌字段明载玉册院为中书省所属机构。",
        "职掌",
    )
    for title in ("玉册官", "刻字官", "金字官", "彩画官"):
        eid = en(w, title, "官职", staff, f"宋前期玉册院编制明载{title}一人。")
        tid = tp(
            w,
            eid,
            "宋前期（玉册院）",
            f"玉册院{title}，设一人",
            i,
            staff,
            "技术吏职",
            f"建{title}宋前期编制节点。",
            "编制",
            chain="none",
        )
        rel(
            w,
            jade_t,
            tid,
            "编制隶属",
            i,
            staff,
            f"玉册院{title}一人。",
            "编制",
            staff_quota=1,
            staff_type="吏",
        )
    w.commit()


def entry768_yuanfeng_officials():
    i = 768
    staff = Q(
        i,
        "②元丰新制，官额十一：中书令、中书侍郎、右散骑常侍各一人，"
        "中书舍人四人，右谏议大夫、起居舍人、右司谏、右正言各一人。",
        "编制",
    )
    w = W(i)
    institute_t = ft(w, fe(w, "中书省", "机构"), "北宋元丰新制")

    zhongshu_ling_e = fe(w, "中书令", "官职")
    zhongshu_ling_t = tp(
        w,
        zhongshu_ling_e,
        "北宋元丰新制（中书省）",
        "中书省官额之一，设一人",
        i,
        staff,
        "职事官",
        "建中书令在元丰中书省的编制节点。",
        "编制",
        chain="none",
    )
    chain_all(
        w,
        zhongshu_ling_e,
        [
            ft(w, zhongshu_ling_e, "宋代（未载具体年月）"),
            zhongshu_ling_t,
            ft(w, zhongshu_ling_e, "南宋乾道八年二月"),
        ],
        "把元丰中书省节点接入中书令全局时间链。",
    )

    right_attendant_e = fe(w, "右散骑常侍", "官职")
    right_attendant_t = tp(
        w,
        right_attendant_e,
        "北宋元丰新制（中书省）",
        "中书省官额之一，设一人",
        i,
        staff,
        "职事官",
        "建右散骑常侍在元丰中书省的编制节点。",
        "编制",
        chain="none",
    )
    chain_all(
        w,
        right_attendant_e,
        [
            ft(w, right_attendant_e, "宋代（未载具体年月）"),
            right_attendant_t,
        ],
        "把元丰中书省节点接入右散骑常侍时间链。",
    )

    drafter_e = fe(w, "中书舍人", "官职")
    drafter_t = tp(
        w,
        drafter_e,
        "北宋元丰新制（中书省）",
        "中书省官额四人，掌制命",
        i,
        staff,
        "职事官",
        "建中书舍人在元丰中书省的编制节点。",
        "编制",
        chain="none",
    )
    chain_all(
        w,
        drafter_e,
        [
            ft(w, drafter_e, "宋前期"),
            ft(w, drafter_e, "北宋天禧元年八月"),
            drafter_t,
            ft(w, drafter_e, "南宋（未载具体年月）"),
        ],
        "把元丰中书省节点接入中书舍人全局时间链。",
    )

    endpoints = (
        ("中书令", zhongshu_ling_t, 1),
        (
            "中书侍郎",
            ft(w, fe(w, "中书侍郎", "官职"), "北宋元丰新制"),
            1,
        ),
        ("右散骑常侍", right_attendant_t, 1),
        ("中书舍人", drafter_t, 4),
        (
            "右谏议大夫",
            ft(w, fe(w, "右谏议大夫", "官职"), "北宋元丰改制后"),
            1,
        ),
        (
            "起居舍人",
            ft(w, fe(w, "起居舍人", "官职"), "北宋元丰五年五月"),
            1,
        ),
        (
            "右司谏",
            ft(w, fe(w, "右司谏", "官职"), "北宋元丰新制"),
            1,
        ),
        (
            "右正言",
            ft(w, fe(w, "右正言", "官职"), "北宋元丰新制"),
            1,
        ),
    )
    for title, target, quota in endpoints:
        rid = rel(
            w,
            institute_t,
            target,
            "编制隶属",
            i,
            staff,
            f"元丰新制中书省{title}{quota}人。",
            "编制",
            staff_quota=quota,
            staff_type="官",
        )
        set_rel_attrs(
            w,
            rid,
            quota,
            "官",
            f"中书省主条明载{title}{quota}人。",
        )
    w.commit()


def entry768_rooms():
    i = 768
    rooms = Q(
        i,
        "分房八：吏、户、兵礼、刑、工、主事、班簿、制敕库房"
        "（哲宗新增催驱虏，兵礼房分为二房，共十房）。",
        "编制",
    )
    w = W(i)
    institute_e = fe(w, "中书省", "机构")
    yuan = ft(w, institute_e, "北宋元丰新制")
    room_tps = {}
    for title in (
        "中书省吏房",
        "中书省户房",
        "中书省兵礼房",
        "中书省刑房",
        "中书省工房",
        "中书省主事房",
        "中书省班簿房",
        "中书省制敕库房",
    ):
        eid = en(w, title, "机构", rooms, f"元丰中书省八房编制明载{title}。")
        tid = tp(
            w,
            eid,
            "北宋元丰新制（中书省）",
            "中书省八个常设办事房之一",
            i,
            rooms,
            "中央政务办事部门",
            f"建{title}元丰新制节点。",
            "编制",
            chain="none",
        )
        room_tps[title] = tid
        rel(
            w,
            yuan,
            tid,
            "上下级机构",
            i,
            rooms,
            f"元丰新制{title}为中书省常设办事房。",
            "编制",
        )

    philosophy = tp(
        w,
        institute_e,
        "北宋哲宗朝（中书省分房变化）",
        "新增催驱房，兵礼房分为兵房、礼房，分房增至十",
        i,
        rooms,
        "中央政务机构",
        "建哲宗朝中书省分房变化节点。",
        "编制",
        chain="none",
    )
    chain_all(
        w,
        institute_e,
        [
            ft(w, institute_e, "魏黄初元年"),
            ft(w, institute_e, "北宋建隆三年前"),
            ft(w, institute_e, "北宋元丰改制前"),
            yuan,
            ft(w, institute_e, "北宋元祐元年十一月"),
            philosophy,
            ft(w, institute_e, "南宋建炎三年四月二十九日"),
        ],
        "把哲宗分房变化节点接入中书省全局时间链。",
    )
    combined_e = fe(w, "中书省兵礼房", "机构")
    combined_end = tp(
        w,
        combined_e,
        "北宋哲宗朝",
        "分为中书省兵房、礼房",
        i,
        rooms,
        "中央政务办事部门",
        "建兵礼房哲宗朝拆分终点。",
        "编制",
        chain="none",
    )
    chain_all(
        w,
        combined_e,
        [room_tps["中书省兵礼房"], combined_end],
        "连接兵礼房元丰始置与哲宗拆分节点。",
    )
    for title in ("中书省兵房", "中书省礼房", "中书省催驱房"):
        eid = en(w, title, "机构", rooms, f"哲宗中书省分房变化明载{title}。")
        tid = tp(
            w,
            eid,
            "北宋哲宗朝",
            "哲宗朝中书省分房变化时设置",
            i,
            rooms,
            "中央政务办事部门",
            f"建{title}哲宗朝节点。",
            "编制",
            chain="none",
        )
        rel(
            w,
            philosophy,
            tid,
            "上下级机构",
            i,
            rooms,
            f"哲宗朝{title}为中书省办事房。",
            "编制",
        )
        if title in ("中书省兵房", "中书省礼房"):
            rel(
                w,
                combined_end,
                tid,
                "前后演变",
                i,
                rooms,
                f"哲宗朝中书省兵礼房分为{title}。",
                "编制",
            )
    w.commit()


def entry768_yuanfeng_clerks():
    i = 768
    staff = Q(
        i,
        "吏额四十五：录事三人、主事四人、令史七人、书令史十四人、守当官十七人。"
        "哲宗朝置守阙守当官一百人",
        "编制",
    )
    w = W(i)
    institute_e = fe(w, "中书省", "机构")
    institute_t = ft(w, institute_e, "北宋元丰新制")
    specs = (
        (
            "录事",
            3,
            [
                "西晋",
                "隋朝",
                "唐朝",
                "宋前期",
                "北宋元丰新制",
            ],
        ),
        (
            "主事",
            4,
            [
                "汉至唐",
                "宋前期",
                "北宋元丰新制（门下省）",
                "宋代（枢密院，未载具体年月）",
            ],
        ),
        (
            "令史",
            7,
            [
                "汉至唐",
                "宋代（枢密院，未载具体年月）",
                "北宋（登闻检院，未载具体年月）",
                "北宋（登闻鼓院，未载具体年月）",
                "北宋元丰新制（门下省）",
                "南宋嘉定五年",
            ],
        ),
        (
            "书令史",
            14,
            [
                "汉至唐",
                "宋代（枢密院，未载具体年月）",
                "北宋淳化四年二月",
                "宋前期（通进司）",
                "北宋元丰新制（门下省）",
                "南宋初（登闻检院）",
                "南宋（登闻鼓院）",
                "南宋嘉定五年",
            ],
        ),
        (
            "守当官",
            17,
            [
                "宋前期",
                "北宋熙宁三年十一月",
                "北宋元丰新制（门下省）",
                "南宋初（登闻检院）",
                "南宋（登闻鼓院）",
                "南宋嘉定五年",
            ],
        ),
    )
    for title, quota, old_times in specs:
        eid = fe(w, title, "官职")
        tid = tp(
            w,
            eid,
            "北宋元丰新制（中书省）",
            f"中书省{title}，设{quota}人",
            i,
            staff,
            "吏",
            f"建{title}在元丰中书省的编制节点。",
            "编制",
            chain="none",
        )
        ordered = [ft(w, eid, time) for time in old_times]
        if title in ("录事", "主事", "令史"):
            insert_at = len(ordered) if title in ("录事", "主事") else 5
        else:
            insert_at = 5 if title == "书令史" else 3
        ordered.insert(insert_at, tid)
        chain_all(w, eid, ordered, f"把元丰中书省节点接入{title}全局时间链。")
        rel(
            w,
            institute_t,
            tid,
            "编制隶属",
            i,
            staff,
            f"元丰新制中书省{title}{quota}人。",
            "编制",
            staff_quota=quota,
            staff_type="吏",
        )

    waiting_e = fe(w, "守阙守当官", "官职")
    waiting_t = tp(
        w,
        waiting_e,
        "北宋哲宗朝（中书省）",
        "中书省候补守当官，设一百人",
        i,
        staff,
        "候补吏",
        "建哲宗朝中书省守阙守当官编制节点。",
        "编制",
        chain="none",
    )
    chain_all(
        w,
        waiting_e,
        [
            waiting_t,
            ft(w, waiting_e, "北宋绍圣三年"),
        ],
        "连接守阙守当官在中书、门下二省的哲宗朝节点。",
    )
    rel(
        w,
        ft(w, institute_e, "北宋哲宗朝（中书省分房变化）"),
        waiting_t,
        "编制隶属",
        i,
        staff,
        "哲宗朝中书省置守阙守当官一百人。",
        "编制",
        staff_quota=100,
        staff_type="候补吏",
    )
    w.commit()


def entry768_merger_staff():
    i = 768
    merger = Q(
        i,
        "③南宋建炎三年（1129）四月二十九日，中书省与门下省合并为中书门下省。"
        "吏额八十九人：中书省四十三与门下省四十六相合。"
        "此外守阙守当官（候补吏人）一百五十人",
        "编制",
    )
    w = W(i)
    waiting_e = fe(w, "守阙守当官", "官职")
    waiting_south = tp(
        w,
        waiting_e,
        "南宋建炎三年四月二十九日（中书门下省）",
        "两省合并后候补吏人一百五十人",
        i,
        merger,
        "候补吏",
        "建合省后守阙守当官一百五十人编制节点。",
        "编制",
        chain="none",
    )
    chain_all(
        w,
        waiting_e,
        [
            ft(w, waiting_e, "北宋哲宗朝（中书省）"),
            ft(w, waiting_e, "北宋绍圣三年"),
            waiting_south,
        ],
        "把建炎合省后的守阙守当官节点接入全局时间链。",
    )
    rel(
        w,
        ft(w, fe(w, "中书门下省", "机构"), "南宋建炎三年四月二十九日"),
        waiting_south,
        "编制隶属",
        i,
        merger,
        "建炎三年合省后守阙守当官一百五十人。",
        "编制",
        staff_quota=150,
        staff_type="候补吏",
    )
    w.commit()


def entry769():
    i = 769
    main = Q(
        i,
        "中书省常设办事部门之一。掌承办除授、考核、升迁、降免、赏罚、"
        "官告废置、荐举、官员请假、亡故、临时差官等文书，以及本省杂务。",
    )
    w = W(i)
    entity_id = fe(w, "中书省吏房", "机构")
    tid = refine(
        w,
        ft(w, entity_id, "北宋元丰新制（中书省）"),
        i,
        main,
        "专条细化中书省吏房职掌。",
        event="掌除授、考核、升降、赏罚、荐举及本省杂务等文书",
        category="中央政务办事部门",
    )
    rid = relation_id(
        w,
        "中书省",
        "中书省吏房",
        "上下级机构",
        "北宋元丰新制",
        "北宋元丰新制（中书省）",
    )
    assert rid
    cite(w, "Relationships", rid, i, main, "专条补证吏房为中书省常设办事部门。")
    w.commit()


def entry770():
    i = 770
    main = Q(
        i,
        "中书省常设办事部门之一。掌郡县户口增长或下降数，以决定镇升县、"
        "县升州、州升府，反之，予以降格或废并；调发边防军需钱粮；"
        "给散、借贷钱物。",
    )
    w = W(i)
    entity_id = fe(w, "中书省户房", "机构")
    tid = refine(
        w,
        ft(w, entity_id, "北宋元丰新制（中书省）"),
        i,
        main,
        "专条细化中书省户房职掌。",
        event="掌州县升降废并、边防军需钱粮及钱物给散借贷",
        category="中央政务办事部门",
    )
    rid = relation_id(
        w,
        "中书省",
        "中书省户房",
        "上下级机构",
        "北宋元丰新制",
        "北宋元丰新制（中书省）",
    )
    assert rid
    cite(w, "Relationships", rid, i, main, "专条补证户房为中书省常设办事部门。")
    w.commit()


def main():
    # 754“鼓”、756“登闻鼓”是物件；760“监院”是监登闻鼓院的简称，
    # 均不另建机构或官职实体。
    entry751()
    entry752()
    entry753()
    entry754_note()
    entry755_core()
    entry757()
    entry758()
    entry759()
    entry761()
    entry762()
    entry763()
    entry764()
    entry765()
    entry766()
    entry767()
    entry755_staff()
    entry768_core()
    entry768_early_staff()
    entry768_yuanfeng_officials()
    entry768_rooms()
    entry768_yuanfeng_clerks()
    entry768_merger_staff()
    entry769()
    entry770()


if __name__ == "__main__":
    main()
