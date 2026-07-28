#!/usr/bin/env python3
"""提取 chapter2t4 第731–750条：进奏院候补吏与登闻检院、登闻院系统。"""
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


F = {i: load(i) for i in range(731, 751)}


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
    cite(
        w,
        "Relationships",
        relationship_id,
        i,
        quotation,
        decision,
        field,
    )
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


def mark_citation_conflict(w, target_table, target_id, i, quotation, note, decision):
    """引用去重后，显式把既有同源引用升级为冲突并留下追溯记录。"""
    row = w.conn.execute(
        "select id,conflict_flag,note from Citations "
        "where target_table=? and target_id=? and citation=? and quotation=? "
        "order by id desc limit 1",
        (target_table, target_id, C(i), quotation),
    ).fetchone()
    assert row, (target_table, target_id, i)
    if row[1] != 1 or row[2] != note:
        w.conn.execute(
            "update Citations set conflict_flag=1,note=? where id=?",
            (note, row[0]),
        )
        w._br(
            "Citations",
            row[0],
            f"将同源既有引用显式标为冲突：{decision}",
        )


def entry732():
    i = 732
    main = Q(
        i,
        "公吏名。在都进奏院执役。咸平四年九月，由守阙进奏官改名。"
        "都进奏院拣中副知以十六人为额，南宋淳熙时，减为十三人。",
    )
    reduction = Q(
        i,
        "（淳熙十三年）诏都进奏院减进奏官十人、副知三人。",
        "简称",
    )
    w = W(i)
    source_e = fe(w, "守阙进奏官", "官职")
    source_t = refine(
        w,
        ft(w, source_e, "宋代（未载具体年月）"),
        i,
        main,
        "专条给出守阙进奏官改名的年月。",
        time="北宋咸平四年九月",
        event="改名拣中副知",
        category="公吏",
    )
    target_e = fe(w, "拣中副知", "官职")
    target_t = refine(
        w,
        ft(w, target_e, "宋代（守阙进奏官改名后，未载年月）"),
        i,
        main,
        "专条给出拣中副知始置年月与十六人编制。",
        time="北宋咸平四年九月",
        event="由守阙进奏官改名，在都进奏院执役，十六人为额",
        category="公吏",
    )
    cite(
        w,
        "Timepoints",
        target_t,
        i,
        main,
        "本条所记后继与守阙进奏官条冲突，保留并标记。",
        note="本条称守阙进奏官改名拣中副知；守阙进奏官条称守阙副知代之。",
        conflict_flag=1,
    )
    mark_citation_conflict(
        w,
        "Timepoints",
        target_t,
        i,
        main,
        "本条称守阙进奏官改名拣中副知；守阙进奏官条称守阙副知代之。",
        "确保拣中副知时间点引用保留冲突标记。",
    )
    evolution = relation_id(
        w, "守阙进奏官", "拣中副知", "前后演变"
    )
    assert evolution
    cite(
        w,
        "Relationships",
        evolution,
        i,
        main,
        "专条补证咸平四年守阙进奏官改名拣中副知；与守阙进奏官条冲突。",
        note="本条称守阙进奏官改名拣中副知；守阙进奏官条称守阙副知代之。",
        conflict_flag=1,
    )
    mark_citation_conflict(
        w,
        "Relationships",
        evolution,
        i,
        main,
        "本条称守阙进奏官改名拣中副知；守阙进奏官条称守阙副知代之。",
        "确保改名拣中副知关系引用保留冲突标记。",
    )

    institute_e = fe(w, "都进奏院", "机构")
    south_t = ft(w, institute_e, "南宋初")
    quota16 = relation_id(
        w,
        "都进奏院",
        "拣中副知",
        "编制隶属",
        "南宋初",
    )
    assert quota16
    set_rel_attrs(w, quota16, 16, "吏", "专条明载拣中副知十六人为额。")
    cite(
        w,
        "Relationships",
        quota16,
        i,
        main,
        "专条补证拣中副知隶都进奏院且原额十六人。",
    )

    reduction_t = tp(
        w,
        target_e,
        "南宋淳熙十三年",
        "减三人，定额十三人",
        i,
        reduction,
        "公吏",
        "简称字段引文给出淳熙十三年减额变化。",
        "简称",
        chain="none",
    )
    chain_all(
        w,
        target_e,
        [target_t, reduction_t],
        "连接拣中副知咸平改名与淳熙减额节点。",
    )
    institute_reduction = tp(
        w,
        institute_e,
        "南宋淳熙十三年",
        "减进奏官十人、拣中副知三人",
        i,
        reduction,
        "中央奏报机构",
        "引文明确记载都进奏院淳熙十三年减额。",
        "简称",
        chain="none",
    )
    chain_all(
        w,
        institute_e,
        [
            ft(w, institute_e, "北宋太平兴国七年十月二十一日"),
            ft(w, institute_e, "北宋太平兴国七年后（未载具体年月）"),
            ft(w, institute_e, "北宋元丰新制"),
            south_t,
            institute_reduction,
        ],
        "把淳熙十三年减额节点接到都进奏院时间链尾。",
    )
    rel(
        w,
        institute_reduction,
        reduction_t,
        "编制隶属",
        i,
        reduction,
        "淳熙十三年都进奏院拣中副知减三人后为十三人。",
        "简称",
        staff_quota=13,
        staff_type="吏",
    )
    w.commit()


def entry731():
    i = 731
    main = Q(
        i,
        "公吏名。原为都进奏院进奏官候补人，咸平四年九月设守阙副知以代之"
        "（见《宋会要·职官》2之46）。",
    )
    w = W(i)
    source_e = fe(w, "守阙进奏官", "官职")
    source_t = ft(w, source_e, "北宋咸平四年九月")
    cite(
        w,
        "Timepoints",
        source_t,
        i,
        main,
        "本条同样给出咸平四年终结时间，但所记后继与拣中副知条冲突。",
        note="本条称守阙副知代之；第182页拣中副知条称改名拣中副知。",
        conflict_flag=1,
    )
    institute_t = ft(
        w,
        fe(w, "都进奏院", "机构"),
        "北宋太平兴国七年后（未载具体年月）",
    )
    rel(
        w,
        institute_t,
        source_t,
        "编制隶属",
        i,
        main,
        "本条明确守阙进奏官为都进奏院进奏官候补吏。",
        staff_type="吏",
    )
    alternate = rel(
        w,
        source_t,
        ft(w, fe(w, "守阙副知", "官职"), "北宋咸平四年九月"),
        "前后演变",
        i,
        main,
        "照录本条所记咸平四年设守阙副知代替守阙进奏官。",
    )
    cite(
        w,
        "Relationships",
        alternate,
        i,
        main,
        "本条后继说法与拣中副知条冲突，保留并标记。",
        note="本条称守阙副知代之；第182页拣中副知条称改名拣中副知。",
        conflict_flag=1,
    )
    mark_citation_conflict(
        w,
        "Relationships",
        alternate,
        i,
        main,
        "本条称守阙副知代之；第182页拣中副知条称改名拣中副知。",
        "确保守阙副知后继关系引用保留冲突标记。",
    )
    w.commit()


def entry734_core():
    i = 734
    origin = Q(
        i,
        "宋雍熙元年(984)，改瓯为检，改瓯院为登闻院；"
        "景德四年(1007)五月改为登闻检院。",
        "职源与沿革",
    )
    north_duty = Q(
        i,
        "凡官民章奏申诉无例由都进奏院或阎门通进者，可向登闻鼓院投诉；"
        "如投诉为登闻鼓院所抑，以及事干机密者，登闻检院接收处理。",
        "职掌",
    )
    south_duty = Q(
        i,
        "南宋时，登闻检院与登闻鼓院的分工，已由申诉程序上先后的分工，"
        "变为职事上的分工。检院掌收接朝廷命官各色人有关机密军国重事、"
        "军期朝政阙失，论诉在京官员不法，及公私利害之事",
        "职掌",
    )
    north_staff = Q(
        i,
        "①北宋隶谏议大夫。判登闻检院事一人，令史二人，书写人一人，"
        "监登闻检院门一人。",
        "编制",
    )
    south_staff = Q(
        i,
        "②南宋隶谏院。监登闻检院二人（常除一人），主管检匣一人，手分三人",
        "编制",
    )
    w = W(i)
    entity_id = en(w, "登闻检院", "机构", origin, "本条明确登闻检院为官署。")
    start = tp(
        w,
        entity_id,
        "北宋景德四年五月",
        "由登闻院改名，接收被登闻鼓院所抑及事干机密的申诉",
        i,
        origin,
        "中央申诉受理机构",
        "建登闻检院景德四年始置节点。",
        "职源与沿革",
        chain="none",
    )
    cite(w, "Timepoints", start, i, north_duty, "补证北宋登闻检院职掌。", "职掌")
    north = tp(
        w,
        entity_id,
        "北宋（未载具体年月）",
        "隶谏议大夫，置判院事、令史、书写人及监门官",
        i,
        north_staff,
        "中央申诉受理机构",
        "编制字段给出北宋隶属与官吏配置。",
        "编制",
        chain="none",
    )
    south = tp(
        w,
        entity_id,
        "南宋",
        "改按职事与登闻鼓院分工，掌机密军国重事、朝政阙失及不法利害申诉",
        i,
        south_duty,
        "中央申诉受理机构",
        "建南宋职掌变化节点。",
        "职掌",
        chain="none",
    )
    cite(w, "Timepoints", south, i, south_staff, "补证南宋隶属与官吏配置。", "编制")
    chain_all(w, entity_id, [start, north, south], "连接登闻检院北宋始置至南宋节点。")
    w.commit()


def entry737():
    i = 737
    main = Q(i, "宋前期差遣官名。元丰新制后职事官名。")
    origin = Q(
        i,
        "真宗景德四年五月置（《燕冀诒谋录》卷2、《长编》卷65）。",
        "职源",
    )
    duty = Q(
        i,
        "领登闻检院事，通常先投诉鼓院，倘为鼓院所抑，再申判检院官",
        "职掌",
    )
    w = W(i)
    entity_id = en(w, "判登闻检院事", "官职", main, "本条明确为差遣、职事官名。")
    start = tp(
        w,
        entity_id,
        "北宋景德四年五月",
        "始置，差遣官，领登闻检院事",
        i,
        origin,
        "差遣官",
        "建判登闻检院事景德始置节点。",
        "职源",
        chain="none",
    )
    cite(w, "Timepoints", start, i, duty, "补证判登闻检院事职掌。", "职掌")
    reform = tp(
        w,
        entity_id,
        "北宋元丰新制后",
        "由差遣官改为职事官",
        i,
        main,
        "职事官",
        "建元丰新制后的官制变化节点。",
        chain="none",
    )
    chain_all(w, entity_id, [start, reform], "连接判登闻检院事始置与元丰改制节点。")
    w.commit()


def entry738():
    i = 738
    main = Q(
        i,
        "南宋初，改判检院为监检院。“旧称判官，今从臣僚之请，改称监院”"
        "（《宋会要·职官》3之67）。",
    )
    w = W(i)
    source_e = fe(w, "判登闻检院事", "官职")
    source_end = tp(
        w,
        source_e,
        "南宋初",
        "改称监登闻检院",
        i,
        main,
        "差遣官",
        "建判登闻检院事南宋初改称节点。",
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
        "把南宋初改称节点接入判登闻检院事时间链。",
    )
    target_e = en(w, "监登闻检院", "官职", main, "本条明确南宋初改置监登闻检院。")
    target_start = tp(
        w,
        target_e,
        "南宋初",
        "由判登闻检院事改称",
        i,
        main,
        "职事官",
        "建监登闻检院南宋初始置节点。",
        chain="none",
    )
    rel(
        w,
        source_end,
        target_start,
        "前后演变",
        i,
        main,
        "南宋初判检院改称监检院。",
    )
    w.commit()


def entry739():
    i = 739
    main = Q(
        i,
        "职事官名。由内侍官充南宋时，监登闻检院门与监登闻鼓院门官互兼"
        "（见《宋会要·职官》3之64、68）。",
    )
    w = W(i)
    entity_id = en(w, "监登闻检院门", "官职", main, "本条明确为职事官名。")
    south = tp(
        w,
        entity_id,
        "南宋",
        "由内侍官充，与监登闻鼓院门官互兼",
        i,
        main,
        "职事官",
        "建监登闻检院门南宋节点。",
        attr_officer_type="内侍官",
        chain="none",
    )
    w.commit()


def entry740():
    i = 740
    main = Q(
        i,
        "南宋职事官名，由内侍充。掌监管检匣。检匣由亲从官抬进抬出，"
        "防止匣内贮纳的书、状不致漏泄、作弊或遗失",
    )
    w = W(i)
    entity_id = en(w, "主管检匣", "官职", main, "本条明确为南宋职事官名。")
    tp(
        w,
        entity_id,
        "南宋",
        "由内侍充，监管检匣，防止所贮书状漏泄、作弊或遗失",
        i,
        main,
        "职事官",
        "建主管检匣南宋职掌节点。",
        attr_officer_type="内侍",
        chain="none",
    )
    w.commit()


def entry746():
    i = 746
    origin = Q(
        i,
        "瓯院之名见于唐文宗朝，太和六年（832），谏议大夫郭承嘏知瓯院事"
        "（《旧唐书》卷165《郭承嘏传》）。宋初沿置。太平兴国九年"
        "（即雍熙元年）七月十二日，改瓯院为登闻院",
        "职源与沿革",
    )
    duty = Q(
        i,
        "领四匮投状事。凡议论国家大事、朝政阙失，或申诉冤案，均许士民于匮投书",
        "职掌",
    )
    w = W(i)
    entity_id = en(w, "匦院", "机构", origin, "规范 OCR 标题后，本条明确为官署。")
    tang = tp(
        w,
        entity_id,
        "唐太和六年",
        "已见知匦院事",
        i,
        origin,
        "投状受理机构",
        "建匦院唐代可考节点；引文中的“瓯院”为 OCR 字形。",
        "职源与沿革",
        chain="none",
    )
    cite(w, "Timepoints", tang, i, duty, "补证匦院受理投书的职掌。", "职掌")
    song = tp(
        w,
        entity_id,
        "宋初",
        "沿唐制设置，领四匮投状事",
        i,
        origin,
        "投状受理机构",
        "建匦院宋初沿置节点。",
        "职源与沿革",
        chain="none",
    )
    end = tp(
        w,
        entity_id,
        "北宋雍熙元年七月十二日",
        "改名登闻院",
        i,
        origin,
        "投状受理机构",
        "建匦院改名登闻院的终点。",
        "职源与沿革",
        chain="none",
    )
    chain_all(w, entity_id, [tang, song, end], "连接匦院唐代、宋初与雍熙改名节点。")
    w.commit()


def entry742():
    i = 742
    origin = Q(
        i,
        "太宗雍熙元年（984）七月十二日（庚申）由医院改名"
        "（见《分纪》卷14《登闻检院》，参《长编》卷25）。"
        "景德四年五月十三日改为登闻检院",
        "职源与沿革",
    )
    structure = Q(
        i,
        "隶谏院，为中书门下下属机构。设判院官一人，或置勾当登闻院事、"
        "兼知登闻院事。监登闻院门一人",
        "编制",
    )
    w = W(i)
    entity_id = en(w, "登闻院", "机构", origin, "本条明确登闻院为官署。")
    start = tp(
        w,
        entity_id,
        "北宋雍熙元年七月十二日",
        "由匦院改名，开言路、通下情",
        i,
        origin,
        "中央申诉受理机构",
        "建登闻院雍熙始置节点；原文“医院”为 OCR 误字。",
        "职源与沿革",
        chain="none",
    )
    end = tp(
        w,
        entity_id,
        "北宋景德四年五月十三日",
        "改名登闻检院",
        i,
        origin,
        "中央申诉受理机构",
        "建登闻院景德四年改名终点。",
        "职源与沿革",
        chain="none",
    )
    cite(w, "Timepoints", start, i, structure, "补证登闻院隶属与编制。", "编制")
    chain_all(w, entity_id, [start, end], "连接登闻院雍熙始置与景德改名节点。")

    source_t = ft(w, fe(w, "匦院", "机构"), "北宋雍熙元年七月十二日")
    rel(
        w,
        source_t,
        start,
        "前后演变",
        i,
        origin,
        "登闻院条记载雍熙元年由前身官署改名；原文“医院”为 OCR 误字。",
        "职源与沿革",
    )
    target_t = ft(w, fe(w, "登闻检院", "机构"), "北宋景德四年五月")
    rel(
        w,
        end,
        target_t,
        "前后演变",
        i,
        origin,
        "景德四年登闻院改为登闻检院。",
        "职源与沿革",
    )

    remonstrance_e = fe(w, "谏院", "机构")
    remonstrance_north = tp(
        w,
        remonstrance_e,
        "北宋前期（登闻院体制）",
        "登闻院隶谏院；与南宋两省谏官置局体制分列",
        i,
        structure,
        "谏官机构",
        "为登闻院北宋隶属关系补建谏院同期节点，并注明与南宋体制不同。",
        "编制",
        chain="none",
    )
    chain_all(
        w,
        remonstrance_e,
        [
            remonstrance_north,
            ft(w, remonstrance_e, "南宋"),
            ft(w, remonstrance_e, "南宋绍兴二年"),
        ],
        "把北宋登闻院体制下的谏院节点接到既有南宋时间链之前。",
    )
    rel(
        w,
        remonstrance_north,
        start,
        "上下级机构",
        i,
        structure,
        "编制字段明载登闻院隶谏院。",
        "编制",
    )
    rel(
        w,
        ft(w, fe(w, "中书门下", "机构"), "宋前期"),
        start,
        "上下级机构",
        i,
        structure,
        "编制字段明载登闻院为中书门下下属机构。",
        "编制",
    )
    gate_e = en(
        w,
        "监登闻院门",
        "官职",
        structure,
        "编制字段明确登闻院置监门官一人。",
    )
    gate_t = tp(
        w,
        gate_e,
        "北宋（登闻院，未载具体年月）",
        "监守登闻院门，设一人",
        i,
        structure,
        "职事官",
        "建监登闻院门编制节点。",
        "编制",
        chain="none",
    )
    rel(
        w,
        start,
        gate_t,
        "编制隶属",
        i,
        structure,
        "编制字段明载登闻院置监登闻院门一人。",
        "编制",
        staff_quota=1,
        staff_type="官",
    )
    w.commit()


def entry743():
    i = 743
    origin = Q(
        i,
        "雍熙元年（即太平兴国九年）七月十二日，与改瓯院为登闻院同步，"
        "即设判院事官一人",
        "职源",
    )
    qualification = Q(
        i,
        "初以中书舍人（或知制诰）兼判，淳化二年四月后，差司谏、正言一员"
        "判登闻院事",
        "官品",
    )
    w = W(i)
    entity_id = en(w, "判登闻院事", "官职", origin, "本条明确为登闻院差遣官。")
    start = tp(
        w,
        entity_id,
        "北宋雍熙元年七月十二日",
        "随登闻院改置而始设一人，领登闻院",
        i,
        origin,
        "差遣官",
        "建判登闻院事始置节点。",
        "职源",
        chain="none",
    )
    change = tp(
        w,
        entity_id,
        "北宋淳化二年四月",
        "改差司谏、正言一员充任",
        i,
        qualification,
        "差遣官",
        "建判登闻院事任官资格变化节点。",
        "官品",
        chain="none",
    )
    chain_all(w, entity_id, [start, change], "连接判登闻院事始置与淳化资格变化节点。")

    institute_e = fe(w, "登闻院", "机构")
    institute_change = tp(
        w,
        institute_e,
        "北宋淳化二年四月",
        "改差司谏、正言一员判登闻院事",
        i,
        qualification,
        "中央申诉受理机构",
        "为淳化二年判院官资格变化补建机构节点。",
        "官品",
        chain="none",
    )
    chain_all(
        w,
        institute_e,
        [
            ft(w, institute_e, "北宋雍熙元年七月十二日"),
            institute_change,
            ft(w, institute_e, "北宋景德四年五月十三日"),
        ],
        "把淳化二年编制变化接入登闻院时间链。",
    )
    rel(
        w,
        ft(w, institute_e, "北宋雍熙元年七月十二日"),
        start,
        "编制隶属",
        i,
        origin,
        "登闻院始置时即设判院事一人。",
        "职源",
        staff_quota=1,
        staff_type="官",
    )
    rel(
        w,
        institute_change,
        change,
        "编制隶属",
        i,
        qualification,
        "淳化二年后差司谏、正言一员判登闻院事。",
        "官品",
        staff_quota=1,
        staff_type="官",
    )
    w.commit()


def entry745():
    i = 745
    main = Q(
        i,
        "差遣官名，由三班使臣充。地位低于判院事、知院事，为其属官。"
        "《宋会要·职官》3之62：“（至道三年）勾当登闻院、殿直程峻。”",
    )
    w = W(i)
    entity_id = en(w, "勾当登闻院公事", "官职", main, "本条明确为差遣官名。")
    officer_t = tp(
        w,
        entity_id,
        "北宋至道三年",
        "已见勾当登闻院，由三班使臣充，为判、知院事属官",
        i,
        main,
        "差遣官",
        "建勾当登闻院公事至道三年可考节点。",
        attr_officer_type="三班使臣",
        chain="none",
    )
    institute_e = fe(w, "登闻院", "机构")
    institute_t = tp(
        w,
        institute_e,
        "北宋至道三年",
        "已见勾当登闻院公事",
        i,
        main,
        "中央申诉受理机构",
        "为至道三年属官记载补建登闻院节点。",
        chain="none",
    )
    chain_all(
        w,
        institute_e,
        [
            ft(w, institute_e, "北宋雍熙元年七月十二日"),
            ft(w, institute_e, "北宋淳化二年四月"),
            institute_t,
            ft(w, institute_e, "北宋景德四年五月十三日"),
        ],
        "把至道三年属官节点接入登闻院时间链。",
    )
    rel(
        w,
        institute_t,
        officer_t,
        "编制隶属",
        i,
        main,
        "本条明载勾当登闻院公事为登闻院属官。",
        staff_type="官",
    )
    w.commit()


def entry744():
    i = 744
    main = Q(
        i,
        "兼官名。真宗咸平时，上封言事者多，为防壅蔽，于判登闻院官之外，"
        "特设兼知官二人。非常制。《宋会要·职官》3之63："
        "“（咸平二年七月）命工部尚书张宏、翰林学士王旦兼知登闻院事。”"
        "其地位高于判登闻院事。",
    )
    w = W(i)
    entity_id = en(w, "知登闻院事", "官职", main, "本条明确为非常设兼官。")
    officer_t = tp(
        w,
        entity_id,
        "北宋咸平二年七月",
        "为防上封言事壅蔽，特设兼知官二人，地位高于判院事",
        i,
        main,
        "兼官",
        "建知登闻院事临时设置节点。",
        chain="none",
    )
    institute_e = fe(w, "登闻院", "机构")
    institute_t = tp(
        w,
        institute_e,
        "北宋咸平二年七月",
        "于判院官外特设兼知登闻院事二人",
        i,
        main,
        "中央申诉受理机构",
        "为咸平二年临时增置兼知官补建机构节点。",
        chain="none",
    )
    chain_all(
        w,
        institute_e,
        [
            ft(w, institute_e, "北宋雍熙元年七月十二日"),
            ft(w, institute_e, "北宋淳化二年四月"),
            ft(w, institute_e, "北宋至道三年"),
            institute_t,
            ft(w, institute_e, "北宋景德四年五月十三日"),
        ],
        "把咸平二年增置兼知官节点接入登闻院时间链。",
    )
    rel(
        w,
        institute_t,
        officer_t,
        "编制隶属",
        i,
        main,
        "咸平二年登闻院特设兼知官二人。",
        staff_quota=2,
        staff_type="兼官",
    )
    w.commit()


def entry748():
    i = 748
    main = Q(i, "吏名。隶登闻检院。掌承办本院事务。设二人")
    w = W(i)
    entity_id = fe(w, "令史", "官职")
    north = tp(
        w,
        entity_id,
        "北宋（登闻检院，未载具体年月）",
        "隶登闻检院，承办本院事务，设二人",
        i,
        main,
        "吏",
        "建令史在登闻检院的北宋编制节点。",
        chain="none",
    )
    chain_all(
        w,
        entity_id,
        [
            ft(w, entity_id, "汉至唐"),
            ft(w, entity_id, "宋代（枢密院，未载具体年月）"),
            north,
            ft(w, entity_id, "北宋元丰新制（门下省）"),
            ft(w, entity_id, "南宋嘉定五年"),
        ],
        "把登闻检院令史节点接入令史全局时间链。",
    )
    rel(
        w,
        ft(w, fe(w, "登闻检院", "机构"), "北宋（未载具体年月）"),
        north,
        "编制隶属",
        i,
        main,
        "本条明载令史隶登闻检院且设二人。",
        staff_quota=2,
        staff_type="吏",
    )
    w.commit()


def entry749():
    i = 749
    main = Q(
        i,
        "书令史、守当官总名。隶登闻检院。统为管文案、文书抄写的胥吏，"
        "但不指定某一吏称。如南宋初，登闻检院“手分三人”，既可以由书令史充，"
        "也可以由书令史或守当官充，须视所派执役吏人资格而定",
    )
    w = W(i)
    hand_e = fe(w, "手分", "官职")
    hand_t = tp(
        w,
        hand_e,
        "南宋初（登闻检院）",
        "书令史、守当官的总名，管文案与文书抄写，设三人",
        i,
        main,
        "胥吏统称",
        "建手分在南宋登闻检院的统称与编制节点。",
        chain="none",
    )
    chain_all(
        w,
        hand_e,
        [ft(w, hand_e, "宋代"), hand_t],
        "把南宋登闻检院手分节点接入既有时间链。",
    )

    clerk_e = fe(w, "书令史", "官职")
    clerk_t = tp(
        w,
        clerk_e,
        "南宋初（登闻检院）",
        "可充登闻检院手分，管文案与文书抄写",
        i,
        main,
        "胥吏",
        "建书令史作为登闻检院手分实例的同期节点。",
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
            clerk_t,
            ft(w, clerk_e, "南宋嘉定五年"),
        ],
        "把南宋登闻检院节点接入书令史全局时间链。",
    )

    keeper_e = fe(w, "守当官", "官职")
    keeper_t = tp(
        w,
        keeper_e,
        "南宋初（登闻检院）",
        "可充登闻检院手分，管文案与文书抄写",
        i,
        main,
        "胥吏",
        "建守当官作为登闻检院手分实例的同期节点。",
        chain="none",
    )
    chain_all(
        w,
        keeper_e,
        [
            ft(w, keeper_e, "宋前期"),
            ft(w, keeper_e, "北宋熙宁三年十一月"),
            ft(w, keeper_e, "北宋元丰新制（门下省）"),
            keeper_t,
            ft(w, keeper_e, "南宋嘉定五年"),
        ],
        "把南宋登闻检院节点接入守当官全局时间链。",
    )
    rel(
        w,
        hand_t,
        clerk_t,
        "统称与实例",
        i,
        main,
        "本条明载手分是书令史、守当官总名。",
    )
    rel(
        w,
        hand_t,
        keeper_t,
        "统称与实例",
        i,
        main,
        "本条明载手分是书令史、守当官总名。",
    )
    rel(
        w,
        ft(w, fe(w, "登闻检院", "机构"), "南宋"),
        hand_t,
        "编制隶属",
        i,
        main,
        "本条明载南宋初登闻检院手分三人。",
        staff_quota=3,
        staff_type="吏",
    )
    w.commit()


def entry750():
    i = 750
    main = Q(
        i,
        "吏卒名。隶登闻检院。由皇城司亲事官指挥所属禁卒充任，在检院从事抬、"
        "背铜制检匣进宫、出宫事。所谓“检匣一座”，“差承送亲事官擎背以匣投进文字”",
    )
    w = W(i)
    entity_id = en(w, "承送亲事官", "官职", main, "本条明确为登闻检院吏卒名。")
    officer_t = tp(
        w,
        entity_id,
        "南宋（未载具体年月）",
        "由皇城司亲事官指挥所属禁卒充任，擎背检匣出入宫",
        i,
        main,
        "吏卒",
        "建承送亲事官在登闻检院的职役节点。",
        attr_officer_type="禁卒",
        chain="none",
    )
    rel(
        w,
        ft(w, fe(w, "登闻检院", "机构"), "南宋"),
        officer_t,
        "编制隶属",
        i,
        main,
        "本条明载承送亲事官隶登闻检院。",
        staff_type="吏卒",
    )
    w.commit()


def entry734_relations():
    i = 734
    origin = Q(
        i,
        "宋雍熙元年(984)，改瓯为检，改瓯院为登闻院；"
        "景德四年(1007)五月改为登闻检院。",
        "职源与沿革",
    )
    north_staff = Q(
        i,
        "①北宋隶谏议大夫。判登闻检院事一人，令史二人，书写人一人，"
        "监登闻检院门一人。",
        "编制",
    )
    south_staff = Q(
        i,
        "②南宋隶谏院。监登闻检院二人（常除一人），主管检匣一人，手分三人",
        "编制",
    )
    w = W(i)
    institute_e = fe(w, "登闻检院", "机构")
    north = ft(w, institute_e, "北宋（未载具体年月）")
    south = ft(w, institute_e, "南宋")

    evolution = relation_id(
        w,
        "登闻院",
        "登闻检院",
        "前后演变",
        "北宋景德四年五月十三日",
        "北宋景德四年五月",
    )
    assert evolution
    cite(
        w,
        "Relationships",
        evolution,
        i,
        origin,
        "登闻检院条补证景德四年由登闻院改名。",
        "职源与沿革",
    )
    rel(
        w,
        ft(w, fe(w, "谏院", "机构"), "南宋"),
        south,
        "上下级机构",
        i,
        south_staff,
        "编制字段明载南宋登闻检院隶谏院。",
        "编制",
    )

    writer_e = fe(w, "书写人", "官职")
    writer_t = tp(
        w,
        writer_e,
        "北宋（登闻检院，未载具体年月）",
        "登闻检院书写人一人",
        i,
        north_staff,
        "吏",
        "建书写人在登闻检院的北宋编制节点。",
        "编制",
        chain="none",
    )
    chain_all(
        w,
        writer_e,
        [
            ft(w, writer_e, "北宋咸平四年九月（都进奏院）"),
            writer_t,
            ft(w, writer_e, "南宋初（都进奏院）"),
            ft(w, writer_e, "南宋淳熙十五年"),
        ],
        "把登闻检院书写人节点接入书写人全局时间链。",
    )
    gate_e = fe(w, "监登闻检院门", "官职")
    gate_north = tp(
        w,
        gate_e,
        "北宋（未载具体年月）",
        "监守登闻检院门，设一人",
        i,
        north_staff,
        "职事官",
        "建监登闻检院门北宋编制节点。",
        "编制",
        chain="none",
    )
    chain_all(
        w,
        gate_e,
        [gate_north, ft(w, gate_e, "南宋")],
        "连接监登闻检院门北宋、南宋节点。",
    )
    for target, quota, staff_type, label in (
        (
            ft(w, fe(w, "判登闻检院事", "官职"), "北宋景德四年五月"),
            1,
            "官",
            "判登闻检院事一人",
        ),
        (
            ft(w, fe(w, "令史", "官职"), "北宋（登闻检院，未载具体年月）"),
            2,
            "吏",
            "令史二人",
        ),
        (writer_t, 1, "吏", "书写人一人"),
        (gate_north, 1, "内侍官", "监登闻检院门一人"),
    ):
        rel(
            w,
            north,
            target,
            "编制隶属",
            i,
            north_staff,
            f"北宋登闻检院编制：{label}。",
            "编制",
            staff_quota=quota,
            staff_type=staff_type,
        )

    for target, quota, staff_type, label in (
        (
            ft(w, fe(w, "监登闻检院", "官职"), "南宋初"),
            2,
            "官",
            "监登闻检院二人，常除一人",
        ),
        (
            ft(w, fe(w, "主管检匣", "官职"), "南宋"),
            1,
            "内侍",
            "主管检匣一人",
        ),
        (
            ft(w, fe(w, "手分", "官职"), "南宋初（登闻检院）"),
            3,
            "吏",
            "手分三人",
        ),
    ):
        rel(
            w,
            south,
            target,
            "编制隶属",
            i,
            south_staff,
            f"南宋登闻检院编制：{label}。",
            "编制",
            staff_quota=quota,
            staff_type=staff_type,
        )
    w.commit()


def entry736_note():
    i = 736
    quotation = Q(i, "南宋时合四检为一检匣")
    w = W(i)
    cite(
        w,
        "Timepoints",
        ft(w, fe(w, "登闻检院", "机构"), "南宋"),
        i,
        quotation,
        "四检条补证南宋四检合为一检匣的运行变化；物件本身不建实体。",
    )
    w.commit()


def main():
    # 733“邸吏”为纯别称；735“检”、736“四检”、741“检匣”、747“匦”
    # 均为物件，不建机构或官职实体。736 的制度变化作为引文挂入登闻检院南宋节点。
    entry732()
    entry731()
    entry734_core()
    entry737()
    entry738()
    entry739()
    entry740()
    entry746()
    entry742()
    entry743()
    entry745()
    entry744()
    entry748()
    entry749()
    entry750()
    entry734_relations()
    entry736_note()


if __name__ == "__main__":
    main()
